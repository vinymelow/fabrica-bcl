import os
import time
import subprocess
from github import Github
from dotenv import load_dotenv

# Carrega os nossos segredos do ficheiro .env
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
# Opcional: Se tiver uma organização no GitHub, coloque o nome aqui
GITHUB_ORG_NAME = "BlueDigitalSolutions" # Mude para "" se for usar a sua conta pessoal

def create_and_push_repo(local_project_path: str, client_name: str) -> str:
    """
    Cria um repositório privado no GitHub e envia o código do projeto local.
    """
    if not GITHUB_TOKEN:
        raise ValueError("O GITHUB_TOKEN não está configurado no ficheiro .env")

    g = Github(GITHUB_TOKEN)
    repo_name = f"bcl-instance-{client_name.lower().replace(' ', '-')}-{int(time.time())}"
    
    try:
        # Tenta obter a organização; se não, usa o utilizador autenticado
        entity = g.get_organization(GITHUB_ORG_NAME) if GITHUB_ORG_NAME else g.get_user()
        print(f"A criar repositório privado '{repo_name}' na conta '{entity.login}'...")
        repo = entity.create_repo(repo_name, private=True, auto_init=False)
        print("Repositório criado com sucesso.")
    except Exception as e:
        raise Exception(f"Falha ao criar o repositório no GitHub: {e}")

    # Usa a linha de comando para inicializar o Git e enviar os ficheiros
    try:
        print(f"A enviar código de '{local_project_path}' para o GitHub...")
        # Usamos capture_output=True para suprimir os logs detalhados do git
        subprocess.run(["git", "init"], cwd=local_project_path, check=True, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=local_project_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Commit inicial de provisionamento automático"], cwd=local_project_path, check=True, capture_output=True)
        subprocess.run(["git", "branch", "-M", "main"], cwd=local_project_path, check=True, capture_output=True)
        # Usamos o repo.clone_url que já inclui o token para autenticação
        remote_url = f"https://{GITHUB_TOKEN}@{repo.clone_url.split('//')[1]}"
        subprocess.run(["git", "remote", "add", "origin", remote_url], cwd=local_project_path, check=True, capture_output=True)
        subprocess.run(["git", "push", "-u", "origin", "main"], cwd=local_project_path, check=True, capture_output=True)
        print("Código enviado para o GitHub com sucesso.")
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.decode()
        raise Exception(f"Falha ao executar comandos Git: {error_message}")

    return repo.clone_url
