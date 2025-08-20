# Ficheiro: Dockerfile

# Passo 1: A Base
FROM python:3.11-slim

# Passo 2: Área de trabalho
WORKDIR /code

# Passo 3: Copiar lista de ingredientes
COPY requirements.txt requirements.txt

# Passo 4: Instalar ingredientes
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Passo 5: Copiar o código da aplicação
COPY ./app /code/app

# Passo 6: Expor a porta (metadata para a nuvem)
EXPOSE 8080

# Passo 7: O Comando Final (usa a variável $PORT, compatível com a nuvem)
CMD uvicorn app.api.main:app --host 0.0.0.0 --port $PORT