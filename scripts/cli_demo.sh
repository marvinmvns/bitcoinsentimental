#!/bin/bash

# ============================================================================
# CLI Demo - Sistema Trading Bitcoin com Ollama LLM
# ============================================================================
# Script de demonstração das funcionalidades da CLI
# ============================================================================

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m'

demo_header() {
    echo -e "${PURPLE}============================================${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}============================================${NC}"
    echo ""
}

demo_step() {
    echo -e "${CYAN}📋 $1${NC}"
    echo -e "${YELLOW}Comando: $2${NC}"
    echo ""
}

wait_for_user() {
    echo -e "${BLUE}Pressione Enter para continuar...${NC}"
    read
    echo ""
}

run_command() {
    echo -e "${GREEN}$ $1${NC}"
    eval "$1"
    echo ""
}

main() {
    clear
    
    demo_header "🚀 DEMONSTRAÇÃO DA CLI - SISTEMA TRADING BITCOIN"
    
    echo "Esta demonstração mostra as principais funcionalidades da"
    echo "interface de linha de comando do sistema de trading Bitcoin."
    echo ""
    wait_for_user
    
    # 1. Verificar status do sistema
    demo_header "1. VERIFICAÇÃO DO STATUS DO SISTEMA"
    demo_step "Verificar se todos os componentes estão funcionando" "python ../src/cli/btc_trading_cli.py system status"
    run_command "python ../src/cli/btc_trading_cli.py system status"
    wait_for_user
    
    # 2. Configuração
    demo_header "2. GERENCIAMENTO DE CONFIGURAÇÃO"
    demo_step "Visualizar configuração atual" "python ../src/cli/btc_trading_cli.py config show"
    run_command "python ../src/cli/btc_trading_cli.py config show"
    
    echo -e "${CYAN}📋 Definir um parâmetro de configuração${NC}"
    echo -e "${YELLOW}Comando: python ../src/cli/btc_trading_cli.py config set min_confidence 0.75${NC}"
    echo ""
    run_command "python ../src/cli/btc_trading_cli.py config set min_confidence 0.75"
    
    echo -e "${CYAN}📋 Verificar valor específico${NC}"
    echo -e "${YELLOW}Comando: python ../src/cli/btc_trading_cli.py config get min_confidence${NC}"
    echo ""
    run_command "python ../src/cli/btc_trading_cli.py config get min_confidence"
    wait_for_user
    
    # 3. Análise de sentimento individual
    demo_header "3. ANÁLISE DE SENTIMENTO INDIVIDUAL"
    demo_step "Analisar sentimento de um texto simples" "python ../src/cli/btc_trading_cli.py sentiment analyze 'Bitcoin is going to the moon!'"
    run_command "python ../src/cli/btc_trading_cli.py sentiment analyze 'Bitcoin is going to the moon!'"
    
    demo_step "Análise com output em JSON" "python ../src/cli/btc_trading_cli.py sentiment analyze 'Bitcoin is crashing!' --output json"
    run_command "python ../src/cli/btc_trading_cli.py sentiment analyze 'Bitcoin is crashing!' --output json"
    
    demo_step "Análise com modelo específico" "python ../src/cli/btc_trading_cli.py sentiment analyze 'Bitcoin price is stable' --model llama3.2:1b --output table"
    run_command "python ../src/cli/btc_trading_cli.py sentiment analyze 'Bitcoin price is stable' --model llama3.2:1b --output table"
    wait_for_user
    
    # 4. Análise em lote
    demo_header "4. ANÁLISE DE SENTIMENTO EM LOTE"
    
    echo -e "${CYAN}📋 Criar arquivo de teste com múltiplos textos${NC}"
    echo ""
    
    cat > /tmp/test_texts.txt << 'EOF'
Bitcoin is showing incredible bullish momentum today!
The crypto market is experiencing a major downturn.
BTC price remains stable around current levels.
HODL! Diamond hands! To the moon!
This Bitcoin dump is terrible, selling everything.
Institutional adoption of Bitcoin is accelerating.
Market sentiment is very bearish right now.
Bitcoin breaking through resistance levels.
EOF
    
    echo "Arquivo criado: /tmp/test_texts.txt"
    echo "Conteúdo:"
    cat /tmp/test_texts.txt
    echo ""
    
    demo_step "Análise em lote com output JSON" "python ../src/cli/btc_trading_cli.py sentiment batch /tmp/test_texts.txt --format json"
    run_command "python ../src/cli/btc_trading_cli.py sentiment batch /tmp/test_texts.txt --format json --output /tmp/batch_results.json"
    
    echo "Resultados salvos em: /tmp/batch_results.json"
    echo "Primeiros resultados:"
    head -20 /tmp/batch_results.json
    echo ""
    wait_for_user
    
    # 5. Backtest
    demo_header "5. BACKTEST DO SISTEMA DE TRADING"
    demo_step "Executar backtest rápido (3 dias)" "python ../src/cli/btc_trading_cli.py trading backtest --days 3 --capital 5000"
    run_command "python ../src/cli/btc_trading_cli.py trading backtest --days 3 --capital 5000"
    
    demo_step "Backtest com output para arquivo" "python ../src/cli/btc_trading_cli.py trading backtest --days 5 --capital 10000 --output /tmp/backtest_results.json"
    run_command "python ../src/cli/btc_trading_cli.py trading backtest --days 5 --capital 10000 --output /tmp/backtest_results.json"
    
    echo "Resultados do backtest:"
    cat /tmp/backtest_results.json | jq '.results'
    echo ""
    wait_for_user
    
    # 6. Benchmark de modelos
    demo_header "6. BENCHMARK DE MODELOS"
    demo_step "Comparar performance de diferentes modelos" "python ../src/cli/btc_trading_cli.py benchmark models --models llama3.2:1b"
    
    echo -e "${YELLOW}Nota: Este teste pode demorar alguns minutos...${NC}"
    echo ""
    run_command "python ../src/cli/btc_trading_cli.py benchmark models --models llama3.2:1b --output /tmp/benchmark_results.json"
    
    echo "Resultados do benchmark:"
    cat /tmp/benchmark_results.json | jq '.results'
    echo ""
    wait_for_user
    
    # 7. Monitoramento
    demo_header "7. MONITORAMENTO E LOGS"
    demo_step "Visualizar métricas do sistema" "python ../src/cli/btc_trading_cli.py system metrics"
    run_command "python ../src/cli/btc_trading_cli.py system metrics"
    
    demo_step "Visualizar logs recentes" "python ../src/cli/btc_trading_cli.py system logs --lines 10"
    run_command "python ../src/cli/btc_trading_cli.py system logs --lines 10"
    wait_for_user
    
    # 8. Funcionalidades avançadas
    demo_header "8. FUNCIONALIDADES AVANÇADAS"
    
    echo -e "${CYAN}📋 Usando aliases (se configurados)${NC}"
    echo -e "${YELLOW}btc-status    # Equivale a: python ../src/cli/btc_trading_cli.py system status${NC}"
    echo -e "${YELLOW}btc-analyze   # Equivale a: python ../src/cli/btc_trading_cli.py sentiment analyze${NC}"
    echo -e "${YELLOW}btc-config    # Equivale a: python ../src/cli/btc_trading_cli.py config show${NC}"
    echo ""
    
    echo -e "${CYAN}📋 Auto-completar (pressione Tab após digitar)${NC}"
    echo -e "${YELLOW}python ../src/cli/btc_trading_cli.py sen<TAB>     # Completa para 'sentiment'${NC}"
    echo -e "${YELLOW}python ../src/cli/btc_trading_cli.py config <TAB> # Mostra: show, set, get, reset${NC}"
    echo ""
    
    echo -e "${CYAN}📋 Ajuda contextual${NC}"
    echo -e "${YELLOW}python ../src/cli/btc_trading_cli.py --help                    # Ajuda geral${NC}"
    echo -e "${YELLOW}python ../src/cli/btc_trading_cli.py sentiment --help          # Ajuda do módulo${NC}"
    echo -e "${YELLOW}python ../src/cli/btc_trading_cli.py sentiment analyze --help  # Ajuda do comando${NC}"
    echo ""
    wait_for_user
    
    # 9. Exemplos práticos
    demo_header "9. EXEMPLOS PRÁTICOS DE USO"
    
    echo -e "${CYAN}📋 Análise rápida de notícia${NC}"
    echo -e "${YELLOW}python ../src/cli/btc_trading_cli.py sentiment analyze 'Tesla announces Bitcoin payment integration' --output table${NC}"
    echo ""
    run_command "python ../src/cli/btc_trading_cli.py sentiment analyze 'Tesla announces Bitcoin payment integration' --output table"
    
    echo -e "${CYAN}📋 Monitoramento contínuo (simulado)${NC}"
    echo -e "${YELLOW}# Em produção, você usaria:${NC}"
    echo -e "${YELLOW}# watch -n 60 'python ../src/cli/btc_trading_cli.py system status'${NC}"
    echo ""
    
    echo -e "${CYAN}📋 Pipeline de análise${NC}"
    echo -e "${YELLOW}# Coletar dados -> Analisar -> Gerar relatório${NC}"
    echo ""
    
    cat > /tmp/pipeline_demo.sh << 'EOF'
#!/bin/bash
# Pipeline de análise automatizada

echo "📊 Coletando dados de sentimento..."
echo "Bitcoin adoption is growing rapidly" > /tmp/market_data.txt
echo "Crypto market showing strong bullish signals" >> /tmp/market_data.txt
echo "Institutional investors buying Bitcoin" >> /tmp/market_data.txt

echo "🧠 Analisando sentimento..."
python ../src/cli/btc_trading_cli.py sentiment batch /tmp/market_data.txt --format json --output /tmp/analysis.json

echo "📈 Gerando relatório..."
echo "Análise de Sentimento - $(date)" > /tmp/report.txt
echo "=================================" >> /tmp/report.txt
jq -r '.[] | "\(.sentiment | ascii_upcase): \(.text) (Score: \(.score | tostring))"' /tmp/analysis.json >> /tmp/report.txt

echo "✅ Relatório gerado: /tmp/report.txt"
cat /tmp/report.txt
EOF
    
    chmod +x /tmp/pipeline_demo.sh
    run_command "/tmp/pipeline_demo.sh"
    wait_for_user
    
    # 10. Finalização
    demo_header "10. RECURSOS ADICIONAIS"
    
    echo -e "${GREEN}📚 Documentação e Ajuda:${NC}"
    echo "  • man python ../src/cli/btc_trading_cli.py              # Manual completo"
    echo "  • python ../src/cli/btc_trading_cli.py --help           # Ajuda da CLI"
    echo "  • python ../src/cli/btc_trading_cli.py <comando> --help # Ajuda específica"
    echo ""
    
    echo -e "${GREEN}🔧 Configuração Avançada:${NC}"
    echo "  • ~/.python ../src/cli/btc_trading_cli.py/config.json   # Configuração pessoal"
    echo "  • ~/.python ../src/cli/btc_trading_cli.py/logs/         # Logs do usuário"
    echo ""
    
    echo -e "${GREEN}🚀 Próximos Passos:${NC}"
    echo "  1. Configure parâmetros específicos com 'python ../src/cli/btc_trading_cli.py config set'"
    echo "  2. Execute backtests com diferentes configurações"
    echo "  3. Monitore performance com 'python ../src/cli/btc_trading_cli.py system metrics'"
    echo "  4. Use modo live para trading em tempo real (com cautela!)"
    echo ""
    
    echo -e "${GREEN}⚠️  Importante:${NC}"
    echo "  • Sempre teste em modo simulação antes do trading real"
    echo "  • Configure limites de risco apropriados"
    echo "  • Monitore logs e métricas regularmente"
    echo "  • Mantenha backups da configuração"
    echo ""
    
    demo_header "🎉 DEMONSTRAÇÃO CONCLUÍDA!"
    
    echo "A CLI do Sistema de Trading Bitcoin oferece uma interface"
    echo "poderosa e flexível para todas as operações do sistema."
    echo ""
    echo "Para começar a usar:"
    echo "  python ../src/cli/btc_trading_cli.py system status"
    echo ""
    echo "Para ajuda completa:"
    echo "  python ../src/cli/btc_trading_cli.py --help"
    echo ""
    echo -e "${GREEN}Obrigado por usar o Sistema de Trading Bitcoin! 🚀${NC}"
    echo ""
    
    # Limpeza
    echo "🧹 Limpando arquivos temporários da demonstração..."
    rm -f /tmp/test_texts.txt /tmp/batch_results.json /tmp/backtest_results.json
    rm -f /tmp/benchmark_results.json /tmp/market_data.txt /tmp/analysis.json
    rm -f /tmp/report.txt /tmp/pipeline_demo.sh
    echo "✅ Limpeza concluída"
}

# Verificar se a CLI está instalada
if ! command -v python ../src/cli/btc_trading_cli.py &> /dev/null; then
    echo -e "${RED}❌ CLI não encontrada${NC}"
    echo "Execute primeiro o script de configuração: ./setup_cli.sh"
    exit 1
fi

# Verificar argumentos
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    echo "Uso: $0"
    echo ""
    echo "Executa demonstração interativa da CLI do sistema de trading Bitcoin."
    echo ""
    echo "Pré-requisitos:"
    echo "  • CLI instalada (python ../src/cli/btc_trading_cli.py disponível no PATH)"
    echo "  • Sistema principal funcionando"
    echo "  • Ollama rodando com modelos instalados"
    exit 0
fi

# Executar demonstração
main

