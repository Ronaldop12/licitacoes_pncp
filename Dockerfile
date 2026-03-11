FROM python:3.11-slim AS builder

WORKDIR /app

# Instalar dependências de compilação
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Imagem final (sem build-essential) ---
FROM python:3.11-slim

WORKDIR /app

# Copiar dependências compiladas
COPY --from=builder /install /usr/local

# Usuário não-root
RUN useradd -m -r appuser && mkdir -p dados config && chown -R appuser:appuser /app

# Copiar código da aplicação
COPY --chown=appuser:appuser . .

USER appuser

# Expor porta do Streamlit
EXPOSE 8501

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

# Executar dashboard
ENTRYPOINT ["streamlit", "run", "dashboard.py", \
    "--server.port=8501", \
    "--server.address=0.0.0.0", \
    "--server.headless=true"]
