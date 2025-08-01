#!/usr/bin/env python3
"""
Bitcoin Trading System CLI - Interface de Linha de Comando
============================================================
Autor: Manus AI
Versão: 1.0
Data: 31 de Julho de 2025

Interface unificada para gerenciar e operar o sistema de trading Bitcoin
com análise de sentimento usando Ollama LLM.
"""

import click
import json
import sys
import os
import time
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Adicionar diretório src ao path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from ..sentiment.enhanced_sentiment_analyzer import EnhancedSentimentAnalyzer
    from ..trading.bitcoin_trading_system_with_ollama import BitcoinTradingSystemWithOllama
    from ..core.sentiment_benchmark import SentimentBenchmark
    from metrics_collector import metrics_collector
except ImportError as e:
    click.echo(f"❌ Erro importando módulos: {e}", err=True)
    click.echo("Certifique-se de que está no diretório correto e que o sistema está instalado.", err=True)
    sys.exit(1)

# Configurações globais
CONFIG_DIR = Path.home() / '.btc-trading'
CONFIG_FILE = CONFIG_DIR / 'config.json'
LOG_DIR = CONFIG_DIR / 'logs'

# Criar diretórios se não existirem
CONFIG_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

class CLIConfig:
    """Gerenciador de configuração da CLI"""
    
    def __init__(self):
        self.config_file = CONFIG_FILE
        self.default_config = {
            'ollama_model': 'llama3.2:1b',
            'min_confidence': 0.6,
            'position_size': 0.1,
            'initial_capital': 10000.0,
            'log_level': 'INFO',
            'cache_enabled': True,
            'auto_update': True
        }
    
    def load(self) -> Dict:
        """Carrega configuração"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                # Mesclar com configuração padrão
                merged_config = self.default_config.copy()
                merged_config.update(config)
                return merged_config
            except Exception as e:
                click.echo(f"⚠️  Erro carregando configuração: {e}", err=True)
        
        return self.default_config.copy()
    
    def save(self, config: Dict):
        """Salva configuração"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            click.echo(f"❌ Erro salvando configuração: {e}", err=True)

# Instância global de configuração
cli_config = CLIConfig()

@click.group()
@click.version_option(version='1.0', prog_name='btc-trading')
@click.option('--config', '-c', help='Arquivo de configuração personalizado')
@click.option('--verbose', '-v', is_flag=True, help='Saída detalhada')
@click.pass_context
def cli(ctx, config, verbose):
    """
    🚀 Sistema de Trading Bitcoin com Ollama LLM
    
    Interface de linha de comando para gerenciar e operar o sistema
    de trading automatizado baseado em análise de sentimento.
    """
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['config'] = cli_config.load()
    
    if config:
        try:
            with open(config, 'r') as f:
                custom_config = json.load(f)
            ctx.obj['config'].update(custom_config)
        except Exception as e:
            click.echo(f"❌ Erro carregando configuração personalizada: {e}", err=True)
            sys.exit(1)

@cli.group()
def sentiment():
    """Comandos para análise de sentimento"""
    pass

@sentiment.command()
@click.argument('text')
@click.option('--model', '-m', help='Modelo Ollama a usar')
@click.option('--output', '-o', type=click.Choice(['json', 'table', 'simple']), default='simple')
@click.pass_context
def analyze(ctx, text, model, output):
    """Analisa sentimento de um texto"""
    config = ctx.obj['config']
    model = model or config['ollama_model']
    
    try:
        with click.progressbar(length=1, label='Analisando sentimento') as bar:
            analyzer = EnhancedSentimentAnalyzer(ollama_model=model)
            result = analyzer.analyze_sentiment(text)
            bar.update(1)
        
        if output == 'json':
            click.echo(json.dumps({
                'text': text,
                'sentiment': result.final_sentiment,
                'score': result.final_score,
                'confidence': result.final_confidence,
                'processing_time': getattr(result, 'ollama_time', 0),
                'model_used': model
            }, indent=2))
        
        elif output == 'table':
            click.echo("\n📊 Resultado da Análise de Sentimento")
            click.echo("=" * 50)
            click.echo(f"Texto: {text}")
            click.echo(f"Sentimento: {result.final_sentiment.upper()}")
            click.echo(f"Score: {result.final_score:.3f}")
            click.echo(f"Confiança: {result.final_confidence:.3f}")
            click.echo(f"Modelo: {model}")
            click.echo(f"Tempo: {getattr(result, 'ollama_time', 0):.2f}s")
        
        else:  # simple
            sentiment_emoji = {
                'positive': '😊',
                'negative': '😞',
                'neutral': '😐'
            }.get(result.final_sentiment, '❓')
            
            click.echo(f"{sentiment_emoji} {result.final_sentiment.upper()} "
                      f"(score: {result.final_score:.3f}, "
                      f"confiança: {result.final_confidence:.3f})")
    
    except Exception as e:
        click.echo(f"❌ Erro na análise: {e}", err=True)
        sys.exit(1)

