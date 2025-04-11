# Use uma imagem base do Python
FROM python:3.10-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia os arquivos do projeto para o container
COPY . /app

# Instala as dependências do sistema necessárias e configura o ambiente virtual
RUN apt-get update && apt-get install -y python3-venv && \
    python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install -r requirements.txt

# Adiciona o ambiente virtual ao PATH
ENV PATH="/opt/venv/bin:$PATH"

# Expõe a porta padrão do Flask
EXPOSE 5000

# Comando para iniciar o servidor Flask
CMD ["python", "app.py"]