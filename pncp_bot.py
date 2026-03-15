import requests
import datetime

print("Iniciando busca de licitações no PNCP...")

# Estados que o robô deve buscar
estados_permitidos = ["PB", "PE", "RN", "AL", "CE", "SE"]

# Palavras-chave das atividades
palavras_chave = [
    "oxigênio",
    "gases medicinais",
    "ar medicinal",
    "vácuo clínico",
    "usina de oxigênio",
    "locação de equipamentos médico hospitalar",
    "engenharia clínica",
    "esterilização",
    "cme",
    "lavanderia hospitalar",
    "manutenção hospitalar",
    "manutenção corretiva",
    "manutenção preventiva",
    "manutenção equipamentos hospitalares",
    "equipamentos hospitalares",
    "central de gases",
    "compressor hospitalar"
]

# Data de hoje
hoje = datetime.date.today().strftime("%Y%m%d")

url = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"

params = {
    "dataPublicacaoInicial": hoje,
    "dataPublicacaoFinal": hoje,
    "pagina": 1,
    "tamanhoPagina": 100
}

response = requests.get(url, params=params)

dados = response.json()

print("Buscando editais publicados hoje...\n")

for item in dados.get("data", []):

    objeto = str(item.get("objetoCompra", "")).lower()
    estado = item.get("unidadeOrgao", {}).get("ufSigla")
    municipio = item.get("unidadeOrgao", {}).get("municipioNome")
    orgao = item.get("orgaoEntidade", {}).get("razaoSocial")
    valor = item.get("valorTotalEstimado")

    # filtro de estado
    if estado not in estados_permitidos:
        continue

    # filtro de palavras-chave
    encontrou = False

    for palavra in palavras_chave:
        if palavra in objeto:
            encontrou = True
            break

    if not encontrou:
        continue

    print("Objeto:", objeto)
    print("Órgão:", orgao)
    print("Estado:", estado)
    print("Município:", municipio)
    print("Valor estimado:", valor)
    print("-" * 50)
