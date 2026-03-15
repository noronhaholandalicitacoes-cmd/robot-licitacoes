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
aba = gc.open_by_key(SPREADSHEET_ID).worksheet("editais capturados")

# Buscar IDs já existentes para evitar duplicados
ids_existentes = aba.col_values(1)

# Estados permitidos
estados_permitidos = ["PB", "PE", "RN", "AL", "CE", "SE"]

# Termos de busca
termos_busca = ["manutenção", "hospitalar", "equipamento", "médico", "clínica"]

# Modalidades
modalidades = [2, 6, 8, 10, 14]

hoje = datetime.date.today()
sete_dias = hoje - datetime.timedelta(days=7)
data_inicial = sete_dias.strftime("%Y%m%d")
data_final = hoje.strftime("%Y%m%d")

url = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"

total_encontrados = 0
vistos = set()

termos_saude = ["hospitalar", "médico", "clínica", "saúde", "odontológico", "oxigênio", "gases", "hospital", "clínico"]
termos_bloqueados = ["veículo", "carro", "automotivo", "frota", "ar condicionado", "predial", "limpeza", "vigilância"]

for mod in modalidades:
    for termo in termos_busca:
        for pagina in range(1, 6):
            params = {
                "dataInicial": data_inicial,
                "dataFinal": data_final,
                "codigoModalidadeContratacao": mod,
                "termo": termo,
                "pagina": pagina,
                "tamanhoPagina": 10
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
                    co
