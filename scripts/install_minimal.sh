#!/bin/bash

# ============================================================================
# Script de Instalação Mínima - Sistema Trading Bitcoin com Ollama LLM
# ============================================================================
# Autor: Manus AI
# Versão: 1.0
# Data: 31 de Julho de 2025
#
# Este script instala apenas os componentes essenciais para desenvolvimento
# e teste do sistema, sem configurações de produção.
# ============================================================================

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configurações
INSTALL_DIR="$HOME/bitcoin-trading-dev"
PYTHON_VERSION="3.11"

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

check_python() {
    if ! command -v python${PYTHON_VERSION} &> /dev/null; then
        log_error "Python ${PYTHON_VERSION} não encontrado"
        log_info "Instale com: sudo apt install python${PYTHON_VERSION} python${PYTHON_VERSION}-venv"
        exit 1
    fi
}

install_ollama() {
    log_info "Verificando Ollama..."
    
    if command -v ollama &> /dev/null; then
        log_success "Ollama já instalado"
    else
        log_info "Instalando Ollama..."
        curl -fsSL https://ollama.com/install.sh | sh
    fi
    
    # Verificar se está rodando
    if ! pgrep -x "ollama" > /dev/null; then
        log_info "Iniciando Ollama..."
        ollama serve &
        sleep 5
    fi
    
    # Baixar modelo principal
    log_info "Baixando modelo Llama 3.2 1B..."
    ollama pull llama3.2:1b
}

setup_environment() {
    log_info "Configurando ambiente de desenvolvimento..."
    
    # Criar diretório
    mkdir -p "$INSTALL_DIR"/{src,data,logs,config,results}
    cd "$INSTALL_DIR"
    
    # Criar ambiente virtual
    python${PYTHON_VERSION} -m venv venv
    source venv/bin/activate
    
    # Instalar dependências essenciais
    pip install --upgrade pip
    pip install \
        langchain==0.3.27 \
        langchain-community==0.3.27 \
        langchain-core==0.3.72 \
        requests==2.31.0 \
        numpy==1.24.3 \
        pandas==2.0.3 \
        matplotlib==3.7.2 \
        vaderSentiment==3.3.2 \
        textblob==0.17.1 \
        tenacity==8.2.3
    
    log_success "Ambiente configurado em $INSTALL_DIR"
}

create_test_script() {
    log_info "Criando script de teste..."
    
    cat > "$INSTALL_DIR/test_installation.py" << 'EOF'
#!/usr/bin/env python3
"""
Teste rápido da instalação mínima
"""

import requests
import time

def test_ollama():
    """Testa conectividade com Ollama"""
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✅ Ollama OK - {len(models)} modelos disponíveis")
            for model in models:
                print(f"  - {model['name']}")
            return True
        else:
            print(f"❌ Ollama erro: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ollama erro: {e}")
        return False

def test_sentiment():
    """Testa análise de sentimento básica"""
    try:
        # Teste simples com API direta do Ollama
        payload = {
            "model": "llama3.2:1b",
            "prompt": "Analyze sentiment: 'Bitcoin is going to the moon!' Return: positive, negative, or neutral",
            "stream": False,
            "options": {"temperature": 0.1, "num_predict": 10}
        }
        
        response = requests.post(
            'http://localhost:11434/api/generate',
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            sentiment = result.get('response', '').strip().lower()
            print(f"✅ Análise de sentimento OK: {sentiment}")
            return True
        else:
            print(f"❌ Erro na análise: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro na análise: {e}")
        return False

def main():
    print("🧪 Testando instalação mínima...")
    print("=" * 40)
    
    tests_passed = 0
    total_tests = 2
    
    if test_ollama():
        tests_passed += 1
    
    if test_sentiment():
        tests_passed += 1
    
    print("=" * 40)
    print(f"📊 Resultados: {tests_passed}/{total_tests} testes passaram")
    
    if tests_passed == total_tests:
        print("🎉 Instalação mínima funcionando!")
    else:
        print("⚠️  Alguns testes falharam")

if __name__ == "__main__":
    main()
EOF

    chmod +x "$INSTALL_DIR/test_installation.py"
}

create_quick_demo() {
    log_info "Criando demo rápido..."
    
    cat > "$INSTALL_DIR/quick_demo.py" << 'EOF'
#!/usr/bin/env python3
"""
Demo rápido do sistema de análise de sentimento
"""

import requests
import time
import json

def analyze_sentiment(text, model="llama3.2:1b"):
    """Analisa sentimento usando Ollama"""
    prompt = f"""
Analyze the sentiment of this Bitcoin text: "{text}"

Return your analysis in this format:
Sentiment: [positive/negative/neutral]
Confidence: [0.0-1.0]
Reasoning: [brief explanation]
"""
    
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 100
        }
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            'http://localhost:11434/api/generate',
            json=payload,
            timeout=30
        )
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            return {
                'success': True,
                'response': result.get('response', ''),
                'processing_time': processing_time
            }
        else:
            return {
                'success': False,
                'error': f'HTTP {response.status_code}'
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def main():
    print("🚀 Demo - Análise de Sentimento Bitcoin")
    print("=" * 50)
    
    test_texts = [
        "Bitcoin is going to the moon! Best investment ever!",
        "Bitcoin is crashing! Worst investment ever!",
        "Bitcoin price is stable today, no major movements.",
        "HODL! Diamond hands! Bitcoin will reach $100k!",
        "This Bitcoin dump is terrible, selling everything."
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n🔍 Teste {i}: {text}")
        print("-" * 50)
        
        result = analyze_sentiment(text)
        
        if result['success']:
            print(f"📊 Resultado:")
            print(result['response'])
            print(f"⏱️  Tempo: {result['processing_time']:.2f}s")
        else:
            print(f"❌ Erro: {result['error']}")
    
    print("\n🎉 Demo concluído!")

if __name__ == "__main__":
    main()
EOF

    chmod +x "$INSTALL_DIR/quick_demo.py"
}

main() {
    echo "============================================"
    echo "🚀 Instalação Mínima - Trading Bitcoin"
    echo "============================================"
    echo ""
    
    check_python
    install_ollama
    setup_environment
    create_test_script
    create_quick_demo
    
    echo ""
    echo "============================================"
    log_success "INSTALAÇÃO MÍNIMA CONCLUÍDA!"
    echo "============================================"
    echo ""
    echo "📁 Diretório: $INSTALL_DIR"
    echo "🐍 Ambiente: $INSTALL_DIR/venv"
    echo ""
    echo "🧪 Para testar:"
    echo "   cd $INSTALL_DIR"
    echo "   source venv/bin/activate"
    echo "   python test_installation.py"
    echo ""
    echo "🎮 Para demo:"
    echo "   python quick_demo.py"
    echo ""
    log_success "Sistema pronto para desenvolvimento!"
}

main

