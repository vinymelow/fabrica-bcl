# vinymelow/fabrica-bcl/app/services/render_service.py

import os
import requests
import logging
import time
from supabase import create_client, Client

logger = logging.getLogger(__name__)

RENDER_API_KEY = os.getenv("RENDER_API_KEY")
OWNER_ID = os.getenv("RENDER_OWNER_ID") 
# Adicione as suas credenciais do Supabase como variáveis de ambiente no Render
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

HEADERS = {
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

def _get_supabase_client() -> Client:
    """Cria e retorna um cliente Supabase."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("As variáveis de ambiente SUPABASE_URL e SUPABASE_KEY são obrigatórias.")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def deploy_to_render(repo_name: str, repo_url: str, campaign_id: int) -> str:
    """
    Faz o deploy de um novo Web Service no Render a partir de um repositório GitHub
    e atualiza o URL do serviço na tabela de campanhas do Supabase.
    """
    url = "https://api.render.com/v1/services"
    
    # As variáveis de ambiente para a instância do cliente
    # A BCL_API_KEY é uma chave simples para o cliente usar
    bcl_api_key = f"bcl_secret_{campaign_id}_{os.urandom(16).hex()}"
    
    payload = {
        "ownerId": OWNER_ID,
        "name": repo_name,
        "type": "web_srv",
        "repo": repo_url,
        "autoDeploy": "yes",
        "branch": "main",
        "serviceDetails": {
            "env": "docker",
            "dockerfilePath": "./Dockerfile",
            "envVars": [
                {"key": "BCL_API_KEY", "value": bcl_api_key},
                # Adicione outras chaves de API que o BCL Activate precisa (OpenAI, Google, etc.)
                # Elas devem ser obtidas do seu ambiente seguro
                {"key": "GOOGLE_API_KEY", "value": os.getenv("TEMPLATE_GOOGLE_API_KEY")},
                {"key": "OPENAI_API_KEY", "value": os.getenv("TEMPLATE_OPENAI_API_KEY")},
                {"key": "EVOLUTION_API_URL", "value": os.getenv("TEMPLATE_EVOLUTION_API_URL")},
                {"key": "EVOLUTION_API_KEY", "value": os.getenv("TEMPLATE_EVOLUTION_API_KEY")},
                # O nome da instância precisa ser único para cada cliente
                {"key": "EVOLUTION_INSTANCE_NAME", "value": f"bcl-instance-{campaign_id}"}
            ]
        }
    }

    try:
        response = requests.post(url, headers=HEADERS, json=payload)
        response.raise_for_status()
        
        data = response.json()
        service_id = data["service"]["id"]
        service_url = data["service"]["serviceDetails"]["url"]
        logger.info(f"Serviço criado no Render com ID: {service_id} e URL: {service_url}")

        # Aguarda um pouco para garantir que o serviço esteja estável antes de atualizar o BD
        time.sleep(5) 
        
        # Atualiza a tabela no Supabase
        _update_campaign_in_supabase(campaign_id, service_url, bcl_api_key)
        
        return service_url

    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao fazer deploy no Render: {e}")
        if e.response:
            logger.error(f"Detalhes do erro do Render: {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"Erro inesperado durante o deploy ou atualização no Supabase: {e}")
        raise

def _update_campaign_in_supabase(campaign_id: int, service_url: str, api_key: str):
    """
    Atualiza o registo da campanha no Supabase com o URL do serviço e a chave de API.
    """
    try:
        supabase = _get_supabase_client()
        logger.info(f"A atualizar campanha {campaign_id} no Supabase com URL: {service_url}")
        
        data, count = supabase.table('campaigns').update({
            'service_url': service_url,
            'status': 'active',
            'api_key': api_key
        }).eq('id', campaign_id).execute()

        logger.info(f"Resposta da atualização do Supabase: {data}, {count}")
        if not (data and len(data[1]) > 0):
             logger.warning(f"Atenção: A campanha com ID {campaign_id} não foi encontrada no Supabase para ser atualizada.")

    except Exception as e:
        logger.error(f"Erro ao atualizar campanha no Supabase: {e}", exc_info=True)
        # Mesmo que a atualização falhe, não interrompemos o fluxo principal,
        # mas registamos o erro para análise posterior.