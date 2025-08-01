#!/bin/bash

# ============================================================================
# Docker Entrypoint - Sistema Trading Bitcoin com Ollama LLM
# ============================================================================
# Script de inicialização para container Docker
# ============================================================================

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Configurações
INSTALL_DIR="/opt/bitcoin-trading-system"
OLLAMA_MODELS=("llama3.2:1b")

init_ollama() {
    log_info "Inicializando Ollama..."
    
    # Iniciar Ollama em background
    ollama serve &
    OLLAMA_PID=$!
    
    # Aguardar Ollama inicializar
    log_info "Aguardando Ollama inicializar..."
    for i in {1..30}; do
        if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
            log_success "Ollama inicializado"
            break
        fi
        
        if [ $i -eq 30 ]; then
            log_error "Timeout aguardando Ollama"
            exit 1
        fi
        
        sleep 2
    done
    
    # Baixar modelos se necessário
    for model in "${OLLAMA_MODELS[@]}"; do
        if ! ollama list | grep -q "$model"; then
            log_info "Baixando modelo: $model"
            ollama pull "$model"
        else
            log_info "Modelo $model já disponível"
        fi
    done
}

setup_environment() {
    log_info "Configurando ambiente..."
    
    # Criar diretórios se não existirem
    mkdir -p "$INSTALL_DIR"/{data,logs,results}
    
    # Configurar permissões
    chown -R bitcoin-trader:bitcoin-trader "$INSTALL_DIR"
    
    # Ativar ambiente virtual
    cd "$INSTALL_DIR"
    source venv/bin/activate
    
    log_success "Ambiente configurado"
}

run_health_checks() {
    log_info "Executando verificações de saúde..."
    
    # Verificar Ollama
    if ! curl -s http://localhost:11434/api/tags > /dev/null; then
        log_error "Ollama não está respondendo"
        return 1
    fi
    
    # Verificar Python
    if ! python3.11 --version > /dev/null; then
        log_error "Python não encontrado"
        return 1
    fi
    
    # Verificar dependências
    cd "$INSTALL_DIR"
    source venv/bin/activate
    
    if ! python -c "import langchain, requests, numpy, pandas" 2>/dev/null; then
        log_error "Dependências Python não encontradas"
        return 1
    fi
    
    log_success "Verificações de saúde concluídas"
    return 0
}

start_monitoring() {
    log_info "Iniciando monitoramento..."
    
    # Criar script de monitoramento simples
    cat > /tmp/monitor.sh << 'EOF'
#!/bin/bash
while true; do
    # Verificar se Ollama está respondendo
    if ! curl -s http://localhost:11434/api/tags > /dev/null; then
        echo "$(date): ALERTA - Ollama não está respondendo" >> /opt/bitcoin-trading-system/logs/monitor.log
    fi
    
    # Verificar uso de memória
    memory_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    if (( $(echo "$memory_usage > 90" | bc -l) )); then
        echo "$(date): ALERTA - Uso de memória alto: ${memory_usage}%" >> /opt/bitcoin-trading-system/logs/monitor.log
    fi
    
    sleep 60
done
EOF
    
    chmod +x /tmp/monitor.sh
    /tmp/monitor.sh &
    
    log_success "Monitoramento iniciado"
}

# Função principal
main() {
    echo "============================================"
    echo "🚀 Iniciando Sistema Trading Bitcoin"
    echo "============================================"
    
    # Verificar se é comando de ajuda
    if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
        echo "Uso: docker run [opções] bitcoin-trading-system [comando]"
        echo ""
        echo "Comandos:"
        echo "  (padrão)    Iniciar sistema completo"
        echo "  bash        Abrir shell interativo"
        echo "  test        Executar testes"
        echo "  demo        Executar demo"
        echo ""
        exit 0
    fi
    
    # Configurar ambiente
    setup_environment
    
    # Inicializar Ollama
    init_ollama
    
    # Executar verificações
    if ! run_health_checks; then
        log_error "Verificações de saúde falharam"
        exit 1
    fi
    
    # Iniciar monitoramento
    start_monitoring
    
    # Executar comando específico ou padrão
    case "${1:-default}" in
        "bash")
            log_info "Abrindo shell interativo..."
            exec /bin/bash
            ;;
        "test")
            log_info "Executando testes..."
            cd "$INSTALL_DIR"
            source venv/bin/activate
            python src/test_system.py
            ;;
        "demo")
            log_info "Executando demo..."
            cd "$INSTALL_DIR"
            source venv/bin/activate
            python src/quick_demo.py
            ;;
        "default"|"supervisord")
            log_info "Iniciando sistema completo..."
            exec "$@"
            ;;
        *)
            log_info "Executando comando personalizado: $*"
            exec "$@"
            ;;
    esac
}

# Tratamento de sinais
trap 'log_info "Recebido sinal de parada, finalizando..."; kill $OLLAMA_PID 2>/dev/null || true; exit 0' SIGTERM SIGINT

# Executar função principal
main "$@"

