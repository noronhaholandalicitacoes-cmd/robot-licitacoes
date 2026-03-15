import requests
import datetime

print("Iniciando busca de licitações no PNCP...")

# Estados permitidos
estados_permitidos = ["PB", "PE", "RN", "AL", "CE", "SE"]

# Palavras-chave
palavras_chave = [
    "oxigênio",
    "gases medicinais",
    "ar medicinal",
    "vácuo",
    "usina de oxigênio",
    "locação",
    "equipamentos hospitalares",
    "engenharia clínica",
    "esterilização",
    "cme",
    "lavanderia hospitalar",
    "manutenção corretiva",
    "manutenção preventiva",
    "central de gases",
    "compressor hospitalar"
]

# datas
hoje = datetime.date.today()
sete_dias = hoje - datetime.timedelta(days=7)

data_inicial = sete_dias.strftime("%Y%m%d")
data_final = hoje.strftime("%Y%m%d")

url = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"

pagina = 1
total_encontrados = 0

while pagina <= 5:

    params = {
        "dataPublicacaoInicial": data_inicial,
        "dataPublicacaoFinal": data_final,
        "pagina": pagina,
        "tamanhoPagina": 100
    }

    response = requests.get(url, params=params)
    dados = response.json()

    for item in dados.get("data", []):

        objeto = str(item.get("objetoCompra", "")).lower()
        estado = item.get("unidadeOrgao", {}).get("ufSigla")
        municipio = item.get("unidadeOrgao", {}).get("municipioNome")
        orgao = item.get("orgaoEntidade", {}).get("razaoSocial")
        valor = item.get("valorTotalEstimado")

        if estado not in estados_permitidos:
            continue

        encontrou = False

        for palavra in palavras_chave:
            if palavra in objeto:
                encontrou = True
                break

        if not encontrou:
            continue

        total_encontrados += 1

        print("Objeto:", objeto)
        print("Órgão:", orgao)
        print("Estado:", estado)
        print("Município:", municipio)
        print("Valor estimado:", valor)
        print("-"*50)

    pagina += 1

print("\nTotal de editais encontrados:", total_encontrados)
