import os
import logging
from typing import Optional, Any
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, ValidationError
from dotenv import load_dotenv
import google.generativeai as genai
from openai import OpenAI

# Carrega as variáveis de ambiente
load_dotenv()

# Configuração do Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração dos Clientes de IA
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

app = FastAPI(
    title="BCL Activate API",
    description="API para ativar leads e receber webhooks.",
    version="1.0.0"
)

# --- MODELOS DE DADOS ---
class Lead(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None
    interest: Optional[str] = None

# --- SEGURANÇA ---
BCL_API_KEY = os.getenv("BCL_API_KEY")
API_KEY_NAME = "X-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key: str = Security(api_key_header)):
    if not BCL_API_KEY:
        logger.warning("Nenhuma BCL_API_KEY configurada. O acesso está desprotegido.")
        return # Permite acesso se nenhuma chave estiver configurada
    if api_key and api_key == BCL_API_KEY:
        return api_key
    else:
        raise HTTPException(status_code=403, detail="Chave de API inválida ou em falta")

# --- LÓGICA CENTRAL ---
def criar_prompt_para_lead(lead: Lead) -> str:
    # ### SYSTEM PROMPT START ###
    # (Este conteúdo será substituído pela fábrica)
    system_prompt = """
    Você é um assistente de vendas especialista. Crie uma mensagem curta e humana para o WhatsApp.
    """
    # ### SYSTEM PROMPT END ###
    
    user_prompt = f"Crie a mensagem para o seguinte lead:\nNome: {lead.name}\nEmail: {lead.email}\nTelefone: {lead.phone}\nEmpresa: {lead.company}\nCargo: {lead.position}\nInteresse: {lead.interest}"
    return f"{system_prompt}\n\n{user_prompt}"

def gerar_mensagem(prompt: str) -> str:
    try:
        if GOOGLE_API_KEY:
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(prompt)
            return response.text
        elif openai_client:
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        else:
            return "Olá! Vi que se interessou pelo nosso produto. Gostaria de conversar?"
    except Exception as e:
        logger.error(f"Erro ao gerar mensagem com IA: {e}")
        return "Olá! Percebi o seu interesse em nossa proposta e gostaria de entender melhor como posso ajudar."

# --- ENDPOINTS DA API ---
@app.post("/activate", dependencies=[Depends(get_api_key)])
def activate_lead(lead_data: Lead):
    logger.info(f"Recebido lead para ativação: {lead_data.name}")
    prompt = criar_prompt_para_lead(lead_data)
    mensagem = gerar_mensagem(prompt)
    logger.info(f"Mensagem gerada: {mensagem}")
    # Aqui viria a lógica para enviar a mensagem via WhatsApp
    return {"status": "sucesso", "lead_name": lead_data.name, "generated_message": mensagem}

# --- ENDPOINT DE WEBHOOK UNIVERSAL ---
FIELD_MAP = {
    "full_name": "name", "first_name": "name", "user_name": "name",
    "email_address": "email", "e-mail": "email",
    "phone_number": "phone", "telefone": "phone",
}

def normalize_lead_data(raw_data: dict) -> dict:
    """Traduz os campos de entrada para o nosso modelo Lead."""
    normalized = {}
    for key, value in raw_data.items():
        clean_key = key.lower().replace(" ", "_")
        target_key = FIELD_MAP.get(clean_key, clean_key)
        if target_key in Lead.model_fields:
            normalized[target_key] = value
    return normalized

@app.post("/webhook/{webhook_id}")
async def receive_webhook(webhook_id: str, raw_lead: dict):
    """Endpoint universal para receber webhooks de várias fontes."""
    logger.info(f"Webhook recebido para {webhook_id} com dados: {raw_lead}")
    try:
        lead_data_dict = normalize_lead_data(raw_lead)
        lead_instance = Lead(**lead_data_dict)
        return activate_lead(lead_instance)
    except ValidationError as e:
        logger.error(f"Erro de validação no webhook: {e.errors()}")
        missing_fields = [err['loc'][0] for err in e.errors() if err['type'] == 'missing']
        raise HTTPException(status_code=422, detail={"error": "Dados do lead incompletos.", "missing_fields": missing_fields})
    except Exception as e:
        logger.error(f"Erro inesperado no processamento do webhook: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao processar o lead.")

@app.get("/")
def read_root():
    return {"status": "BCL Activate Instance está online."}