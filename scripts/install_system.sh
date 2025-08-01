#!/bin/bash

# ============================================================================
# Script de Instalação Automatizada - Sistema Trading Bitcoin com Ollama LLM
# ============================================================================
# Autor: Manus AI
# Versão: 1.0
# Data: 31 de Julho de 2025
#
# Este script automatiza a instalação completa do sistema de trading Bitcoin
# com análise de sentimento usando Ollama LLM.
# ============================================================================

set -e  # Parar em caso de erro
set -u  # Parar se variável não definida

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações padrão
INSTALL_DIR="/opt/bitcoin-trading-system"
USER_NAME="bitcoin-trader"
PYTHON_VERSION="3.11"
OLLAMA_MODELS=("llama3.2:1b" "gemma2:9b" "deepseek-r1:7b")

# Funções utilitárias
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "Este script não deve ser executado como root"
        log_info "Execute como usuário normal com privilégios sudo"
        exit 1
    fi
}

check_sudo() {
    if ! sudo -n true 2>/dev/null; then
        log_error "Este script requer privilégios sudo"
        log_info "Execute: sudo -v"
        exit 1
    fi
}

detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
    else
        log_error "Sistema operacional não suportado"
        exit 1
    fi
    
    log_info "Sistema detectado: $OS $OS_VERSION"
}

install_system_dependencies() {
    log_info "Instalando dependências do sistema..."
    
    case $OS in
        ubuntu|debian)
            sudo apt update
            sudo apt install -y \
                curl \
                wget \
                git \
                build-essential \
                python${PYTHON_VERSION} \
                python${PYTHON_VERSION}-venv \
                python${PYTHON_VERSION}-dev \
                python3-pip \
                htop \
                jq \
                unzip \
                software-properties-common
            ;;
        centos|rhel|fedora)
            if command -v dnf &> /dev/null; then
                sudo dnf update -y
                sudo dnf groupinstall -y "Development Tools"
                sudo dnf install -y \
                    curl \
                    wget \
                    git \
                    python${PYTHON_VERSION} \
                    python${PYTHON_VERSION}-venv \
                    python${PYTHON_VERSION}-devel \
                    python3-pip \
                    htop \
                    jq \
                    unzip
            else
                sudo yum update -y
                sudo yum groupinstall -y "Development Tools"
                sudo yum install -y \
                    curl \
                    wget \
                    git \
                    python${PYTHON_VERSION} \
                    python${PYTHON_VERSION}-venv \
                    python${PYTHON_VERSION}-devel \
                    python3-pip \
                    htop \
                    jq \
                    unzip
            fi
            ;;
        *)
            log_error "Sistema operacional $OS não suportado"
            exit 1
            ;;
    esac
    
    log_success "Dependências do sistema instaladas"
}

create_user() {
    if id "$USER_NAME" &>/dev/null; then
        log_warning "Usuário $USER_NAME já existe"
    else
        log_info "Criando usuário $USER_NAME..."
        sudo useradd -m -s /bin/bash "$USER_NAME"
        sudo usermod -aG sudo "$USER_NAME"
        log_success "Usuário $USER_NAME criado"
    fi
}

create_directories() {
    log_info "Criando estrutura de diretórios..."
    
    sudo mkdir -p "$INSTALL_DIR"/{src,data,logs,config,models,results,backup}
    sudo chown -R "$USER_NAME:$USER_NAME" "$INSTALL_DIR"
    sudo chmod -R 755 "$INSTALL_DIR"
    
    log_success "Estrutura de diretórios criada"
}

install_ollama() {
    log_info "Instalando Ollama..."
    
    if command -v ollama &> /dev/null; then
        log_warning "Ollama já está instalado"
        ollama --version
    else
        curl -fsSL https://ollama.com/install.sh | sh
        
        # Verificar se o serviço está rodando
        if ! systemctl is-active --quiet ollama; then
            sudo systemctl start ollama
            sudo systemctl enable ollama
        fi
        
        log_success "Ollama instalado e configurado"
    fi
    
    # Aguardar o serviço inicializar
    log_info "Aguardando Ollama inicializar..."
    sleep 5
    
    # Verificar conectividade
    if curl -s http://localhost:11434/api/tags > /dev/null; then
        log_success "Ollama está respondendo"
    else
        log_error "Ollama não está respondendo"
        exit 1
    fi
}

