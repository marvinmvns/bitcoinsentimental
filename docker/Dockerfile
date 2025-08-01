# ============================================================================
# Dockerfile - Sistema Trading Bitcoin com Ollama LLM
# ============================================================================
# Autor: Manus AI
# Versão: 1.0
# Data: 31 de Julho de 2025
#
# Este Dockerfile cria uma imagem containerizada do sistema de trading
# ============================================================================

FROM ubuntu:22.04

# Metadados
LABEL maintainer="Manus AI"
LABEL version="1.0"
LABEL description="Sistema de Trading Bitcoin com Ollama LLM"

# Evitar prompts interativos durante instalação
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Configurações do sistema
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TRADING_ENV=production
ENV INSTALL_DIR=/opt/bitcoin-trading-system

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    htop \
    jq \
    unzip \
    software-properties-common \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Criar usuário não-root
RUN useradd -m -s /bin/bash bitcoin-trader && \
    mkdir -p $INSTALL_DIR && \
    chown -R bitcoin-trader:bitcoin-trader $INSTALL_DIR

# Instalar Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Mudar para usuário não-root
USER bitcoin-trader
WORKDIR $INSTALL_DIR

# Criar estrutura de diretórios
RUN mkdir -p {src,data,logs,config,models,results,backup}

# Configurar ambiente Python
RUN python3.11 -m venv venv && \
    . venv/bin/activate && \
    pip install --upgrade pip setuptools wheel

# Copiar requirements
COPY --chown=bitcoin-trader:bitcoin-trader requirements.txt .

# Instalar dependências Python
RUN . venv/bin/activate && \
    pip install -r requirements.txt

# Copiar arquivos do sistema
COPY --chown=bitcoin-trader:bitcoin-trader src/ /opt/bitcoin-trading-system/src/
COPY --chown=bitcoin-trader:bitcoin-trader config/ /opt/bitcoin-trading-system/config/

# Tornar scripts executáveis
RUN chmod +x src/*.py

# Voltar para root para configurações finais
USER root

# Configurar supervisor
COPY supervisord.conf /etc/supervisor/conf.d/bitcoin-trading.conf

# Script de inicialização
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Expor portas
EXPOSE 8080 11434

# Volumes para persistência
VOLUME ["$INSTALL_DIR/data", "$INSTALL_DIR/logs", "$INSTALL_DIR/results"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:11434/api/tags || exit 1

# Ponto de entrada
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["supervisord", "-c", "/etc/supervisor/supervisord.conf"]