@sentiment.command()
@click.argument('input_file', type=click.File('r'))
@click.option('--output', '-o', type=click.File('w'), default='-')
@click.option('--format', type=click.Choice(['json', 'csv']), default='json')
@click.option('--model', '-m', help='Modelo Ollama a usar')
@click.pass_context
def batch(ctx, input_file, output, format, model):
    """Analisa sentimento de múltiplos textos de um arquivo"""
    config = ctx.obj['config']
    model = model or config['ollama_model']
    
    try:
        # Ler textos do arquivo
        texts = [line.strip() for line in input_file if line.strip()]
        
        if not texts:
            click.echo("❌ Nenhum texto encontrado no arquivo", err=True)
            sys.exit(1)
        
        click.echo(f"📝 Analisando {len(texts)} textos...")
        
        analyzer = EnhancedSentimentAnalyzer(ollama_model=model)
        
        results = []
        with click.progressbar(texts, label='Processando') as bar:
            for text in bar:
                result = analyzer.analyze_sentiment(text)
                results.append({
                    'text': text,
                    'sentiment': result.final_sentiment,
                    'score': result.final_score,
                    'confidence': result.final_confidence,
                    'processing_time': getattr(result, 'ollama_time', 0)
                })
        
        # Salvar resultados
        if format == 'json':
            json.dump(results, output, indent=2, ensure_ascii=False)
        elif format == 'csv':
            import csv
            writer = csv.DictWriter(output, fieldnames=['text', 'sentiment', 'score', 'confidence', 'processing_time'])
            writer.writeheader()
            writer.writerows(results)
        
        # Estatísticas
        positive_count = sum(1 for r in results if r['sentiment'] == 'positive')
        negative_count = sum(1 for r in results if r['sentiment'] == 'negative')
        neutral_count = sum(1 for r in results if r['sentiment'] == 'neutral')
        avg_confidence = sum(r['confidence'] for r in results) / len(results)
        
        click.echo(f"\n📊 Resumo:")
        click.echo(f"  Positivos: {positive_count} ({positive_count/len(results)*100:.1f}%)")
        click.echo(f"  Negativos: {negative_count} ({negative_count/len(results)*100:.1f}%)")
        click.echo(f"  Neutros: {neutral_count} ({neutral_count/len(results)*100:.1f}%)")
        click.echo(f"  Confiança média: {avg_confidence:.3f}")
    
    except Exception as e:
        click.echo(f"❌ Erro na análise em lote: {e}", err=True)
        sys.exit(1)

@cli.group()
def trading():
    """Comandos para sistema de trading"""
    pass

@trading.command()
@click.option('--days', '-d', default=7, help='Número de dias para simular')
@click.option('--capital', '-c', default=10000.0, help='Capital inicial')
@click.option('--output', '-o', type=click.File('w'), help='Arquivo para salvar resultados')
@click.option('--model', '-m', help='Modelo Ollama a usar')
@click.pass_context
def backtest(ctx, days, capital, output, model):
    """Executa backtest do sistema de trading"""
    config = ctx.obj['config']
    model = model or config['ollama_model']
    
    try:
        click.echo(f"🧪 Iniciando backtest: {days} dias, ${capital:,.2f} capital inicial")
        
        system = BitcoinTradingSystemWithOllama(
            initial_capital=capital,
            ollama_model=model
        )
        
        with click.progressbar(length=days, label='Executando simulação') as bar:
            result = system.run_simulation(days=days, news_frequency=4)
            bar.update(days)
        
        # Exibir resultados
        click.echo(f"\n📊 Resultados do Backtest:")
        click.echo(f"  Capital inicial: ${capital:,.2f}")
        click.echo(f"  Capital final: ${result.final_capital:,.2f}")
        click.echo(f"  Retorno total: {result.total_return:.2f}%")
        click.echo(f"  Sharpe Ratio: {result.sharpe_ratio:.3f}")
        click.echo(f"  Drawdown máximo: {result.max_drawdown:.2f}%")
        click.echo(f"  Taxa de acerto: {result.win_rate:.1f}%")
        click.echo(f"  Total de trades: {result.total_trades}")
        
        # Salvar resultados se especificado
        if output:
            result_data = {
                'backtest_config': {
                    'days': days,
                    'initial_capital': capital,
                    'model': model
                },
                'results': {
                    'final_capital': result.final_capital,
                    'total_return': result.total_return,
                    'sharpe_ratio': result.sharpe_ratio,
                    'max_drawdown': result.max_drawdown,
                    'win_rate': result.win_rate,
                    'total_trades': result.total_trades
                },
                'timestamp': datetime.now().isoformat()
            }
            
            json.dump(result_data, output, indent=2)
            click.echo(f"💾 Resultados salvos em {output.name}")
    
    except Exception as e:
        click.echo(f"❌ Erro no backtest: {e}", err=True)
        sys.exit(1)

