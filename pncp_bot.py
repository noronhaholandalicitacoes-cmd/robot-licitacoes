import requests
import datetime

print("Iniciando busca de licitações no PNCP (Versão Otimizada)...")

# Estados permitidos
estados_permitidos = ["PB", "PE", "RN", "AL", "CE", "SE"]

# Termos de busca para a API (para aumentar a cobertura)
termos_busca = ["manutenção", "hospitalar", "equipamento", "preventiva", "corretiva"]

# Modalidades obrigatórias para a API
# 2: Concorrência, 6: Pregão, 8: Dispensa, 10: Inexigibilidade, 14: Credenciamento
modalidades = [2, 6, 8, 10, 14]

hoje = datetime.date.today()
sete_dias = hoje - datetime.timedelta(days=7)

# Formato esperado pela API: YYYYMMDD
data_inicial = sete_dias.strftime("%Y%m%d")
data_final = hoje.strftime("%Y%m%d")

url = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"

total_encontrados = 0
vistos = set( ) # Para evitar duplicados entre termos/modalidades

for mod in modalidades:
    for termo in termos_busca:
        # Busca as primeiras 5 páginas para cada combinação (total de 50 itens por termo/mod)
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
                if response.status_code == 204: # No Content
                    break
                if response.status_code != 200:
                    continue
                    
                dados = response.json()
                items = dados.get("data", [])
                if not items:
                    break
                    
                for item in items:
                    # Criar um ID único para evitar duplicados
                    compra_id = f"{item.get('orgaoEntidade', {}).get('cnpj')}-{item.get('anoCompra')}-{item.get('sequencialCompra')}"
                    if compra_id in vistos:
                        continue
                    
                    objeto = str(item.get("objetoCompra", "")).lower()
                    estado = item.get("unidadeOrgao", {}).get("ufSigla")
                    
                    # Filtro de Estado
                    if estado not in estados_permitidos:
                        continue
                    
                    # Filtro Refinado: Deve conter "manutenção" E algum termo hospitalar/equipamento/preventiva/corretiva
                    # OU conter termos muito específicos como "engenharia clínica" ou "oxigênio medicinal"
                    is_manutencao = "manutenção" in objeto
                    is_hospitalar = any(p in objeto for p in ["hospitalar", "equipamento", "clínica", "médico", "hospital", "preventiva", "corretiva"])
                    is_especifico = any(p in objeto for p in ["engenharia clínica", "oxigênio medicinal", "gases medicinais"])
                    
                    if (is_manutencao and is_hospitalar) or is_especifico:
                        vistos.add(compra_id)
                        total_encontrados += 1
                        
                        print(f"--- ENCONTRADO ---")
                        print(f"Objeto: {objeto}")
                        print(f"Órgão: {item.get('orgaoEntidade', {}).get('razaoSocial')}")
                        print(f"Estado: {estado}")
                        print(f"Município: {item.get('unidadeOrgao', {}).get('municipioNome')}")
                        print(f"Valor estimado: R$ {item.get('valorTotalEstimado', 0):,.2f}")
                        print(f"Link: https://pncp.gov.br/app/editais/{item.get('orgaoEntidade', {} ).get('cnpj')}/{item.get('anoCompra')}/{item.get('sequencialCompra')}")
                        print("-" * 50)
                
            except Exception as e:
                # Silencia erros de conexão para não travar o robô
                break

print(f"\nTotal de editais encontrados: {total_encontrados}")
