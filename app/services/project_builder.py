import os
import shutil
import tempfile
import uuid
from ..api.models import CampaignConfiguration

# Define o caminho para a nossa pasta de "moldes"
TEMPLATE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "templates", "bcl-activate-template"))

def create_custom_project(config: CampaignConfiguration) -> str:
    """
    Cria um projeto Python personalizado para um novo cliente a partir do template.
    """
    # 1. Cria uma pasta temporária com um nome único para evitar conflitos
    temp_dir = os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))
    print(f"A criar projeto temporário para '{config.client_name}' em: {temp_dir}")

    # 2. Copia o conteúdo do nosso "molde" para a nova pasta
    shutil.copytree(TEMPLATE_PATH, temp_dir)

    # 3. Personaliza o projeto
    #    Neste exemplo, apenas adicionamos um comentário ao main.py do template.
    #    Numa versão futura, aqui seria injetada a lógica de prompt dinâmica
    #    baseada no tom de voz, persona e objetivo da campanha do cliente.
    main_py_path = os.path.join(temp_dir, "app", "api", "main.py")
    with open(main_py_path, 'a') as f:
        f.write(f'\n# --- Configuração Personalizada para: {config.client_name} ---\n')
        f.write(f'# Objetivo da Campanha: {config.campaign_goal}\n')

    print(f"Projeto para '{config.client_name}' copiado e personalizado com sucesso.")
    
    # 4. Retorna o caminho para a pasta do novo projeto
    return temp_dir