download_ollama_models() {
    log_info "Baixando modelos Ollama..."
    
    for model in "${OLLAMA_MODELS[@]}"; do
        log_info "Baixando modelo: $model"
        
        if ollama list | grep -q "$model"; then
            log_warning "Modelo $model já existe"
        else
            ollama pull "$model"
            log_success "Modelo $model baixado"
        fi
    done
    
    log_info "Modelos disponíveis:"
    ollama list
}

setup_python_environment() {
    log_info "Configurando ambiente Python..."
    
    # Mudar para usuário dedicado para criar ambiente virtual
    sudo -u "$USER_NAME" bash << EOF
cd "$INSTALL_DIR"

# Criar ambiente virtual
python${PYTHON_VERSION} -m venv venv

# Ativar ambiente virtual
source venv/bin/activate

# Atualizar pip
pip install --upgrade pip setuptools wheel

# Instalar dependências do requirements.txt se existir
if [[ -f "requirements.txt" ]]; then
    echo "Instalando dependências do requirements.txt..."
    pip install -r requirements.txt
else
    # Instalar dependências principais manualmente
    pip install langchain==0.3.27
    pip install langchain-community==0.3.27
    pip install langchain-core==0.3.72
    
    # Dependências de análise de sentimento
    pip install vaderSentiment==3.3.2
    pip install textblob==0.17.1
    
    # Dependências de análise de dados
    pip install numpy==1.24.3
    pip install pandas==2.0.3
    pip install matplotlib==3.7.2
    pip install seaborn==0.12.2
    
    # Dependências de rede e utilitários
    pip install requests==2.31.0
    pip install tenacity==8.2.3
    pip install python-dotenv==1.0.0
    pip install psutil==5.9.5
    pip install click==8.1.6
    pip install rich==13.5.2
    
    # Dependências opcionais
    pip install plotly==5.15.0
    pip install scikit-learn==1.3.0
    pip install yfinance==0.2.18
    pip install ccxt==4.0.77
    
    # Dependências de desenvolvimento
    pip install pytest==7.4.0
    pip install black==23.7.0
    pip install flake8==6.0.0
fi

# Configurar Python path executando setup.py se existir
if [[ -f "setup.py" ]]; then
    python setup.py
fi

echo "Ambiente Python configurado com sucesso"
EOF
    
    log_success "Ambiente Python configurado"
}


create_secure_env_file() {
    log_info "Criando arquivo .env com permissões seguras..."
    
    # Criar arquivo temporário
    local temp_env=$(mktemp)
    
    # Escrever conteúdo no arquivo temporário
    cat > "$temp_env" << 'EOF'
# Configurações do Sistema
TRADING_ENV=production
DEBUG=false

# Configurações de Monitoramento
ENABLE_METRICS=true
METRICS_PORT=8080

# Configurações de Segurança
LOG_LEVEL=INFO
MAX_CONCURRENT_REQUESTS=10
EOF
    
    # Mover arquivo para local final com sudo e definir permissões
    sudo mv "$temp_env" "$INSTALL_DIR/config/.env"
    sudo chown "$USER_NAME:$USER_NAME" "$INSTALL_DIR/config/.env"
    sudo sudo chmod 600 "$INSTALL_DIR/config/.env"
    
    log_success "Arquivo .env criado com permissões seguras"
}


create_secure_env_file() {
    log_info "Criando arquivo .env com permissões seguras..."
    
    # Criar arquivo temporário
    local temp_env=$(mktemp)
    
    # Escrever conteúdo no arquivo temporário
    cat > "$temp_env" << 'EOF'
# Configurações do Sistema
TRADING_ENV=production
DEBUG=false

# Configurações de Monitoramento
ENABLE_METRICS=true
METRICS_PORT=8080

# Configurações de Segurança
LOG_LEVEL=INFO
MAX_CONCURRENT_REQUESTS=10
EOF
    
    # Mover arquivo para local final com sudo e definir permissões
    sudo mv "$temp_env" "$INSTALL_DIR/config/.env"
    sudo chown "$USER_NAME:$USER_NAME" "$INSTALL_DIR/config/.env"
    sudo sudo chmod 600 "$INSTALL_DIR/config/.env"
    
    log_success "Arquivo .env criado com permissões seguras"
}


