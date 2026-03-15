import requests

url = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"

response = requests.get(url)

print(response.json())
