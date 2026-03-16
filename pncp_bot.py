import requests
import datetime
import gspread
import json
import os
from google.oauth2.service_account import Credentials

print("Iniciando busca de licitações no PNCP (Versão com Google Sheets)...")

# Configuração do Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
credentials_json = os.environ.get("GOOGLE_CREDENTIALS")
credentials_dict = json.loads(credentials_json)
creds = Credentials.from_service_account_info(credentials_dict, scopes=SCOPES)
gc = gspread.authorize(creds)

SPREADSHEET_ID = "1I5hzuAKQCFLgyqSswIc4gTHqbiAmJ39C2dgHRTN2Ncs"
aba = gc.open_by_key(SPREADSHEET_ID).worksheet("EDITAIS CAPTURADOS")

ids_existentes = aba.col_values(1)

estados_permitidos = ["PB", "PE", "RN", "AL", "CE", "SE"]

termos_busca = [
    "hospital", "manutenção", "preventiva", "corretiva",
    "engenharia clinica", "lavanderia", "CME", "esterilização",
    "gas", "oxigenio", "medicinal", "usina", "rede de gas"
]

modalidades = [2, 6, 8, 10, 14]

hoje = datetime.date.today()
sete_dias = hoje - datetime.timedelta(days=7)
data_inicial = sete_dias.strftime("%Y%m%d")
data_final = hoje.strftime("%Y%m%d")

url = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"

total_encontrados = 0
vistos = set()

# Combinações que garantem relevância para o negócio
# Grupo 1: manutenção + saúde
termos_manutencao = [
    "manutenção", "preventiva", "corretiva", "calibração",
    "engenharia clínica", "esterilização", "lavanderia", "cme"
]
termos_saude = [
    "hospital", "hospitalar", "médico", "clínica", "saúde",
    "odontológico", "clínico", "uti", "samu", "hemodiálise",
    "cirúrgico", "laboratorial", "fisioterapêutico"
]

# Grupo 2: gases medicinais (já são específicos do negócio)
termos_gases = [
    "oxigênio medicinal", "oxigenio medicinal", "gases medicinais",
    "gás medicinal", "gas medicinal", "usina de oxigênio",
    "usina de oxigenio", "rede de gases", "rede de gás medicinal",
    "cilindro de oxigênio", "oxigênio líquido", "ar comprimido medicinal",
    "gases hospitalares", "recarga de oxigênio", "recarga de oxigenio"
]

# Termos que EXCLUEM o edital
termos_bloqueados = [
    "veículo", "carro", "automotivo", "frota",
    "predial", "limpeza urbana", "construção",
    "obra", "pavimentação", "rodovia", "gás de cozinha",
    "gás engarrafado", "botijão"
]

for mod in modalidades:
    for termo in termos_busca:
        for pagina in range(1, 11):
            params = {
                "dataInicial": data_inicial,
                "dataFinal": data_final,
                "codigoModalidadeContratacao": mod,
                "termo": termo,
                "pagina": pagina,
                "tamanhoPagina": 50
            }

            try:
                response = requests.get(url, params=params, timeout=15)
                if response.status_code != 200:
                    continue

                dados = response.json()
                items = dados.get("data", [])
                if not items:
                    break

                for item in items:
                    cnpj = item.get("orgaoEntidade", {}).get("cnpj")
                    ano = item.get("anoCompra")
                    seq = item.get("sequencialCompra")
                    compra_id = f"{cnpj}-{ano}-{seq}"

                    if compra_id in vistos or compra_id in ids_existentes:
                        continue

                    objeto = str(item.get("objetoCompra", "")).lower()
                    estado = item.get("unidadeOrgao", {}).get("ufSigla")

                    # Filtro de Estado
                    if estado not in estados_permitidos:
                        continue

                    # Filtro de Exclusão
                    if any(b in objeto for b in termos_bloqueados):
                        continue

                    # Lógica de aprovação
                    # Caso 1: gases medicinais (específico do negócio)
                    is_gases = any(g in objeto for g in termos_gases)

                    # Caso 2: manutenção + saúde
                    tem_manutencao = any(m in objeto for m in termos_manutencao)
                    tem_saude = any(s in objeto for s in termos_saude)
                    is_manutencao_hospitalar = tem_manutencao and tem_saude

                    if is_gases or is_manutencao_hospitalar:
                        vistos.add(compra_id)
                        total_encontrados += 1

                        municipio = item.get("unidadeOrgao", {}).get("municipioNome", "")
                        orgao = item.get("orgaoEntidade", {}).get("razaoSocial", "")
                        valor = item.get("valorTotalEstimado", 0)
                        link = f"https://pncp.gov.br/app/editais/{cnpj}/{ano}/{seq}"
                        data_pub = hoje.strftime("%d/%m/%Y")
                        proximo_id = len(ids_existentes) + total_encontrados

                        linha = [
                            proximo_id,
                            data_pub,
                            "",
                            orgao,
                            objeto.capitalize(),
                            municipio,
                            f"{municipio}/{estado}",
                            f"R$ {valor:,.2f}",
                            "", "", "", "", "",
                            link
                        ]

                        aba.append_row(linha)
                        ids_existentes.append(compra_id)
                        print(f"✅ Adicionado [{estado}]: {objeto[:70]}")

            except Exception as e:
                print(f"Erro: {e}")
                break

print(f"\nTotal de editais adicionados: {total_encontrados}")
