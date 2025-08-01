#!/bin/bash

# ============================================================================
# Setup CLI - Sistema Trading Bitcoin com Ollama LLM
# ============================================================================
# Script para configurar a interface de linha de comando
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
CLI_SCRIPT="btc_trading_cli.py"
BIN_DIR="/usr/local/bin"
COMPLETION_DIR="/etc/bash_completion.d"

install_cli_dependencies() {
    log_info "Instalando dependências da CLI..."
    
    # Ativar ambiente virtual
    cd "$INSTALL_DIR"
    source venv/bin/activate
    
    # Instalar click para CLI
    pip install click==8.1.6
    pip install rich==13.5.2  # Para output colorido
    pip install tabulate==0.9.0  # Para tabelas
    
    log_success "Dependências da CLI instaladas"
}

create_cli_executable() {
    log_info "Criando executável da CLI..."
    
    # Copiar script CLI para diretório do sistema
    cp "$CLI_SCRIPT" "$INSTALL_DIR/src/"
    chmod +x "$INSTALL_DIR/src/$CLI_SCRIPT"
    
    # Criar link simbólico no PATH
    sudo ln -sf "$INSTALL_DIR/src/$CLI_SCRIPT" "$BIN_DIR/btc-trading"
    
    log_success "CLI instalada como 'btc-trading'"
}

create_bash_completion() {
    log_info "Configurando auto-completar bash..."
    
    # Criar script de auto-completar
    sudo tee "$COMPLETION_DIR/btc-trading" > /dev/null << 'EOF'
# Bash completion for btc-trading CLI

_btc_trading_completion() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    # Comandos principais
    if [[ ${COMP_CWORD} == 1 ]]; then
        opts="sentiment trading benchmark config system version --help --version"
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi
    
    # Subcomandos
    case "${COMP_WORDS[1]}" in
        sentiment)
            if [[ ${COMP_CWORD} == 2 ]]; then
                opts="analyze batch"
                COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
            fi
            ;;
        trading)
            if [[ ${COMP_CWORD} == 2 ]]; then
                opts="backtest live"
                COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
            fi
            ;;
        benchmark)
            if [[ ${COMP_CWORD} == 2 ]]; then
                opts="models"
                COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
            fi
            ;;
        config)
            if [[ ${COMP_CWORD} == 2 ]]; then
                opts="show set get reset"
                COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
            fi
            ;;
        system)
            if [[ ${COMP_CWORD} == 2 ]]; then
                opts="status logs metrics"
                COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
            fi
            ;;
    esac
    
    # Opções comuns
    case "${prev}" in
        --model|-m)
            opts="llama3.2:1b gemma2:9b deepseek-r1:7b"
            COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
            ;;
        --output|-o)
            COMPREPLY=( $(compgen -f -- ${cur}) )
            ;;
        --format)
            opts="json csv table simple"
            COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
            ;;
    esac
}

complete -F _btc_trading_completion btc-trading
EOF
    
    log_success "Auto-completar configurado"
}

create_shell_aliases() {
    log_info "Criando aliases úteis..."
    
    # Criar arquivo de aliases
    cat > "$INSTALL_DIR/shell_aliases.sh" << 'EOF'
#!/bin/bash
# Aliases úteis para o sistema de trading Bitcoin

# Aliases principais
alias btc='btc-trading'
alias btc-status='btc-trading system status'
alias btc-logs='btc-trading system logs'
alias btc-config='btc-trading config show'

# Aliases para análise de sentimento
alias btc-analyze='btc-trading sentiment analyze'
alias btc-batch='btc-trading sentiment batch'

# Aliases para trading
alias btc-backtest='btc-trading trading backtest'
alias btc-live='btc-trading trading live --dry-run'

# Aliases para benchmark
alias btc-benchmark='btc-trading benchmark models'

# Funções úteis
btc-quick-test() {
    echo "🧪 Teste rápido do sistema..."
    btc-trading sentiment analyze "Bitcoin is going to the moon!"
}

btc-monitor() {
    echo "📊 Monitorando sistema..."
    watch -n 30 'btc-trading system status && echo && btc-trading system metrics | head -10'
}

btc-help() {
    echo "🚀 Sistema de Trading Bitcoin - Comandos Úteis"
    echo "=============================================="
    echo "btc-status      - Status do sistema"
    echo "btc-logs        - Ver logs"
    echo "btc-config      - Ver configuração"
    echo "btc-analyze     - Analisar sentimento"
    echo "btc-backtest    - Executar backtest"
    echo "btc-benchmark   - Benchmark de modelos"
    echo "btc-quick-test  - Teste rápido"
    echo "btc-monitor     - Monitorar sistema"
    echo ""
    echo "Para ajuda completa: btc-trading --help"
}

# Exportar funções
export -f btc-quick-test btc-monitor btc-help
EOF
    
    # Adicionar ao bashrc se não existir
    if ! grep -q "bitcoin-trading-system/shell_aliases.sh" ~/.bashrc; then
        echo "" >> ~/.bashrc
        echo "# Bitcoin Trading System aliases" >> ~/.bashrc
        echo "source $INSTALL_DIR/shell_aliases.sh" >> ~/.bashrc
        log_info "Aliases adicionados ao ~/.bashrc"
    fi
    
    log_success "Aliases criados"
}

create_desktop_entry() {
    log_info "Criando entrada no menu de aplicações..."
    
    # Criar arquivo .desktop
    sudo tee "/usr/share/applications/btc-trading.desktop" > /dev/null << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Bitcoin Trading System
Comment=Sistema de Trading Bitcoin com Ollama LLM
Exec=gnome-terminal -- btc-trading system status
Icon=applications-office
Terminal=true
Categories=Office;Finance;
Keywords=bitcoin;trading;cryptocurrency;ai;sentiment;
EOF
    
    log_success "Entrada no menu criada"
}

