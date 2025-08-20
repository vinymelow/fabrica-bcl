# fabrica-bcl/app/services/github_service.py

import os
import logging
from github import Github
from git import Repo

logger = logging.getLogger(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")

def create_and_push_to_github(repo_path: str, repo_name: str) -> str:
    """
    Cria um repositório privado no GitHub e faz push do código local.
    """
    if not GITHUB_TOKEN or not GITHUB_USERNAME:
        raise ValueError("As variáveis de ambiente GITHUB_TOKEN e GITHUB_USERNAME são obrigatórias.")

    try:
        # Autentica-se no GitHub
        g = Github(GITHUB_TOKEN)
        user = g.get_user(GITHUB_USERNAME)

        # Cria o repositório privado
        logger.info(f"A criar repositório privado: {repo_name}")
        repo = user.create_repo(repo_name, private=True)
        repo_url = repo.clone_url
        logger.info(f"Repositório criado com sucesso: {repo_url}")

        # Inicializa o repositório local e faz o push
        local_repo = Repo.init(repo_path)
        local_repo.index.add("*")
        local_repo.index.commit("Commit inicial da instância BCL")

        origin = local_repo.create_remote("origin", repo_url)
        # A autenticação é feita no URL para o push
        push_url = repo_url.replace("https://", f"https://{GITHUB_USERNAME}:{GITHUB_TOKEN}@")
        origin.set_url(push_url)

        origin.push(refspec="main:main")
        logger.info(f"Push para o repositório {repo_name} concluído com sucesso.")

        return repo_url

    except Exception as e:
        logger.error(f"Falha ao criar ou fazer push para o repositório GitHub: {e}", exc_info=True)
        raise