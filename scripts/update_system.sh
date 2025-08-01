#!/bin/bash

# ============================================================================
# Script de Atualização - Sistema Trading Bitcoin com Ollama LLM
# ============================================================================
# Autor: Manus AI
# Versão: 1.0
# Data: 31 de Julho de 2025
#
# Este script atualiza o sistema existente com novas versões dos componentes
# ============================================================================

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configurações
INSTALL_DIR="/opt/bitcoin-trading-system"
USER_NAME="bitcoin-trader"
BACKUP_DIR="$INSTALL_DIR/backup/$(date +%Y%m%d_%H%M%S)"

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

check_installation() {
    if [[ ! -d "$INSTALL_DIR" ]]; then
        log_error "Sistema não encontrado em $INSTALL_DIR"
        log_info "Execute primeiro o script de instalação"
        exit 1
    fi
    
    if ! id "$USER_NAME" &>/dev/null; then
        log_error "Usuário $USER_NAME não encontrado"
        exit 1
    fi
    
    log_success "Instalação existente encontrada"
}

create_backup() {
    log_info "Criando backup do sistema atual..."
    
    sudo -u "$USER_NAME" mkdir -p "$BACKUP_DIR"
    
    # Backup dos arquivos de configuração
    sudo -u "$USER_NAME" cp -r "$INSTALL_DIR/config" "$BACKUP_DIR/"
    
    # Backup dos arquivos de código fonte
    sudo -u "$USER_NAME" cp -r "$INSTALL_DIR/src" "$BACKUP_DIR/"
    
    # Backup dos logs importantes
    sudo -u "$USER_NAME" cp -r "$INSTALL_DIR/logs" "$BACKUP_DIR/" 2>/dev/null || true
    
    # Backup dos resultados
    sudo -u "$USER_NAME" cp -r "$INSTALL_DIR/results" "$BACKUP_DIR/" 2>/dev/null || true
    
    log_success "Backup criado em $BACKUP_DIR"
}

stop_services() {
    log_info "Parando serviços..."
    
    if systemctl is-active --quiet bitcoin-trading-system; then
        sudo systemctl stop bitcoin-trading-system
        log_info "Serviço bitcoin-trading-system parado"
    fi
    
    if systemctl is-active --quiet bitcoin-trading-monitor; then
        sudo systemctl stop bitcoin-trading-monitor
        log_info "Serviço bitcoin-trading-monitor parado"
    fi
}

update_ollama() {
    log_info "Verificando atualizações do Ollama..."
    
    # Verificar versão atual
    current_version=$(ollama --version 2>/dev/null || echo "não instalado")
    log_info "Versão atual do Ollama: $current_version"
    
    # Atualizar Ollama
    curl -fsSL https://ollama.com/install.sh | sh
    
    # Verificar nova versão
    new_version=$(ollama --version)
    log_success "Ollama atualizado para: $new_version"
    
    # Reiniciar serviço se necessário
    if systemctl is-active --quiet ollama; then
        sudo systemctl restart ollama
        sleep 5
    fi
}

update_models() {
    log_info "Verificando atualizações dos modelos..."
    
    local models=("llama3.2:1b" "gemma2:9b" "deepseek-r1:7b")
    
    for model in "${models[@]}"; do
        if ollama list | grep -q "$model"; then
            log_info "Atualizando modelo: $model"
            ollama pull "$model"
        else
            log_warning "Modelo $model não encontrado, pulando..."
        fi
    done
    
    log_success "Modelos atualizados"
}

update_python_dependencies() {
    log_info "Atualizando dependências Python..."
    
    sudo -u "$USER_NAME" bash << 'EOF'
cd "$INSTALL_DIR"
source venv/bin/activate

# Atualizar pip
pip install --upgrade pip

# Atualizar dependências principais
pip install --upgrade \
    langchain \
    langchain-community \
    langchain-core \
    requests \
    numpy \
    pandas \
    matplotlib \
    seaborn \
    vaderSentiment \
    textblob \
    tenacity \
    psutil

echo "Dependências Python atualizadas"
EOF
    
    log_success "Dependências Python atualizadas"
}

update_system_files() {
    log_info "Atualizando arquivos do sistema..."
    
    # Lista de arquivos para atualizar
    local files=(
        "enhanced_sentiment_analyzer.py"
        "bitcoin_trading_system_with_ollama.py"
        "sentiment_benchmark.py"
        "ollama_sentiment_analyzer.py"
        "reddit_collector.py"
        "sentiment_analyzer.py"
    )
    
    for file in "${files[@]}"; do
        if [[ -f "$file" ]]; then
            # Backup do arquivo atual
            if [[ -f "$INSTALL_DIR/src/$file" ]]; then
                sudo -u "$USER_NAME" cp "$INSTALL_DIR/src/$file" "$BACKUP_DIR/src/${file}.old"
            fi
            
            # Copiar novo arquivo
            sudo cp "$file" "$INSTALL_DIR/src/"
            sudo chown "$USER_NAME:$USER_NAME" "$INSTALL_DIR/src/$file"
            sudo chmod +x "$INSTALL_DIR/src/$file"
            
            log_success "Atualizado: $file"
        else
            log_warning "Arquivo não encontrado: $file"
        fi
    done
}

