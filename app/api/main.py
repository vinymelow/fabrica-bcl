from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.api.models import ProvisionRequest
from app.services import project_builder, github_service, render_service, notification_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Blue Connect Lead Factory",
    description="API para provisionar novas instâncias do BCL Activate",
    version="0.2.0" # Version bump for new features
)

# Configuração do CORS
origins = [
    "http://localhost:5173",
    "http://localhost:8080",
    "https://blueconnectlead.com",
    "https://www.blueconnectlead.com",
    "https://blueconnectlead.vercel.app" 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def provision_instance_flow(req: ProvisionRequest):
    """
    Orquestra a criação completa de uma nova instância do BCL Activate,
    com gestão de erros robusta.
    """
    supabase_client = None # Inicializa fora do try para estar acessível no except
    campaign_id = req.campaign_id # Guarda o ID para o bloco except

    try:
        user_email = req.user_email
        details = req.campaign_details
        
        # Cria o cliente Supabase para reportar o status
        supabase_client = render_service._get_supabase_client()
        
        logger.info(f"Iniciando provisionamento para Campanha ID: {campaign_id}...")

        # 1. Criar uma cópia personalizada do projeto
        repo_path, repo_name = project_builder.create_project_from_template(campaign_id, details)
        logger.info(f"Projeto criado em: {repo_path}")

        # 2. Criar repositório no GitHub e fazer push
        repo_url = github_service.create_and_push_to_github(repo_path, repo_name)
        logger.info(f"Repositório criado no GitHub: {repo_url}")

        # 3. Fazer deploy no Render
        service_url = render_service.deploy_to_render(repo_name, repo_url, campaign_id)
        logger.info(f"Deploy iniciado no Render. URL do serviço será: {service_url}")

        # 4. Notificar o usuário (a atualização do status já foi feita pelo render_service)
        notification_service.send_provisioning_complete_email(user_email, service_url)
        logger.info(f"Processo de provisionamento para {campaign_id} concluído com sucesso.")

    except Exception as e:
        error_message = str(e)
        logger.error(f"Falha no fluxo de provisionamento para Campanha ID: {campaign_id}. Erro: {error_message}", exc_info=True)
        # Tenta atualizar o status da campanha para 'failed'
        if supabase_client and campaign_id:
            try:
                # Trunca a mensagem de erro para caber no campo do URL, se necessário
                error_for_db = f"Erro: {error_message[:250]}"
                supabase_client.table('campaigns').update({
                    'status': 'failed',
                    'service_url': error_for_db
                }).eq('id', campaign_id).execute()
                logger.info(f"Status da campanha {campaign_id} atualizado para 'failed'.")
            except Exception as db_error:
                logger.error(f"Não foi possível atualizar o status da campanha {campaign_id} para 'failed'. Erro no DB: {db_error}")

@app.post("/provision/new-instance")
async def provision_new_instance(req: ProvisionRequest, background_tasks: BackgroundTasks):
    """
    Endpoint para solicitar a criação de uma nova instância.
    Recebe os detalhes da campanha e inicia o processo em segundo plano.
    """
    if not req.campaign_id or not req.user_email or not req.campaign_details:
        raise HTTPException(status_code=400, detail="Dados da campanha, ID e e-mail do usuário são obrigatórios.")

    logger.info(f"Requisição de provisionamento recebida para o usuário: {req.user_email}")
    background_tasks.add_task(provision_instance_flow, req)

    return {"message": f"Ativação iniciada! O motor da campanha '{req.campaign_details.campaignName}' está sendo construído. Você receberá um e-mail quando estiver pronto."}


@app.get("/")
def read_root():
    return {"status": "A fábrica da Blue Connect Lead está funcionando!"}