@trading.command()
@click.option('--duration', '-d', default=60, help='Duração em minutos')
@click.option('--interval', '-i', default=5, help='Intervalo entre análises (minutos)')
@click.option('--dry-run', is_flag=True, help='Modo simulação (não executa trades reais)')
@click.pass_context
def live(ctx, duration, interval, dry_run):
    """Executa sistema de trading em tempo real"""
    config = ctx.obj['config']
    
    if not dry_run:
        click.confirm('⚠️  Modo de trading real. Continuar?', abort=True)
    
    try:
        click.echo(f"🚀 Iniciando trading {'(simulação)' if dry_run else '(REAL)'}")
        click.echo(f"Duração: {duration} minutos, Intervalo: {interval} minutos")
        
        system = BitcoinTradingSystemWithOllama(
            initial_capital=config['initial_capital'],
            ollama_model=config['ollama_model']
        )
        
        start_time = time.time()
        end_time = start_time + (duration * 60)
        
        while time.time() < end_time:
            try:
                # Simular análise de mercado
                click.echo(f"\n📊 {datetime.now().strftime('%H:%M:%S')} - Analisando mercado...")
                
                # Aqui seria implementada a coleta real de dados
                # Por enquanto, usar dados simulados
                market_data = {
                    'sentiment_text': 'Bitcoin showing strong momentum today',
                    'price': 45000.0,
                    'volume': 1000000
                }
                
                # Gerar sinal de trading
                signal = system.generate_trading_signal(market_data)
                
                click.echo(f"🎯 Sinal: {signal['action']} "
                          f"(confiança: {signal['confidence']:.3f})")
                
                if not dry_run and signal['action'] != 'HOLD':
                    click.echo(f"💼 Executando trade: {signal['action']}")
                    # Aqui seria implementada a execução real do trade
                
                # Aguardar próximo intervalo
                time.sleep(interval * 60)
                
            except KeyboardInterrupt:
                click.echo("\n⏹️  Trading interrompido pelo usuário")
                break
            except Exception as e:
                click.echo(f"❌ Erro durante trading: {e}", err=True)
                time.sleep(60)  # Aguardar 1 minuto antes de tentar novamente
    
    except Exception as e:
        click.echo(f"❌ Erro iniciando trading: {e}", err=True)
        sys.exit(1)

@cli.group()
def benchmark():
    """Comandos para benchmark e testes"""
    pass

@benchmark.command()
@click.option('--models', '-m', multiple=True, help='Modelos para testar')
@click.option('--output', '-o', type=click.File('w'), help='Arquivo para salvar resultados')
@click.pass_context
def models(ctx, models, output):
    """Executa benchmark comparativo de modelos"""
    if not models:
        models = ['llama3.2:1b', 'gemma2:9b', 'deepseek-r1:7b']
    
    try:
        click.echo(f"🧪 Executando benchmark de {len(models)} modelos...")
        
        benchmark = SentimentBenchmark()
        results = {}
        
        for model in models:
            click.echo(f"\n🤖 Testando modelo: {model}")
            
            try:
                with click.progressbar(length=1, label=f'Benchmark {model}') as bar:
                    result = benchmark.run_model_benchmark(model)
                    bar.update(1)
                
                results[model] = result
                
                click.echo(f"  Acurácia: {result['accuracy']:.1f}%")
                click.echo(f"  Tempo médio: {result['avg_time']:.2f}s")
                
            except Exception as e:
                click.echo(f"  ❌ Erro testando {model}: {e}")
                results[model] = {'error': str(e)}
        
        # Exibir resumo
        click.echo(f"\n📊 Resumo do Benchmark:")
        click.echo("=" * 50)
        
        for model, result in results.items():
            if 'error' not in result:
                click.echo(f"{model:15} | {result['accuracy']:6.1f}% | {result['avg_time']:6.2f}s")
            else:
                click.echo(f"{model:15} | ERROR: {result['error']}")
        
        # Salvar resultados
        if output:
            benchmark_data = {
                'timestamp': datetime.now().isoformat(),
                'models_tested': list(models),
                'results': results
            }
            json.dump(benchmark_data, output, indent=2)
            click.echo(f"\n💾 Resultados salvos em {output.name}")
    
    except Exception as e:
        click.echo(f"❌ Erro no benchmark: {e}", err=True)
        sys.exit(1)

