# Conteúdo Corrigido e Organizado para: app/api/main.py

import os
import google.generativeai as genai
import openai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import random
import requests
import json
import time
from google.api_core import exceptions as google_exceptions

# --- 1. CONFIGURAÇÃO INICIAL ---
load_dotenv()

# Configurar Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
else:
    print("AVISO: GOOGLE_API_KEY não encontrada. O sistema irá usar a OpenAI diretamente.")

# Configurar OpenAI
openai_client = openai.OpenAI()


# --- 2. MODELOS DE DADOS ---
class Lead(BaseModel):
    nome: str
    desafio: str | None = None
    investimento: str
    nicho: str
    telefone: str
    email: str


# --- 3. FUNÇÕES AUXILIARES ---
def criar_prompt_para_lead(lead: Lead):
    """
    Cria um prompt de sistema dinâmico, inspirado nos princípios de Alex Hormozi,
    para converter um novo lead para o agendamento do onboarding do Free Trial.
    """
    primeiro_nome = lead.nome.split()[0].capitalize()
    link_agendamento = "https://calendar.app.google/3Tf6XfQGtHpghRTx8"
    
    dores_por_nicho = {
        "Clínicas": "garantir que nenhum paciente se perde por demora no atendimento",
        "Imobiliário": "perder leads para uma concorrência mais rápida",
        "E-commerce": "lidar com o alto custo para adquirir novos clientes",
        "Indústria/B2B": "a sobrecarga da equipa comercial com a qualificação de leads"
    }
    dor_padrao = dores_por_nicho.get(lead.nicho, "otimizar os seus processos de aquisição de clientes")
    dor_principal = lead.desafio if lead.desafio and lead.desafio.strip() else dor_padrao

    # --- BIBLIOTECA DE TEMPLATES ESTRATÉGICOS (Hormozi Style) ---
    # Foco em Valor, Urgência e Remoção de Risco.
    
    templates = [
        # Template 1: A Oferta "No-Brainer"
        f"Olá {primeiro_nome}! 👋 Aqui é o Vinycius, da Blue.\n\nVi o seu interesse e vou ser direto: queremos provar o nosso valor, não apenas falar sobre ele. Por isso, estamos a oferecer-lhe acesso gratuito de 7 dias ao nosso motor de resposta instantânea.\n\nO único 'custo' para si são 30 minutos numa chamada de onboarding para o ativarmos. Em troca, vai ver na prática como o problema de '{dor_principal}' pode ser resolvido.\n\nSem risco, sem compromisso. Se parece justo, agende o seu onboarding aqui:\n{link_agendamento}",
        
        # Template 2: Foco no Resultado e na Dor
        f"{primeiro_nome}, Vinycius da Blue aqui.\n\nSe está a investir {lead.investimento} em anúncios, cada lead que não é contactado de imediato é dinheiro a ser desperdiçado. A dor de '{dor_principal}' é real e custa caro.\n\nVamos resolver isto juntos. O nosso teste gratuito de 7 dias é um diagnóstico prático para 'selar' essa fuga de receita. O próximo passo é agendar a sessão de ativação de 30 minutos.\n\nEscolha o melhor horário para si e comece a transformar o seu investimento em conversas:\n{link_agendamento}",

        # Template 3: Urgência e Prova Futura
        f"Olá {primeiro_nome}.\n\nExcelente decisão em querer testar o BCL. Abrimos apenas 5 vagas para o nosso programa de testes gratuitos esta semana para garantir um acompanhamento de elite.\n\nA sua vaga está pré-reservada. O passo final para a garantir é agendar a sua sessão de ativação de 30 minutos. É nela que ligamos o motor.\n\nGaranta a sua vaga e veja em 7 dias o que a sua concorrência levará 1 ano a perceber:\n{link_agendamento}"
    ]
    
    template_escolhido = random.choice(templates)

    # --- O NOVO SYSTEM PROMPT INTELIGENTE ---
    prompt_final = f"""
    **# DIRETIVA DE EXECUÇÃO**
    Atue como um especialista em marketing de resposta direta de classe mundial, treinado nos princípios de Alex Hormozi. A sua tarefa é pegar no template de mensagem de WhatsApp abaixo e otimizá-lo para ser uma "Grand Slam Offer" - uma oferta tão boa que a pessoa se sente estúpida a dizer não.

    Siga estas regras rigorosamente:
    1.  **Clareza e Densidade de Valor:** Vá direto ao ponto. Cada palavra deve servir o propósito de levar à ação. Enfatize o que o cliente GANHA (resultados, dados, velocidade) versus o que ele DÁ (30 minutos).
    2.  **Urgência e Escassez:** Se o template mencionar urgência ou vagas limitadas, reforce essa ideia de forma credível.
    3.  **Remoção de Risco:** Assegure que a mensagem transmite "sem custo, sem compromisso, sem risco".
    4.  **Linguagem:** Otimize o texto para Português de Portugal, garantindo que é natural, confiante e profissional.

    Gere APENAS a mensagem de WhatsApp final, nada mais. Mantenha a estrutura, as quebras de linha e o link intactos.

    **--- TEMPLATE BASE PARA OTIMIZAR ---**
    {template_escolhido}
    **--- FIM DO TEMPLATE ---**
    """
    return prompt_final

