import requests
import datetime

print("Iniciando busca de licitações no PNCP (Versão FOCO HOSPITALAR)...")

# Estados permitidos
estados_permitidos = ["PB", "PE", "RN", "AL", "CE", "SE"]

# Termos de busca para a API (para aumentar a cobertura)
termos_busca = ["manutenção", "hospitalar", "equipamento", "medico", "clinica", "locação", "locacao", "CME", "esterilização", "preventiva", "corretiva"]

# Modalidades obrigatórias para a API
modalidades = [2, 6, 8, 10, 14]

hoje = datetime.date.today()
sete_dias = hoje - datetime.timedelta(days=7)

# Formato esperado pela API: YYYYMMDD
data_inicial = sete_dias.strftime("%Y%m%d")
data_final = hoje.strftime("%Y%m%d")

url = "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"

total_encontrados = 0
vistos = set( )

# Termos que DEFINEM que é hospitalar (deve ter pelo menos um destes)
termos_saude = ["hospitalar", "medico", "clinica", "saude", "odontologico", "oxigenio", "gases", "hospital", "clinico"]

# Termos que indicam que NÃO é o que queremos (Filtro de Exclusão)
termos_bloqueados = ["veículo", "alimentícios", "carro", "automotivo", "frota", "ar condicionado", "predial", "limpeza", "vigilância"]

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
                    compra_id = f"{item.get('orgaoEntidade', {}).get('cnpj')}-{item.get('anoCompra')}-{item.get('sequencialCompra')}"
                    if compra_id in vistos:
                        continue
                    
                    objeto = str(item.get("objetoCompra", "")).lower()
                    estado = item.get("unidadeOrgao", {}).get("ufSigla")
                    
                    # 1. Filtro de Estado
                    if estado not in estados_permitidos:
                        continue
                    
                    # 2. Filtro de Exclusão (Se tiver 'carro', 'veículo', etc, ignora na hora)
                    if any(b in objeto for b in termos_bloqueados):
                        continue
                    
                    # 3. Lógica de Manutenção Hospitalar
                    # Deve ter a palavra 'manutenção' E algum termo de saúde
                    tem_manutencao = "manutenção" in objeto
                    tem_saude = any(s in objeto for s in termos_saude)
                    
                    # Caso especial: Termos que já são hospitalares por si só
                    is_especifico = any(e in objeto for e in ["engenharia clínica", "equipamentos hospitalares", "aparelhos médicos"])
                    
                    if (tem_manutencao and tem_saude) or is_especifico:
                        vistos.add(compra_id)
                        total_encontrados += 1
                        
                        print(f"--- ENCONTRADO ---")
                        print(f"Objeto: {objeto}")
                        print(f"Órgão: {item.get('orgaoEntidade', {}).get('razaoSocial')}")
                        print(f"Estado: {estado}")
                        print(f"Link: https://pncp.gov.br/app/editais/{item.get('orgaoEntidade', {} ).get('cnpj')}/{item.get('anoCompra')}/{item.get('sequencialCompra')}")
                        print("-" * 50)
                
            except Exception:
                break

print(f"\nTotal de editais hospitalares encontrados: {total_encontrados}")
