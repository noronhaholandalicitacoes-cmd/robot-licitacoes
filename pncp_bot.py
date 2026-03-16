import requests
import datetime

print("Testando API do PNCP com filtro de estado...")

hoje = datetime.date.today()
sete_dias = hoje - datetime.timedelta(days=7)
data_inicial = sete_dias.strftime("%Y%m%d")
data_final = hoje.strftime("%Y%m%d")

url = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"

estados_permitidos = ["PB", "PE", "RN", "AL", "CE", "SE"]
termos_saude = [
    "hospital", "hospitalar", "médico", "clínica", "saúde",
    "odontológico", "oxigênio", "oxigenio", "gases", "gás", "gas",
    "clínico", "cme", "esterilização", "lavanderia",
    "engenharia clínica", "preventiva", "corretiva",
    "equipamento", "medicinal", "usina", "rede de gás"
]

encontrados = 0

for mod in [2, 6, 8, 10, 14]:
    for pagina in range(1, 20):
        params = {
            "dataInicial": data_inicial,
            "dataFinal": data_final,
            "codigoModalidadeContratacao": mod,
            "termo": "hospital",
            "pagina": pagina,
            "tamanhoPagina": 50
        }

        response = requests.get(url, params=params, timeout=15)
        if response.status_code != 200:
            break

        dados = response.json()
        items = dados.get("data", [])
        if not items:
            break

        for item in items:
            estado = item.get("unidadeOrgao", {}).get("ufSigla")
            objeto = str(item.get("objetoCompra", "")).lower()

            if estado in estados_permitidos:
                tem_saude = any(s in objeto for s in termos_saude)
                print(f"[{estado}] {objeto[:80]} | saude={tem_saude}")
                encontrados += 1

print(f"\nTotal nos seus estados: {encontrados}")
