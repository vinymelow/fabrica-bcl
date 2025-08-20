import os
import shutil
import uuid
import re
from app.api.models import CampaignDetails

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), '..', 'templates', 'bcl-activate-template')
OUTPUT_DIR = os.path.join('/tmp', 'bcl_instances')

def create_project_from_template(campaign_id: int, details: CampaignDetails) -> tuple[str, str]:
    """
    Cria uma nova instância do projeto a partir de um template,
    personalizando o prompt da IA com base nos detalhes da campanha.
    """
    instance_uuid = str(uuid.uuid4())[:8]
    repo_name = f"bcl-instance-{campaign_id}-{instance_uuid}"
    new_project_path = os.path.join(OUTPUT_DIR, repo_name)

    # Garante que o diretório de saída exista
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Copia o template para um novo diretório
    shutil.copytree(TEMPLATE_PATH, new_project_path)

    # Personaliza o arquivo principal da API (main.py)
    _customize_main_py(new_project_path, details)

    return new_project_path, repo_name

def _customize_main_py(project_path: str, details: CampaignDetails):
    """
    Lê o main.py do template, substitui o prompt da IA e salva o arquivo.
    """
    main_py_path = os.path.join(project_path, 'app', 'api', 'main.py')

    # Mapeia os valores do frontend para descrições mais claras
    persona_map = {
        "consultor": "um consultor especialista",
        "assistente": "um assistente pessoal amigável",
        "gerente": "um gerente de contas proativo"
    }
    tone_map = {
        "profissional": "profissional e direto",
        "entusiasta": "entusiasta e energético",
        "calmo": "calmo e confiante",
        "formal": "extremamente formal"
    }
    
    # Novo prompt do sistema personalizado
    new_system_prompt = f"""
    Você é um assistente de vendas especialista em prospecção via WhatsApp.
    Sua identidade é a de '{persona_map.get(details.assistantPersona, "um assistente")}'.
    Seu tom de voz deve ser '{tone_map.get(details.toneOfVoice, "profissional")}'.
    
    Seu objetivo é criar uma mensagem inicial de WhatsApp EXTREMAMENTE PERSUASIVA E HUMANA para um novo lead.
    
    **Contexto da Campanha:**
    - **Nosso Objetivo:** {details.objective}
    - **Nossa Oferta:** {details.offer}
    - **Perfil do Cliente Ideal:** {details.customerProfile}
    
    **Regras Críticas para a Mensagem:**
    1.  **SEMPRE use o nome do lead.** Chame a pessoa pelo nome para criar uma conexão imediata.
    2.  **Mensagem Curta e Direta:** A mensagem deve ter no máximo 3 frases. As pessoas estão ocupadas.
    3.  **Clareza e Relevância:** A mensagem deve ser imediatamente clara sobre o porquê do contato, conectando a nossa oferta a uma possível necessidade do lead.
    4.  **Termine com uma Pergunta Aberta:** A mensagem DEVE terminar com uma pergunta aberta e fácil de responder para incentivar o diálogo. Não pode ser uma pergunta de "sim" ou "não".
    5.  **Sem Cara de SPAM:** A mensagem deve parecer que foi escrita por um humano, não por um robô. Use uma linguagem natural e evite jargões de marketing.
    6.  **Formatação do WhatsApp:** Use negrito (*texto*) ou itálico (_texto_) sutilmente para destacar no máximo UMA palavra ou frase chave, se ajudar na ênfase. Não abuse.
    7.  **Não se apresente formalmente no início.** A apresentação deve ser fluida e integrada à conversa, não um "Olá, meu nome é...".
    
    Baseado no nome do lead e nos seus dados (empresa, cargo, etc.), crie a mensagem perfeita.
    """

    with open(main_py_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Usando regex para substituir o conteúdo entre as tags ### SYSTEM PROMPT START ### e ### SYSTEM PROMPT END ###
    # O re.DOTALL faz com que o '.' também corresponda a quebras de linha
    pattern = r"(# ### SYSTEM PROMPT START ###\n).*(# ### SYSTEM PROMPT END ###)"
    
    # O r'\1' preserva o marcador inicial, e r'\2' o final
    replacement = f"\\1{new_system_prompt.strip()}\\2"
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    with open(main_py_path, 'w', encoding='utf-8') as f:
        f.write(new_content)