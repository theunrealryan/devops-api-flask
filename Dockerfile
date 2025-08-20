# Etapa 1: Usar uma imagem base oficial e leve do Python
FROM python:3.9-slim

# Etapa 2: Definir o diretório de trabalho dentro do contêiner
WORKDIR /app

# Etapa 3: Copiar o ficheiro de dependências e instalá-las
# Esta ordem otimiza o cache de build do Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Etapa 4: Copiar o resto do código da aplicação
COPY . .

# Etapa 5: Expor a porta em que o Gunicorn irá correr
EXPOSE 5000

# Etapa 6: Comando para executar a aplicação com um servidor de produção
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
