# --- Estágio 1: build ---
FROM python:3.12-slim AS builder
WORKDIR /src

# Copia lista de dependências e instala em diretório de usuário
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# --- Estágio 2: runtime ---
FROM python:3.12-alpine
WORKDIR /app

# Traz as dependências instaladas no builder
COPY --from=builder /root/.local /root/.local

# Copia todo o código da API
COPY . .

# Ajusta PATH para achar o pip instalado em --user
ENV PATH=/root/.local/bin:$PATH

# Comando padrão ao iniciar o container
CMD ["python", "app.py"]
