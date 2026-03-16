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

# Buscar IDs existentes
ids_existentes = aba.col_values(1)

# Calcular próximo ID baseado no maior número existente
ids_numericos = []
for i in ids_existentes[1:]:
    try:
        ids_numericos.append(int(i))
    except:
        pass
proximo_id = max(ids_numericos) + 1 if ids_numericos else 1

print(f"Próximo ID: {proximo_id}")

estados_permitidos = ["PB", "PE", "RN", "AL", "CE", "SE"]

termos_busca = [
    "hospital", "manutenção", "preventiva", "corretiva",
    "engenharia clinica", "lavanderia", "CME", "esterilização",
    "oxigenio", "medicinal", "usina", "rede de gas"
]

modalidades = [2, 6, 8, 10, 14]

hoje = datetime.date.today()
sete_dias = hoje - datetime.timedelta(days=7)
data_inicial = sete_dias.strftime("%Y%m%d")
data_final = hoje.strftime("%Y%m%d")

url = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"

total_encontrados = 0
vistos = set()

# Termos de manutenção (qualquer um destes)
termos_manutencao = [
    "manutenção", "preventiva", "corretiva",
    "engenharia clínica", "esterilização", "lavanderia",
    "cme", "calibração"
]

# Termos de saúde (qualquer um destes)
termos_saude = [
    "hospital", "hospitalar", "médico", "clínica", "saúde",
    "odontológico", "clínico", "uti", "samu", "hemodiálise",
    "cirúrgico", "laboratorial", "fisioterapêutico",
    "equipamento médico", "equipamento hospitalar"
]

# Gases medicinais
termos_gases = [
    "oxigênio medicinal", "oxigenio medicinal", "gases medicinais",
    "gás medicinal", "gas medicinal", "usina de oxigênio",
    "usina de oxigenio", "rede de gases", "rede de gás medicinal",
    "cilindro de oxigênio", "oxigênio líquido", "ar comprimido medicinal",
    "gases hospitalares", "recarga de oxigênio", "recarga de oxigenio"
]

# Termos bloqueados
termos_bloqueados = [
    "veículo", "carro", "automotivo", "frota", "predial",
    "limpeza urbana", "construção", "obra", "pavimentação",
    "rodovia", "gás de cozinha", "gás engarrafado", "botijão",
    "empilhadeira", "retroescavadeira", "trator", "ônibus",
    "caminhão", "motocicleta", "ambulância", "escolar",
    "alimentação", "merenda"
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
                    numero = item.get("numeroCompra", "")
                    compra_id = f"{cnpj}-{ano}-{seq}"

                    if compra_id in vistos or compra_id in ids_existentes:
                        continue

                    objeto = str(item.get("objetoCompra", "")).lower()
                    estado = item.get("unidadeOrgao", {}).get("ufSigla", "")
                    municipio = item.get("unidadeOrgao", {}).get("municipioNome", "")
                    orgao = item.get("orgaoEntidade", {}).get("razaoSocial", "")
                    modalidade_nome = item.get("modalidadeNome", "")
                    valor = item.get("valorTotalEstimado", 0)
                    data_abertura = item.get("dataAberturaProposta", "")

                    # Filtro de Estado
                    if estado not in estados_permitidos:
                        continue

                    # Filtro de Exclusão
                    if any(b in objeto for b in termos_bloqueados):
                        continue

                    # Lógica de aprovação
                    is_gases = any(g in objeto for g in termos_gases)
                    tem_manutencao = any(m in objeto for m in termos_manutencao)
                    tem_saude = any(s in objeto for s in termos_saude)
                    is_manutencao_hospitalar = tem_manutencao and tem_saude

                    if is_gases or is_manutencao_hospitalar:
                        vistos.add(compra_id)

                        # Formatar data de abertura
                        try:
                            dt = datetime.datetime.fromisoformat(data_abertura)
                            data_abertura_fmt = dt.strftime("%d/%m/%Y às %Hh")
                        except:
                            data_abertura_fmt = ""

                        # Montar número da licitação
                        if "Pregão" in modalidade_nome:
                            modalidade_sigla = "PE"
                        elif "Dispensa" in modalidade_nome:
                            modalidade_sigla = "DL"
                        elif "Inexigibilidade" in modalidade_nome:
                            modalidade_sigla = "IE"
                        elif "Concorrência" in modalidade_nome:
                            modalidade_sigla = "CC"
                        else:
                            modalidade_sigla = "LT"

                        numero_licitacao = f"{modalidade_sigla} - {numero}/{ano} - {orgao[:30]} - {municipio} {estado} - {data_abertura_fmt}"

                        link = f"https://pncp.gov.br/app/editais/{cnpj}/{ano}/{seq}"
                        data_pub = hoje.strftime("%d/%m/%Y")

                        linha = [
                            proximo_id,
                            data_pub,
                            "",
                            numero_licitacao,
                            objeto.capitalize(),
                            municipio,
                            f"{municipio}/{estado}",
                            f"R$ {valor:,.2f}",
                            "", "", "", "", "",
                            link
                        ]

                        aba.append_row(linha)
                        ids_existentes.append(compra_id)
                        total_encontrados += 1
                        proximo_id += 1

                        print(f"✅ [{estado}] {objeto[:60]}")

            except Exception as e:
                print(f"Erro: {e}")
                break

print(f"\nTotal de editais adicionados: {total_encontrados}")