@cli.group()
def config():
    """Comandos para configuração"""
    pass

@config.command()
def show():
    """Exibe configuração atual"""
    config = cli_config.load()
    
    click.echo("⚙️  Configuração Atual:")
    click.echo("=" * 30)
    
    for key, value in config.items():
        click.echo(f"{key:20}: {value}")

@config.command()
@click.argument('key')
@click.argument('value')
def set(key, value):
    """Define valor de configuração"""
    config = cli_config.load()
    
    # Tentar converter valor para tipo apropriado
    try:
        if value.lower() in ['true', 'false']:
            value = value.lower() == 'true'
        elif value.replace('.', '').replace('-', '').isdigit():
            value = float(value) if '.' in value else int(value)
    except:
        pass  # Manter como string
    
    config[key] = value
    cli_config.save(config)
    
    click.echo(f"✅ Configuração atualizada: {key} = {value}")

@config.command()
@click.argument('key')
def get(key):
    """Obtém valor de configuração"""
    config = cli_config.load()
    
    if key in config:
        click.echo(config[key])
    else:
        click.echo(f"❌ Chave '{key}' não encontrada", err=True)
        sys.exit(1)

@config.command()
def reset():
    """Restaura configuração padrão"""
    if click.confirm('⚠️  Restaurar configuração padrão?'):
        cli_config.save(cli_config.default_config)
        click.echo("✅ Configuração restaurada")

@cli.group()
def system():
    """Comandos para gerenciamento do sistema"""
    pass

@system.command()
def status():
    """Verifica status do sistema"""
    click.echo("🔍 Verificando status do sistema...")
    
    # Verificar Ollama
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            click.echo(f"✅ Ollama: Online ({len(models)} modelos)")
        else:
            click.echo(f"❌ Ollama: Erro HTTP {response.status_code}")
    except Exception as e:
        click.echo(f"❌ Ollama: Offline ({e})")
    
    # Verificar dependências Python
    try:
        import langchain
        import numpy
        import pandas
        click.echo("✅ Dependências Python: OK")
    except ImportError as e:
        click.echo(f"❌ Dependências Python: {e}")
    
    # Verificar configuração
    config = cli_config.load()
    click.echo(f"✅ Configuração: {len(config)} parâmetros carregados")
    
    # Verificar logs
    if LOG_DIR.exists():
        log_files = list(LOG_DIR.glob('*.log'))
        click.echo(f"📝 Logs: {len(log_files)} arquivos em {LOG_DIR}")
    else:
        click.echo("📝 Logs: Diretório não encontrado")

@system.command()
@click.option('--lines', '-n', default=50, help='Número de linhas')
@click.option('--follow', '-f', is_flag=True, help='Acompanhar logs em tempo real')
def logs(lines, follow):
    """Exibe logs do sistema"""
    log_file = LOG_DIR / 'trading.log'
    
    if not log_file.exists():
        click.echo("❌ Arquivo de log não encontrado", err=True)
        sys.exit(1)
    
    try:
        if follow:
            click.echo("📝 Acompanhando logs (Ctrl+C para sair)...")
            import subprocess
            subprocess.run(['tail', '-f', str(log_file)])
        else:
            with open(log_file, 'r') as f:
                lines_list = f.readlines()
                for line in lines_list[-lines:]:
                    click.echo(line.rstrip())
    
    except Exception as e:
        click.echo(f"❌ Erro lendo logs: {e}", err=True)
        sys.exit(1)

@system.command()
def metrics():
    """Exibe métricas do sistema"""
    try:
        # Obter métricas recentes
        recent_metrics = metrics_collector.get_recent_alerts(hours=24)
        
        click.echo("📊 Métricas do Sistema (últimas 24h):")
        click.echo("=" * 40)
        
        if recent_metrics:
            for metric in recent_metrics[:10]:  # Mostrar últimas 10
                timestamp = datetime.fromisoformat(metric['timestamp']).strftime('%H:%M:%S')
                click.echo(f"{timestamp} | {metric['severity']:8} | {metric['message']}")
        else:
            click.echo("Nenhuma métrica disponível")
    
    except Exception as e:
        click.echo(f"❌ Erro obtendo métricas: {e}", err=True)

@cli.command()
def version():
    """Exibe informações de versão"""
    click.echo("🚀 Sistema de Trading Bitcoin com Ollama LLM")
    click.echo("Versão: 1.0")
    click.echo("Autor: Manus AI")
    click.echo("Data: 31 de Julho de 2025")

if __name__ == '__main__':
    cli()

