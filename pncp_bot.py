import requests
import datetime

print("Testando API do PNCP...")

hoje = datetime.date.today()
sete_dias = hoje - datetime.timedelta(days=7)
data_inicial = sete_dias.strftime("%Y%m%d")
data_final = hoje.strftime("%Y%m%d")

url = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"

params = {
    "dataInicial": data_inicial,
    "dataFinal": data_final,
    "codigoModalidadeContratacao": 6,
    "termo": "hospital",
    "pagina": 1,
    "tamanhoPagina": 10
}

response = requests.get(url, params=params, timeout=15)
print(f"Status: {response.status_code}")
print(f"Resposta: {response.text[:3000]}")
