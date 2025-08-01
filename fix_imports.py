#!/usr/bin/env python3
"""
Script para corrigir todos os imports após reorganização da estrutura de diretórios
"""

import os
import re
from pathlib import Path

def fix_imports():
    """Corrige todos os imports no projeto"""
    
    project_root = Path(__file__).parent
    
    # Mapeamento de correções de imports
    import_fixes = {
        # Correções para arquivos em src/sentiment/
        'src/sentiment/enhanced_sentiment_analyzer.py': [
            ('from sentiment_analyzer import', 'from .sentiment_analyzer import'),
        ],
        
        # Correções para arquivos em src/trading/
        'src/trading/bitcoin_trading_algorithm.py': [
            ('from sentiment_analyzer import', 'from ..sentiment.sentiment_analyzer import'),
            ('from reddit_collector import', 'from ..data.reddit_collector import'),
        ],
        
        'src/trading/bitcoin_trading_system_with_ollama.py': [
            ('from enhanced_sentiment_analyzer import', 'from ..sentiment.enhanced_sentiment_analyzer import'),
        ],
        
        # Correções para arquivos em src/core/
        'src/core/sentiment_benchmark.py': [
            ('from enhanced_sentiment_analyzer import', 'from ..sentiment.enhanced_sentiment_analyzer import'),
            ('from test_ollama_simple import', 'from .test_ollama_simple import'),
        ],
        
        # Correções para arquivos em src/cli/
        'src/cli/btc_trading_cli.py': [
            ('sys.path.append(str(Path(__file__).parent / \'src\'))', 'sys.path.append(str(Path(__file__).parent.parent))'),
            ('from enhanced_sentiment_analyzer import', 'from ..sentiment.enhanced_sentiment_analyzer import'),
            ('from bitcoin_trading_system_with_ollama import', 'from ..trading.bitcoin_trading_system_with_ollama import'),
            ('from sentiment_benchmark import', 'from ..core.sentiment_benchmark import'),
        ],
        
        # Correções para examples/
        'examples/main_demo.py': [
            ('from sentiment_analyzer import', 'from src.sentiment.sentiment_analyzer import'),
            ('from reddit_collector import', 'from src.data.reddit_collector import'),
            ('from bitcoin_trading_algorithm import', 'from src.trading.bitcoin_trading_algorithm import'),
        ],
    }
    
    print("🔧 Corrigindo imports...")
    
    for file_path, fixes in import_fixes.items():
        full_path = project_root / file_path
        
        if not full_path.exists():
            print(f"⚠️  Arquivo não encontrado: {file_path}")
            continue
            
        try:
            # Ler arquivo
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Aplicar correções
            modified = False
            for old_import, new_import in fixes:
                if old_import in content:
                    content = content.replace(old_import, new_import)
                    modified = True
                    print(f"✅ Corrigido em {file_path}: {old_import} -> {new_import}")
            
            # Salvar se modificado
            if modified:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
        except Exception as e:
            print(f"❌ Erro ao processar {file_path}: {e}")
    
    # Adicionar __init__.py com imports corretos se necessário
    init_files = {
        'src/sentiment/__init__.py': [
            'from .sentiment_analyzer import create_sentiment_analyzer, SentimentAnalyzer, SentimentResult',
            'from .enhanced_sentiment_analyzer import EnhancedSentimentAnalyzer, EnhancedSentimentResult',
            'from .ollama_sentiment_analyzer import OllamaSentimentAnalyzer',
        ],
        'src/trading/__init__.py': [
            'from .bitcoin_trading_algorithm import BitcoinTradingAlgorithm',
            'from .bitcoin_trading_system_with_ollama import BitcoinTradingSystemWithOllama',
        ],
        'src/data/__init__.py': [
            'from .reddit_collector import BitcoinSentimentCollector',
        ],
        'src/cli/__init__.py': [
            '# CLI module',
        ],
        'src/core/__init__.py': [
            '# Core testing and benchmarking',
        ],
        'src/utils/__init__.py': [
            '# Utilities',
        ],
    }
    
    print("\n📝 Atualizando arquivos __init__.py...")
    
    for init_path, imports in init_files.items():
        full_path = project_root / init_path
        
        try:
            content = '"""Module exports"""\n\n' + '\n'.join(imports) + '\n'
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            print(f"✅ Atualizado: {init_path}")
            
        except Exception as e:
            print(f"❌ Erro ao criar {init_path}: {e}")

def fix_scripts():
    """Corrige paths nos scripts de instalação"""
    
    project_root = Path(__file__).parent
    
    script_fixes = {
        'scripts/cli_demo.sh': [
            ('python ', 'python ../'),
            ('btc-trading', 'python ../src/cli/btc_trading_cli.py'),
        ],
        'docker/Dockerfile': [
            ('COPY --chown=bitcoin-trader:bitcoin-trader src/ src/', 'COPY --chown=bitcoin-trader:bitcoin-trader src/ /opt/bitcoin-trading-system/src/'),
            ('COPY --chown=bitcoin-trader:bitcoin-trader config/ config/', 'COPY --chown=bitcoin-trader:bitcoin-trader config/ /opt/bitcoin-trading-system/config/'),
        ],
    }
    
    print("\n🐳 Corrigindo scripts e Docker...")
    
    for file_path, fixes in script_fixes.items():
        full_path = project_root / file_path
        
        if not full_path.exists():
            print(f"⚠️  Arquivo não encontrado: {file_path}")
            continue
            
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            modified = False
            for old_path, new_path in fixes:
                if old_path in content:
                    content = content.replace(old_path, new_path)
                    modified = True
                    print(f"✅ Corrigido em {file_path}: {old_path} -> {new_path}")
            
            if modified:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
        except Exception as e:
            print(f"❌ Erro ao processar {file_path}: {e}")

def main():
    """Função principal"""
    print("🚀 CORREÇÃO DE IMPORTS - Sistema Trading Bitcoin")
    print("=" * 50)
    
    fix_imports()
    fix_scripts()
    
    print("\n✅ Correção de imports concluída!")
    print("\nTeste a estrutura com:")
    print("  python setup.py")
    print("  python examples/main_demo.py")
    print("  python src/cli/btc_trading_cli.py --help")

if __name__ == "__main__":
    main()