create_man_page() {
    log_info "Criando página de manual..."
    
    # Criar diretório man se não existir
    sudo mkdir -p /usr/local/share/man/man1
    
    # Criar página de manual
    sudo tee "/usr/local/share/man/man1/btc-trading.1" > /dev/null << 'EOF'
.TH BTC-TRADING 1 "July 2025" "1.0" "Bitcoin Trading System"
.SH NAME
btc-trading \- Sistema de Trading Bitcoin com Ollama LLM
.SH SYNOPSIS
.B btc-trading
[\fIOPTIONS\fR] \fICOMMAND\fR [\fIARGS\fR]
.SH DESCRIPTION
Sistema de trading automatizado para Bitcoin baseado em análise de sentimento usando Large Language Models (LLM) locais via Ollama.
.SH COMMANDS
.TP
.B sentiment analyze \fITEXT\fR
Analisa o sentimento de um texto
.TP
.B sentiment batch \fIFILE\fR
Analisa sentimento de múltiplos textos de um arquivo
.TP
.B trading backtest
Executa backtest do sistema de trading
.TP
.B trading live
Executa sistema de trading em tempo real
.TP
.B benchmark models
Executa benchmark comparativo de modelos
.TP
.B config show
Exibe configuração atual
.TP
.B config set \fIKEY\fR \fIVALUE\fR
Define valor de configuração
.TP
.B system status
Verifica status do sistema
.TP
.B system logs
Exibe logs do sistema
.SH OPTIONS
.TP
.B \-h, \-\-help
Mostra ajuda
.TP
.B \-v, \-\-verbose
Saída detalhada
.TP
.B \-c, \-\-config \fIFILE\fR
Arquivo de configuração personalizado
.SH EXAMPLES
.TP
Analisar sentimento de um texto:
.B btc-trading sentiment analyze "Bitcoin is going up!"
.TP
Executar backtest de 30 dias:
.B btc-trading trading backtest --days 30 --capital 10000
.TP
Verificar status do sistema:
.B btc-trading system status
.SH FILES
.TP
.I ~/.btc-trading/config.json
Arquivo de configuração do usuário
.TP
.I ~/.btc-trading/logs/
Diretório de logs
.SH AUTHOR
Manus AI
.SH SEE ALSO
.BR ollama (1)
EOF
    
    # Atualizar banco de dados do man
    sudo mandb > /dev/null 2>&1 || true
    
    log_success "Página de manual criada"
}

test_cli_installation() {
    log_info "Testando instalação da CLI..."
    
    # Testar comando básico
    if btc-trading --version > /dev/null 2>&1; then
        log_success "CLI funcionando corretamente"
    else
        log_error "CLI não está funcionando"
        return 1
    fi
    
    # Testar auto-completar
    if [[ -f "$COMPLETION_DIR/btc-trading" ]]; then
        log_success "Auto-completar instalado"
    else
        log_warning "Auto-completar não encontrado"
    fi
    
    # Testar aliases
    if [[ -f "$INSTALL_DIR/shell_aliases.sh" ]]; then
        log_success "Aliases criados"
    else
        log_warning "Aliases não encontrados"
    fi
}

main() {
    echo "============================================"
    echo "🚀 Configuração da CLI - Trading Bitcoin"
    echo "============================================"
    echo ""
    
    # Verificar se está sendo executado como root para algumas operações
    if [[ $EUID -eq 0 ]]; then
        log_error "Não execute este script como root"
        log_info "Execute como usuário normal com privilégios sudo"
        exit 1
    fi
    
    # Verificar se o sistema principal está instalado
    if [[ ! -d "$INSTALL_DIR" ]]; then
        log_error "Sistema principal não encontrado em $INSTALL_DIR"
        log_info "Execute primeiro o script de instalação principal"
        exit 1
    fi
    
    # Verificar se o script CLI existe
    if [[ ! -f "$CLI_SCRIPT" ]]; then
        log_error "Script CLI não encontrado: $CLI_SCRIPT"
        log_info "Certifique-se de que está no diretório correto"
        exit 1
    fi
    
    # Executar configuração
    install_cli_dependencies
    create_cli_executable
    create_bash_completion
    create_shell_aliases
    create_desktop_entry
    create_man_page
    test_cli_installation
    
    echo ""
    echo "============================================"
    log_success "CONFIGURAÇÃO DA CLI CONCLUÍDA!"
    echo "============================================"
    echo ""
    echo "🎯 A CLI foi instalada como 'btc-trading'"
    echo ""
    echo "📚 Comandos úteis:"
    echo "   btc-trading --help          # Ajuda completa"
    echo "   btc-trading system status   # Status do sistema"
    echo "   btc-trading sentiment analyze 'texto'  # Análise rápida"
    echo "   man btc-trading             # Manual completo"
    echo ""
    echo "🔧 Para ativar aliases e auto-completar:"
    echo "   source ~/.bashrc"
    echo "   # ou reinicie o terminal"
    echo ""
    echo "🚀 Teste rápido:"
    echo "   btc-trading version"
    echo ""
    log_success "CLI pronta para uso!"
}

# Verificar argumentos
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    echo "Uso: $0"
    echo ""
    echo "Configura a interface de linha de comando do sistema de trading Bitcoin."
    echo ""
    echo "Pré-requisitos:"
    echo "  - Sistema principal instalado em $INSTALL_DIR"
    echo "  - Script CLI ($CLI_SCRIPT) no diretório atual"
    echo "  - Privilégios sudo para instalação"
    exit 0
fi

# Executar configuração
main