create_secure_env_file() {
    log_info "Criando arquivo .env com permissões seguras..."
    
    # Criar arquivo temporário
    local temp_env=$(mktemp)
    
    # Escrever conteúdo no arquivo temporário
    cat > "$temp_env" << 'EOF'
# Configurações do Sistema
TRADING_ENV=production
DEBUG=false

# Configurações de Monitoramento
ENABLE_METRICS=true
METRICS_PORT=8080

# Configurações de Segurança
LOG_LEVEL=INFO
MAX_CONCURRENT_REQUESTS=10
EOF
    
    # Mover arquivo para local final com sudo e definir permissões
    sudo mv "$temp_env" "$INSTALL_DIR/config/.env"
    sudo chown "$USER_NAME:$USER_NAME" "$INSTALL_DIR/config/.env"
    sudo chmod 600 "$INSTALL_DIR/config/.env"
    
    log_success "Arquivo .env criado com permissões seguras"
}

create_configuration_files() {
    log_info "Criando arquivos de configuração..."
    
    # Arquivo de configuração principal
    sudo -u "$USER_NAME" tee "$INSTALL_DIR/config/trading_config.json" > /dev/null << 'EOF'
{
  "ollama": {
    "base_url": "http://localhost:11434",
    "primary_model": "llama3.2:1b",
    "backup_model": "gemma2:9b",
    "specialized_model": "deepseek-r1:7b",
    "timeout": 30,
    "max_retries": 3,
    "temperature": 0.1,
    "num_predict": 100
  },
  "sentiment": {
    "min_confidence": 0.6,
    "ollama_weight": 0.6,
    "vader_weight": 0.25,
    "textblob_weight": 0.15,
    "batch_size": 5,
    "cache_enabled": true,
    "cache_ttl": 3600
  },
  "trading": {
    "initial_capital": 10000.0,
    "position_size": 0.1,
    "min_confidence": 0.6,
    "stop_loss": 0.05,
    "take_profit": 0.15,
    "technical_weight": 0.6,
    "sentiment_weight": 0.4
  },
  "data_collection": {
    "reddit_subreddits": [
      "Bitcoin",
      "BitcoinMarkets", 
      "CryptoCurrency",
      "btc",
      "CryptoMarkets",
      "BitcoinBeginners",
      "investing",
      "stocks"
    ],
    "collection_interval": 300,
    "max_posts_per_subreddit": 30,
    "min_score": 5,
    "hours_lookback": 24
  },
  "technical_analysis": {
    "rsi_period": 14,
    "rsi_overbought": 70,
    "rsi_oversold": 30,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
    "bb_period": 20,
    "bb_std": 2,
    "sma_short": 20,
    "sma_long": 50
  },
  "logging": {
    "level": "INFO",
    "file_path": "/opt/bitcoin-trading-system/logs/trading.log",
    "max_file_size": "10MB",
    "backup_count": 5,
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  },
  "monitoring": {
    "metrics_enabled": true,
    "metrics_interval": 60,
    "alert_thresholds": {
      "error_rate": 0.05,
      "response_time": 30.0,
      "memory_usage": 0.8
    }
  }
}
EOF

    # Arquivo de variáveis de ambiente - usar função segura
    create_secure_env_file
    
    log_success "Arquivos de configuração criados"
}