update_configuration() {
    log_info "Verificando configurações..."
    
    # Verificar se há novas configurações para adicionar
    local config_file="$INSTALL_DIR/config/trading_config.json"
    
    if [[ -f "$config_file" ]]; then
        # Fazer backup da configuração atual
        sudo -u "$USER_NAME" cp "$config_file" "$BACKUP_DIR/config/trading_config.json.old"
        
        # Aqui você pode adicionar lógica para mesclar novas configurações
        log_info "Configuração atual preservada"
    else
        log_warning "Arquivo de configuração não encontrado"
    fi
}

run_migration_tests() {
    log_info "Executando testes pós-atualização..."
    
    sudo -u "$USER_NAME" bash << 'EOF'
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

# Teste de importações
python3 -c "
try:
    import sys
    sys.path.append('src')
    from enhanced_sentiment_analyzer import EnhancedSentimentAnalyzer
    analyzer = EnhancedSentimentAnalyzer()
    print('✅ Módulos importados com sucesso')
except Exception as e:
    print('❌ Erro de importação:', e)
    exit(1)
"

echo "✅ Testes pós-atualização concluídos"
EOF
    
    log_success "Testes pós-atualização concluídos"
}

start_services() {
    log_info "Reiniciando serviços..."
    
    # Recarregar configuração do systemd
    sudo systemctl daemon-reload
    
    # Iniciar serviços
    if [[ -f /etc/systemd/system/bitcoin-trading-system.service ]]; then
        sudo systemctl start bitcoin-trading-system
        log_success "Serviço bitcoin-trading-system iniciado"
    fi
    
    if [[ -f /etc/systemd/system/bitcoin-trading-monitor.service ]]; then
        sudo systemctl start bitcoin-trading-monitor
        log_success "Serviço bitcoin-trading-monitor iniciado"
    fi
}

cleanup_old_backups() {
    log_info "Limpando backups antigos..."
    
    # Manter apenas os 5 backups mais recentes
    sudo -u "$USER_NAME" bash << 'EOF'
cd "$INSTALL_DIR/backup"
ls -1t | tail -n +6 | xargs -r rm -rf
EOF
    
    log_success "Backups antigos removidos"
}

print_update_summary() {
    echo ""
    echo "============================================"
    log_success "ATUALIZAÇÃO CONCLUÍDA COM SUCESSO!"
    echo "============================================"
    echo ""
    echo "📁 Backup criado em: $BACKUP_DIR"
    echo "🔄 Serviços reiniciados"
    echo "🧪 Testes pós-atualização: ✅"
    echo ""
    echo "📊 Para verificar status:"
    echo "   sudo systemctl status bitcoin-trading-system"
    echo ""
    echo "📋 Para ver logs:"
    echo "   tail -f $INSTALL_DIR/logs/trading.log"
    echo ""
    echo "🔙 Para reverter (se necessário):"
    echo "   $0 --rollback $BACKUP_DIR"
    echo ""
    log_success "Sistema atualizado e funcionando!"
}

rollback_system() {
    local backup_path="$1"
    
    if [[ ! -d "$backup_path" ]]; then
        log_error "Backup não encontrado: $backup_path"
        exit 1
    fi
    
    log_info "Revertendo sistema para backup: $backup_path"
    
    # Parar serviços
    stop_services
    
    # Restaurar arquivos
    sudo -u "$USER_NAME" cp -r "$backup_path/config/"* "$INSTALL_DIR/config/"
    sudo -u "$USER_NAME" cp -r "$backup_path/src/"* "$INSTALL_DIR/src/"
    
    # Reiniciar serviços
    start_services
    
    log_success "Sistema revertido com sucesso"
}

main() {
    echo "============================================"
    echo "🔄 Atualizador do Sistema Trading Bitcoin"
    echo "============================================"
    echo ""
    
    # Verificar se é rollback
    if [[ "${1:-}" == "--rollback" ]]; then
        if [[ -z "${2:-}" ]]; then
            log_error "Especifique o caminho do backup para rollback"
            exit 1
        fi
        rollback_system "$2"
        return
    fi
    
    # Processo normal de atualização
    check_installation
    create_backup
    stop_services
    update_ollama
    update_models
    update_python_dependencies
    update_system_files
    update_configuration
    run_migration_tests
    start_services
    cleanup_old_backups
    print_update_summary
}

# Verificar argumentos
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    echo "Uso: $0 [opções]"
    echo ""
    echo "Opções:"
    echo "  --help, -h              Mostrar esta ajuda"
    echo "  --rollback BACKUP_PATH  Reverter para backup específico"
    echo ""
    echo "Exemplos:"
    echo "  $0                      Atualizar sistema"
    echo "  $0 --rollback /opt/bitcoin-trading-system/backup/20250731_120000"
    exit 0
fi

# Executar atualização
main "$@"

