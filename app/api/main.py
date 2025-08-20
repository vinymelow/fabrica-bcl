from fastapi import FastAPI, HTTPException, BackgroundTasks
from .models import CampaignConfiguration
import shutil
import os

# Importar os nossos "operários" (os serviços)
from ..services import project_builder, github_service, render_service, notification_service

app = FastAPI(title="BCL Provisioning API")


def provisioning_task(config: CampaignConfiguration):
    """
    Esta é a tarefa de longa duração que corre em segundo plano.
    É a nossa "linha de montagem".
    """
    local_project_path = ""
    try:
        # Passo 1 da linha de montagem: Construir o projeto local personalizado
        print(f"INICIANDO: Construção do projeto para {config.client_name}")
        local_project_path = project_builder.create_custom_project(config)
        
        # Passo 2: Criar o repositório no GitHub e enviar o código
        print("INICIANDO: Criação do repositório no GitHub")
        repo_url = github_service.create_and_push_repo(local_project_path, config.client_name)
        
        # Passo 3: Fazer o deploy da nova instância no Render
        print("INICIANDO: Deploy da nova instância no Render")
        service_url = render_service.deploy_new_service(repo_url, config.client_name, config)
        
        # Passo 4: Notificar o cliente sobre o sucesso
        if service_url:
            print("INICIANDO: Notificação para o cliente")
            notification_service.notify_client(config.client_email, service_url, config.lead_source_type)
            print(f"SUCESSO: Provisionamento para {config.client_name} concluído!")
        else:
            raise Exception("O URL do serviço do Render não foi obtido.")

    except Exception as e:
        # Se qualquer passo falhar, registamos o erro.
        # Num sistema real, enviaríamos uma notificação de erro para a nossa equipa.
        print(f"ERRO DE PROVISIONAMENTO para {config.client_name}: {e}")
    
    finally:
        # O último passo é sempre limpar a pasta temporária do projeto,
        # quer o processo tenha tido sucesso ou tenha falhado.
        if local_project_path and os.path.exists(local_project_path):
            shutil.rmtree(local_project_path)
            print(f"Limpeza: Pasta temporária {local_project_path} removida.")


@app.post("/provision/new-instance")
async def provision_new_instance(config: CampaignConfiguration, background_tasks: BackgroundTasks):
    """
    Este é o nosso endpoint principal. Ele recebe a configuração, responde imediatamente
    e adiciona a tarefa de provisionamento para ser executada em segundo plano.
    """
    # Adiciona a nossa "linha de montagem" (provisioning_task) a uma fila de tarefas
    background_tasks.add_task(provisioning_task, config)
    
    # Devolve uma resposta imediata ao utilizador
    return {
        "status": "iniciado", 
        "message": f"O provisionamento para o cliente {config.client_name} foi iniciado. Você receberá uma notificação quando estiver concluído."
    }