def enviar_whatsapp(numero: str, mensagem: str):
    """Envia uma mensagem de texto para um número de WhatsApp usando a Evolution API, com pausas dinâmicas e humanizadas."""
    
    # --- PARÂMETROS DE HUMANIZAÇÃO (pode afiná-los aqui) ---
    CARACTERES_POR_SEGUNDO = 15  # Velocidade de digitação média (mais baixo = mais lento)
    MIN_DELAY_SEGUNDOS = 1.8     # A pausa mínima, mesmo para mensagens curtas
    MAX_DELAY_SEGUNDOS = 5.0     # A pausa máxima, para evitar esperas longas
    # ---------------------------------------------------------
    
    api_url = os.getenv("EVOLUTION_API_URL")
    api_key = os.getenv("EVOLUTION_API_KEY")
    instance_name = os.getenv("EVOLUTION_INSTANCE", "bcl_instance")
    
    if not all([api_url, api_key]):
        print("ERRO: Credenciais da Evolution API não configuradas no .env")
        return False

    full_url = f"{api_url}/message/sendText/{instance_name}"
    headers = {"apikey": api_key, "Content-Type": "application/json"}
    numero_formatado = f"{numero}@s.whatsapp.net"
    paragrafos = [p for p in mensagem.split('\n') if p.strip()]

    for i, paragrafo in enumerate(paragrafos):
        payload = {"number": numero_formatado, "options": {"delay": 1200, "presence": "composing"}, "text": paragrafo}
        
        # Apenas calcula a pausa dinâmica *após* a primeira mensagem
        if i > 0:
            # 1. Calcula o tempo base de digitação
            delay_base = len(paragrafo) / CARACTERES_POR_SEGUNDO
            
            # 2. Adiciona um desvio aleatório para simular o fator humano
            delay_com_jitter = delay_base + random.uniform(-0.5, 1.0)
            
            # 3. Garante que a pausa está dentro dos nossos limites mínimo e máximo
            delay_final = max(MIN_DELAY_SEGUNDOS, min(delay_com_jitter, MAX_DELAY_SEGUNDOS))
            
            print(f"Pausa humanizada de {delay_final:.2f} segundos antes do próximo parágrafo.")
            time.sleep(delay_final)

        try:
            print(f"A enviar parágrafo: '{paragrafo}' para {numero_formatado}")
            response = requests.post(full_url, headers=headers, json=payload)
            response.raise_for_status()
            
        except requests.exceptions.RequestException as e:
            print(f"ERRO ao enviar parágrafo via Evolution API: {e}")
            if e.response is not None:
                print(f"Detalhe do erro da API: {e.response.text}")
            return False
            
    print("Todos os parágrafos foram enviados com sucesso.")
    return True


