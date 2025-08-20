import os
import requests
from dotenv import load_dotenv
from ..api.models import CampaignConfiguration

load_dotenv()

RENDER_API_KEY = os.getenv("RENDER_API_KEY")
RENDER_OWNER_ID = os.getenv("RENDER_OWNER_ID")

# Carregar as nossas credenciais padrão da Evolution API
EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")

def deploy_new_service(repo_url: str, client_name: str, config: CampaignConfiguration) -> str:
    """
    Cria um novo Web Service no Render a partir de um repositório do GitHub.
    """
    url = "https://api.render.com/v1/services"
    service_name = f"bcl-instance-{client_name.lower().replace(' ', '-')}"

    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # --- INÍCIO DA NOVA LÓGICA ---
    # Gerar o nome da instância padronizado
    # Ex: "CaveLusa" -> "cavelusa_instance"
    instance_name = f"{client_name.lower().replace(' ', '-')}_instance"
    print(f"Nome da instância gerado para a Evolution API: {instance_name}")
    # --- FIM DA NOVA LÓGICA ---

    payload = {
        "type": "web_srv",
        "name": service_name,
        "ownerId": RENDER_OWNER_ID,
        "repo": repo_url,
        "autoDeploy": "yes",
        "branch": "main",
        "serviceDetails": {
            "runtime": "docker",
            "envVars": [
                # Variável de ambiente específica do cliente
                {"key": "GOOGLE_API_KEY", "value": config.google_api_key},
                
                # Nossas variáveis de ambiente padrão para a Evolution API
                {"key": "EVOLUTION_API_URL", "value": EVOLUTION_API_URL},
                {"key": "EVOLUTION_API_KEY", "value": EVOLUTION_API_KEY},
                
                # A instância gerada dinamicamente para este cliente
                {"key": "EVOLUTION_INSTANCE", "value": instance_name},
            ],
        }
    }

    try:
        print(f"A enviar pedido de deploy para o Render para o serviço '{service_name}'...")
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        service_data = response.json()
        # Corrigido para extrair o URL corretamente
        service_url = service_data.get("deploy", {}).get("service", {}).get("url")
        print(f"Serviço criado com sucesso! URL: {service_url}")
        return service_url
    except requests.exceptions.RequestException as e:
        error_details = e.response.text if e.response else str(e)
        raise Exception(f"Falha ao criar o serviço no Render: {error_details}")