copy_system_files() {
    log_info "Copiando arquivos do sistema..."
    
    # Determinar diretório base do projeto
    local PROJECT_ROOT
    if [[ -f "../src/sentiment/enhanced_sentiment_analyzer.py" ]]; then
        PROJECT_ROOT="$(pwd)/.."
    elif [[ -f "./src/sentiment/enhanced_sentiment_analyzer.py" ]]; then
        PROJECT_ROOT="$(pwd)"
    else
        log_error "Não foi possível encontrar os arquivos do projeto"
        log_info "Execute o script a partir do diretório raiz do projeto ou do diretório scripts/"
        exit 1
    fi
    
    log_info "Diretório do projeto: $PROJECT_ROOT"
    
    # Copiar toda a estrutura src/
    if [[ -d "$PROJECT_ROOT/src" ]]; then
        sudo cp -r "$PROJECT_ROOT/src"/* "$INSTALL_DIR/src/"
        sudo chown -R "$USER_NAME:$USER_NAME" "$INSTALL_DIR/src/"
        sudo chmod -R 755 "$INSTALL_DIR/src/"
        log_success "Estrutura src/ copiada"
    fi
    
    # Copiar scripts auxiliares
    if [[ -d "$PROJECT_ROOT/scripts" ]]; then
        sudo mkdir -p "$INSTALL_DIR/scripts"
        sudo cp -r "$PROJECT_ROOT/scripts"/* "$INSTALL_DIR/scripts/"
        sudo chown -R "$USER_NAME:$USER_NAME" "$INSTALL_DIR/scripts/"
        sudo chmod +x "$INSTALL_DIR/scripts"/*.sh
        log_success "Scripts auxiliares copiados"
    fi
    
    # Copiar exemplos
    if [[ -d "$PROJECT_ROOT/examples" ]]; then
        sudo mkdir -p "$INSTALL_DIR/examples"
        sudo cp -r "$PROJECT_ROOT/examples"/* "$INSTALL_DIR/examples/"
        sudo chown -R "$USER_NAME:$USER_NAME" "$INSTALL_DIR/examples/"
        log_success "Exemplos copiados"
    fi
    
    # Copiar arquivo requirements.txt se existir
    if [[ -f "$PROJECT_ROOT/requirements.txt" ]]; then
        sudo cp "$PROJECT_ROOT/requirements.txt" "$INSTALL_DIR/"
        sudo chown "$USER_NAME:$USER_NAME" "$INSTALL_DIR/requirements.txt"
        log_success "requirements.txt copiado"
    fi
    
    # Copiar setup.py se existir
    if [[ -f "$PROJECT_ROOT/setup.py" ]]; then
        sudo cp "$PROJECT_ROOT/setup.py" "$INSTALL_DIR/"
        sudo chown "$USER_NAME:$USER_NAME" "$INSTALL_DIR/setup.py"
        log_success "setup.py copiado"
    fi
}

create_systemd_services() {
    log_info "Criando serviços systemd..."
    
    # Serviço principal
    sudo tee /etc/systemd/system/bitcoin-trading-system.service > /dev/null << EOF
[Unit]
Description=Bitcoin Trading System with Ollama LLM
After=network.target ollama.service
Requires=ollama.service

[Service]
Type=simple
User=$USER_NAME
Group=$USER_NAME
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/src/trading/bitcoin_trading_system_with_ollama.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Limites de recursos
LimitNOFILE=65536
MemoryMax=4G

[Install]
WantedBy=multi-user.target
EOF

    # Recarregar systemd
    sudo systemctl daemon-reload
    
    log_success "Serviços systemd criados"
}

setup_logrotate() {
    log_info "Configurando rotação de logs..."
    
    sudo tee /etc/logrotate.d/bitcoin-trading > /dev/null << EOF
$INSTALL_DIR/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $USER_NAME $USER_NAME
    postrotate
        systemctl reload bitcoin-trading-system || true
    endscript
}
EOF
    
    log_success "Rotação de logs configurada"
}

run_tests() {
    log_info "Executando testes do sistema..."
    
    sudo -u "$USER_NAME" bash << EOF
cd "$INSTALL_DIR"
source venv/bin/activate

# Teste de conectividade Ollama
python3 -c "
import requests
try:
    response = requests.get('http://localhost:11434/api/tags', timeout=5)
    if response.status_code == 200:
        print('✅ Ollama conectado')
    else:
        print('❌ Erro Ollama:', response.status_code)
        exit(1)
except Exception as e:
    print('❌ Erro Ollama:', e)
    exit(1)
"

# Teste de dependências Python
python3 -c "
try:
    import langchain
    import numpy as np
    import pandas as pd
    import requests
    import matplotlib.pyplot as plt
    print('✅ Dependências Python OK')
except Exception as e:
    print('❌ Erro dependências:', e)
    exit(1)
"

echo "✅ Todos os testes passaram"
EOF
    
    log_success "Testes concluídos com sucesso"
}

create_quick_start_script() {
    log_info "Criando script de início rápido..."
    
    sudo -u "$USER_NAME" tee "$INSTALL_DIR/quick_start.sh" > /dev/null << 'EOF'
#!/bin/bash

# Script de início rápido para o sistema de trading Bitcoin

INSTALL_DIR="/opt/bitcoin-trading-system"

echo "🚀 Sistema de Trading Bitcoin com Ollama LLM"
echo "============================================"

cd "$INSTALL_DIR"
source venv/bin/activate

echo "📊 Status do sistema:"
echo "- Ollama: $(curl -s http://localhost:11434/api/tags > /dev/null && echo "✅ Online" || echo "❌ Offline")"
echo "- Modelos: $(ollama list | wc -l) disponíveis"
echo "- Python: $(python --version)"

echo ""
echo "Comandos disponíveis:"
echo "1. Executar sistema completo:"
echo "   python src/trading/bitcoin_trading_system_with_ollama.py"
echo ""
echo "2. Executar demonstração:"
echo "   python examples/main_demo.py"
echo ""
echo "3. Interface CLI:"
echo "   python src/cli/btc_trading_cli.py --help"
echo ""
echo "4. Executar benchmark:"
echo "   python src/core/sentiment_benchmark.py"
echo ""
echo "5. Testar Ollama:"
echo "   python src/core/test_ollama_simple.py"
echo ""
echo "6. Monitorar logs:"
echo "   tail -f logs/trading.log"
echo ""
echo "Para mais informações, consulte a documentação em:"
echo "$INSTALL_DIR/docs/"
EOF

    sudo sudo chmod +x "$INSTALL_DIR/quick_start.sh"
    
    log_success "Script de início rápido criado"
}

print_installation_summary() {
    echo ""
    echo "============================================"
    log_success "INSTALAÇÃO CONCLUÍDA COM SUCESSO!"
    echo "============================================"
    echo ""
    echo "📁 Diretório de instalação: $INSTALL_DIR"
    echo "👤 Usuário do sistema: $USER_NAME"
    echo "🐍 Ambiente Python: $INSTALL_DIR/venv"
    echo "🤖 Modelos Ollama: ${#OLLAMA_MODELS[@]} instalados"
    echo ""
    echo "🚀 Para iniciar o sistema:"
    echo "   sudo su - $USER_NAME"
    echo "   cd $INSTALL_DIR"
    echo "   ./quick_start.sh"
    echo ""
    echo "🔧 Para gerenciar o serviço:"
    echo "   sudo systemctl start bitcoin-trading-system"
    echo "   sudo systemctl status bitcoin-trading-system"
    echo "   sudo systemctl stop bitcoin-trading-system"
    echo ""
    echo "📊 Para monitorar:"
    echo "   tail -f $INSTALL_DIR/logs/trading.log"
    echo "   sudo journalctl -u bitcoin-trading-system -f"
    echo ""
    echo "📚 Documentação completa disponível em:"
    echo "   $INSTALL_DIR/docs/"
    echo ""
    log_success "Sistema pronto para uso!"
}

# Função principal
main() {
    echo "============================================"
    echo "🚀 Instalador do Sistema Trading Bitcoin"
    echo "============================================"
    echo ""
    
    # Verificações iniciais
    check_root
    check_sudo
    detect_os
    
    # Instalação
    install_system_dependencies
    create_user
    create_directories
    install_ollama
    download_ollama_models
    setup_python_environment
    create_configuration_files
    copy_system_files
    create_systemd_services
    setup_logrotate
    run_tests
    create_quick_start_script
    
    # Resumo final
    print_installation_summary
}

# Verificar argumentos
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    echo "Uso: $0 [opções]"
    echo ""
    echo "Opções:"
    echo "  --help, -h     Mostrar esta ajuda"
    echo "  --user USER    Especificar usuário (padrão: bitcoin-trader)"
    echo "  --dir DIR      Especificar diretório (padrão: /opt/bitcoin-trading-system)"
    echo ""
    echo "Exemplo:"
    echo "  $0 --user myuser --dir /home/myuser/trading"
    exit 0
fi

# Processar argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        --user)
            USER_NAME="$2"
            shift 2
            ;;
        --dir)
            INSTALL_DIR="$2"
            shift 2
            ;;
        *)
            log_error "Argumento desconhecido: $1"
            exit 1
            ;;
    esac
done

# Executar instalação
main