# --- 4. APLICAÇÃO FastAPI E ENDPOINTS ---
app = FastAPI(title="BCL Activate API")

# Adicione este import no topo do seu ficheiro
from fastapi.middleware.cors import CORSMiddleware

# ...
# app = FastAPI(title="BCL Activate API")
# ...

# --- INÍCIO DA CONFIGURAÇÃO DE CORS ---
# Esta secção autoriza o seu front-end a comunicar com a sua API.
origins = [
    "*"  # Permite todas as origens (ideal para testes)
    # Para produção, pode restringir, ex: "https://o-seu-site.lovable.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- FIM DA CONFIGURAÇÃO DE CORS ---

# O resto do seu código, como @app.post("/activate"), continua aqui...

# Adicionar este import no topo do seu ficheiro
from fastapi.middleware.cors import CORSMiddleware

# ... (a sua linha app = FastAPI(...) fica aqui)

# --- INÍCIO DA CONFIGURAÇÃO DE CORS ---
# Esta secção autoriza o seu front-end (Lovable) a comunicar com a sua API.
origins = [
    "*",  # Permite todas as origens (bom para testes, mas para produção restrinja ao domínio do Lovable)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Permite todos os métodos (GET, POST, etc.)
    allow_headers=["*"], # Permite todos os cabeçalhos
)
# --- FIM DA CONFIGURAÇÃO DE CORS ---

# O resto do seu código continua normalmente a partir daqui...

@app.post("/activate")
def ativar_lead(lead: Lead):
    print(f"Lead recebido para ativação: {lead.nome} do nicho {lead.nicho}")
    
    prompt_personalizado = criar_prompt_para_lead(lead)
    print(f"--- Prompt Gerado para a IA ---\n{prompt_personalizado}\n---------------------")
    
    mensagem_final = ""

    try:
        if not GOOGLE_API_KEY:
            raise ValueError("Chave do Gemini não configurada, a saltar para a OpenAI.")
        print("A tentar gerar mensagem com o Google Gemini...")
        model_gemini = genai.GenerativeModel('gemini-1.5-flash-latest')
        response = model_gemini.generate_content(prompt_personalizado)
        mensagem_final = response.text
        print("Mensagem gerada com sucesso pelo Gemini.")

    except (google_exceptions.ResourceExhausted, ValueError) as e:
        print(f"AVISO: A chamada ao Gemini falhou ({e}). A tentar com a OpenAI como fallback...")
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Você é um assistente de marketing direto especialista em refinar mensagens de WhatsApp."},
                    {"role": "user", "content": prompt_personalizado}
                ],
                temperature=0.7,
            )
            mensagem_final = response.choices[0].message.content
            print("Mensagem gerada com sucesso pela OpenAI.")
        except Exception as openai_error:
            print(f"ERRO: A chamada de fallback à OpenAI também falhou: {openai_error}")
            raise HTTPException(status_code=500, detail="Ambos os serviços de IA falharam.")
            
    except Exception as e:
        print(f"ERRO: Ocorreu um erro inesperado na geração da mensagem: {e}")
        raise HTTPException(status_code=500, detail="Ocorreu um erro inesperado ao gerar a mensagem.")

    if not mensagem_final:
        raise HTTPException(status_code=500, detail="Não foi possível gerar uma mensagem.")

    print(f"--- Mensagem Final Gerada ---\n{mensagem_final}\n-----------------------------")
    
    sucesso_envio = enviar_whatsapp(lead.telefone, mensagem_final)
    
    return {
        "status": "sucesso",
        "lead_email": lead.email,
        "mensagem_gerada": mensagem_final,
        "status_envio_whatsapp": "Enviado com sucesso" if sucesso_envio else "Falha no envio"
    }