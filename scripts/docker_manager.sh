#!/bin/bash

# ============================================================================
# Docker Manager - Sistema Trading Bitcoin com Ollama LLM
# ============================================================================
# Script para facilitar o gerenciamento do sistema via Docker
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
IMAGE_NAME="bitcoin-trading-system"
CONTAINER_NAME="bitcoin-trading-main"
COMPOSE_FILE="docker-compose.yml"

check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker não está instalado"
        log_info "Instale Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose não está instalado"
        log_info "Instale Docker Compose: https://docs.docker.com/compose/install/"
        exit 1
    fi
}

build_image() {
    log_info "Construindo imagem Docker..."
    
    if [[ ! -f "Dockerfile" ]]; then
        log_error "Dockerfile não encontrado"
        exit 1
    fi
    
    docker build -t "$IMAGE_NAME:latest" .
    log_success "Imagem construída: $IMAGE_NAME:latest"
}

start_system() {
    log_info "Iniciando sistema completo..."
    
    if [[ -f "$COMPOSE_FILE" ]]; then
        docker-compose up -d
        log_success "Sistema iniciado via Docker Compose"
    else
        docker run -d \
            --name "$CONTAINER_NAME" \
            -p 8080:8080 \
            -p 11434:11434 \
            -v trading_data:/opt/bitcoin-trading-system/data \
            -v trading_logs:/opt/bitcoin-trading-system/logs \
            -v trading_results:/opt/bitcoin-trading-system/results \
            "$IMAGE_NAME:latest"
        log_success "Container iniciado: $CONTAINER_NAME"
    fi
}

stop_system() {
    log_info "Parando sistema..."
    
    if [[ -f "$COMPOSE_FILE" ]]; then
        docker-compose down
        log_success "Sistema parado via Docker Compose"
    else
        docker stop "$CONTAINER_NAME" 2>/dev/null || true
        docker rm "$CONTAINER_NAME" 2>/dev/null || true
        log_success "Container parado e removido"
    fi
}

restart_system() {
    log_info "Reiniciando sistema..."
    stop_system
    start_system
}

show_status() {
    log_info "Status do sistema:"
    echo ""
    
    if [[ -f "$COMPOSE_FILE" ]]; then
        docker-compose ps
    else
        docker ps -f name="$CONTAINER_NAME"
    fi
    
    echo ""
    log_info "Uso de recursos:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
}

show_logs() {
    local service="${1:-bitcoin-trading}"
    
    log_info "Mostrando logs do serviço: $service"
    
    if [[ -f "$COMPOSE_FILE" ]]; then
        docker-compose logs -f "$service"
    else
        docker logs -f "$CONTAINER_NAME"
    fi
}

enter_container() {
    log_info "Entrando no container..."
    
    if [[ -f "$COMPOSE_FILE" ]]; then
        docker-compose exec bitcoin-trading bash
    else
        docker exec -it "$CONTAINER_NAME" bash
    fi
}

run_tests() {
    log_info "Executando testes..."
    
    if [[ -f "$COMPOSE_FILE" ]]; then
        docker-compose exec bitcoin-trading python src/test_system.py
    else
        docker exec "$CONTAINER_NAME" python src/test_system.py
    fi
}

run_demo() {
    log_info "Executando demo..."
    
    if [[ -f "$COMPOSE_FILE" ]]; then
        docker-compose exec bitcoin-trading python src/quick_demo.py
    else
        docker exec "$CONTAINER_NAME" python src/quick_demo.py
    fi
}

backup_data() {
    local backup_dir="backup_$(date +%Y%m%d_%H%M%S)"
    
    log_info "Criando backup em: $backup_dir"
    
    mkdir -p "$backup_dir"
    
    # Backup dos volumes
    docker run --rm \
        -v trading_data:/data \
        -v trading_logs:/logs \
        -v trading_results:/results \
        -v "$(pwd)/$backup_dir":/backup \
        alpine tar czf /backup/trading_data.tar.gz -C / data logs results
    
    log_success "Backup criado em: $backup_dir"
}

restore_data() {
    local backup_file="$1"
    
    if [[ -z "$backup_file" ]]; then
        log_error "Especifique o arquivo de backup"
        exit 1
    fi
    
    if [[ ! -f "$backup_file" ]]; then
        log_error "Arquivo de backup não encontrado: $backup_file"
        exit 1
    fi
    
    log_info "Restaurando backup: $backup_file"
    
    # Parar sistema
    stop_system
    
    # Restaurar dados
    docker run --rm \
        -v trading_data:/data \
        -v trading_logs:/logs \
        -v trading_results:/results \
        -v "$(pwd)":/backup \
        alpine tar xzf "/backup/$backup_file" -C /
    
    # Reiniciar sistema
    start_system
    
    log_success "Backup restaurado"
}

cleanup() {
    log_info "Limpando recursos Docker..."
    
    # Parar sistema
    stop_system
    
    # Remover imagens não utilizadas
    docker image prune -f
    
    # Remover volumes órfãos
    docker volume prune -f
    
    log_success "Limpeza concluída"
}

update_system() {
    log_info "Atualizando sistema..."
    
    # Fazer backup antes da atualização
    backup_data
    
    # Parar sistema
    stop_system
    
    # Reconstruir imagem
    build_image
    
    # Reiniciar sistema
    start_system
    
    log_success "Sistema atualizado"
}

show_help() {
    echo "Uso: $0 <comando> [opções]"
    echo ""
    echo "Comandos disponíveis:"
    echo "  build       Construir imagem Docker"
    echo "  start       Iniciar sistema"
    echo "  stop        Parar sistema"
    echo "  restart     Reiniciar sistema"
    echo "  status      Mostrar status"
    echo "  logs        Mostrar logs [serviço]"
    echo "  shell       Entrar no container"
    echo "  test        Executar testes"
    echo "  demo        Executar demo"
    echo "  backup      Criar backup dos dados"
    echo "  restore     Restaurar backup [arquivo]"
    echo "  update      Atualizar sistema"
    echo "  cleanup     Limpar recursos Docker"
    echo "  help        Mostrar esta ajuda"
    echo ""
    echo "Exemplos:"
    echo "  $0 build"
    echo "  $0 start"
    echo "  $0 logs bitcoin-trading"
    echo "  $0 restore backup_20250731_120000/trading_data.tar.gz"
}

main() {
    local command="${1:-help}"
    
    case "$command" in
        "build")
            check_docker
            build_image
            ;;
        "start")
            check_docker
            start_system
            ;;
        "stop")
            check_docker
            stop_system
            ;;
        "restart")
            check_docker
            restart_system
            ;;
        "status")
            check_docker
            show_status
            ;;
        "logs")
            check_docker
            show_logs "$2"
            ;;
        "shell"|"bash")
            check_docker
            enter_container
            ;;
        "test")
            check_docker
            run_tests
            ;;
        "demo")
            check_docker
            run_demo
            ;;
        "backup")
            check_docker
            backup_data
            ;;
        "restore")
            check_docker
            restore_data "$2"
            ;;
        "update")
            check_docker
            update_system
            ;;
        "cleanup")
            check_docker
            cleanup
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            log_error "Comando desconhecido: $command"
            show_help
            exit 1
            ;;
    esac
}

main "$@"

