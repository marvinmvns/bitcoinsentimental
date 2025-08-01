#!/usr/bin/env python3
"""
Script Principal de Demonstração
Sistema de Análise de Sentimento para Trading de Bitcoin

Este script demonstra todas as funcionalidades do sistema desenvolvido,
incluindo coleta de dados, análise de sentimento, análise técnica e
geração de sinais de trading.

Autor: Manus AI
Data: 31 de Julho de 2025
"""

import json
import pandas as pd
from datetime import datetime
import logging

# Importa módulos do sistema
from src.sentiment.sentiment_analyzer import create_sentiment_analyzer, SentimentAggregator
from src.data.reddit_collector import BitcoinSentimentCollector
from src.trading.bitcoin_trading_algorithm import BitcoinTradingAlgorithm

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_header(title: str):
    """Imprime cabeçalho formatado"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def print_section(title: str):
    """Imprime seção formatada"""
    print(f"\n--- {title} ---")

def demonstrate_sentiment_analysis():
    """Demonstra análise de sentimento individual"""
    print_header("DEMONSTRAÇÃO: ANÁLISE DE SENTIMENTO")
    
    # Textos de exemplo relacionados a Bitcoin
    test_texts = [
        "Bitcoin is going to the moon! 🚀 Best investment ever! HODL!",
        "BTC is crashing hard, time to sell everything before it gets worse",
        "Bitcoin price is stable today, waiting for next move. Sideways action.",
        "HODL Bitcoin, diamond hands! 💎🙌 Never selling my precious sats",
        "Bitcoin bubble is about to burst, be very careful with your investments",
        "Just bought the dip! Bitcoin at discount prices, loading up more BTC",
        "Regulatory concerns are affecting Bitcoin price negatively",
        "Bitcoin adoption by major corporations is bullish for long term",
        "Technical analysis shows Bitcoin forming ascending triangle pattern",
        "Fear and greed index shows extreme fear, might be good buying opportunity"
    ]
    
    print(f"Analisando {len(test_texts)} textos de exemplo...")
    
    # Testa diferentes analisadores
    analyzers = {
        "VADER": "vader",
        "TextBlob": "textblob", 
        "Ensemble": "ensemble"
    }
    
    results = {}
    
    for name, analyzer_type in analyzers.items():
        print_section(f"Analisador: {name}")
        
        try:
            analyzer = create_sentiment_analyzer(analyzer_type)
            analyzer_results = []
            
            for i, text in enumerate(test_texts, 1):
                result = analyzer.analyze(text)
                analyzer_results.append(result)
                
                print(f"{i:2d}. Texto: {text[:50]}...")
                print(f"    Sentimento: {result.sentiment:>8} | Score: {result.score:>6.3f} | Confiança: {result.confidence:.3f}")
            
            # Calcula estatísticas
            positive_count = sum(1 for r in analyzer_results if r.sentiment == 'positive')
            negative_count = sum(1 for r in analyzer_results if r.sentiment == 'negative')
            neutral_count = sum(1 for r in analyzer_results if r.sentiment == 'neutral')
            avg_score = sum(r.score for r in analyzer_results) / len(analyzer_results)
            
            print(f"\n    Resumo: {positive_count} positivos, {negative_count} negativos, {neutral_count} neutros")
            print(f"    Score médio: {avg_score:.3f}")
            
            results[name] = analyzer_results
            
        except Exception as e:
            print(f"    Erro: {e}")
    
    # Calcula weighted sentiment score
    if "Ensemble" in results:
        print_section("Weighted Sentiment Score")
        weighted_score = SentimentAggregator.calculate_weighted_sentiment(results["Ensemble"])
        
        print(f"Score Positivo: {weighted_score.positive_score:.3f}")
        print(f"Score Negativo: {weighted_score.negative_score:.3f}")
        print(f"Score Ponderado Final: {weighted_score.weighted_score:.3f}")
        print(f"Total de textos: {weighted_score.total_texts}")
        
        # Interpretação
        if weighted_score.weighted_score > 2.0:
            interpretation = "Muito Positivo"
        elif weighted_score.weighted_score > 0.5:
            interpretation = "Positivo"
        elif weighted_score.weighted_score > -0.5:
            interpretation = "Neutro"
        elif weighted_score.weighted_score > -2.0:
            interpretation = "Negativo"
        else:
            interpretation = "Muito Negativo"
        
        print(f"Interpretação: {interpretation}")

def demonstrate_reddit_collection():
    """Demonstra coleta de dados do Reddit"""
    print_header("DEMONSTRAÇÃO: COLETA DE DADOS DO REDDIT")
    
    collector = BitcoinSentimentCollector()
    
    print("Coletando dados recentes do Reddit...")
    posts, df = collector.collect_recent_sentiment_data(
        hours_back=24,
        min_score=5,
        max_posts_per_subreddit=15
    )
    
    if posts:
        print(f"\n✅ Coletados {len(posts)} posts relevantes")
        
        print_section("Estatísticas dos Posts")
        print(f"Score médio: {df['score'].mean():.1f}")
        print(f"Comentários médios: {df['num_comments'].mean():.1f}")
        print(f"Subreddits únicos: {df['subreddit'].nunique()}")
        
        print(f"\nDistribuição por subreddit:")
        for subreddit, count in df['subreddit'].value_counts().head().items():
            print(f"  r/{subreddit}: {count} posts")
        
        print_section("Exemplos de Posts Coletados")
        for i, post in enumerate(posts[:3], 1):
            print(f"{i}. [{post.subreddit}] {post.title}")
            print(f"   Score: {post.score} | Comentários: {post.num_comments}")
            print(f"   Texto: {post.selftext[:100]}{'...' if len(post.selftext) > 100 else ''}")
            print()
        
        # Tópicos em alta
        trending = collector.get_trending_topics(posts, top_n=5)
        print_section("Tópicos em Alta")
        for word, count in trending:
            print(f"  {word}: {count} menções")
        
        return posts, df
    else:
        print("❌ Nenhum post coletado")
        return [], pd.DataFrame()

def demonstrate_full_trading_analysis():
    """Demonstra análise completa de trading"""
    print_header("DEMONSTRAÇÃO: ANÁLISE COMPLETA DE TRADING")
    
    # Inicializa algoritmo
    algorithm = BitcoinTradingAlgorithm(
        sentiment_weight=0.4,
        technical_weight=0.6,
        min_confidence=0.6
    )
    
    print("Configuração do algoritmo:")
    print(f"  Peso do sentimento: {algorithm.sentiment_weight:.1%}")
    print(f"  Peso da análise técnica: {algorithm.technical_weight:.1%}")
    print(f"  Confiança mínima: {algorithm.min_confidence:.1%}")
    
    print_section("Executando Análise Atual")
    
    # Executa análise completa
    signal = algorithm.run_analysis(hours_back=24)
    
    print_section("RESULTADO DA ANÁLISE")
    
    # Determina emoji baseado no sinal
    signal_emojis = {
        "STRONG_BUY": "🚀",
        "BUY": "📈", 
        "HOLD": "⏸️",
        "SELL": "📉",
        "STRONG_SELL": "💥"
    }
    
    emoji = signal_emojis.get(signal.signal.value, "❓")
    
    print(f"\n{emoji} SINAL: {signal.signal.value}")
    print(f"💪 Confiança: {signal.confidence:.1%}")
    print(f"💰 Preço Atual: ${signal.price:.2f}")
    print(f"📊 Score Sentimento: {signal.sentiment_score:+.3f}")
    print(f"📈 Score Técnico: {signal.technical_score:+.3f}")
    print(f"⚖️ Score Combinado: {signal.combined_score:+.3f}")
    
    print_section("Raciocínio da Decisão")
    for i, reason in enumerate(signal.reasoning, 1):
        print(f"{i:2d}. {reason}")
    
    # Interpretação do sinal
    print_section("Interpretação")
    
    if signal.signal.value in ["STRONG_BUY", "BUY"]:
        print("🟢 RECOMENDAÇÃO: Considere COMPRAR Bitcoin")
        if signal.confidence > 0.8:
            print("   Alta confiança - sinal forte")
        else:
            print("   Confiança moderada - considere posição menor")
    elif signal.signal.value in ["STRONG_SELL", "SELL"]:
        print("🔴 RECOMENDAÇÃO: Considere VENDER Bitcoin")
        if signal.confidence > 0.8:
            print("   Alta confiança - sinal forte")
        else:
            print("   Confiança moderada - considere venda parcial")
    else:
        print("🟡 RECOMENDAÇÃO: MANTER posição atual")
        print("   Sinais mistos ou baixa confiança")
    
    return signal

def demonstrate_backtest():
    """Demonstra backtest da estratégia"""
    print_header("DEMONSTRAÇÃO: BACKTEST DA ESTRATÉGIA")
    
    algorithm = BitcoinTradingAlgorithm()
    
    print("Executando backtest de 30 dias...")
    print("(Simulação com dados realistas de preço)")
    
    results = algorithm.backtest_strategy(days=30)
    
    print_section("RESULTADOS DO BACKTEST")
    
    print(f"💵 Valor Inicial: ${results['initial_value']:,.2f}")
    print(f"💵 Valor Final: ${results['final_value']:,.2f}")
    print(f"📊 Retorno Estratégia: {results['total_return']:+.2%}")
    print(f"📊 Retorno Buy & Hold: {results['buy_hold_return']:+.2%}")
    
    outperformance = results['outperformance']
    if outperformance > 0:
        print(f"🎯 Outperformance: +{outperformance:.2%} ✅")
        print("   A estratégia superou buy & hold!")
    else:
        print(f"🎯 Underperformance: {outperformance:.2%} ❌")
        print("   A estratégia ficou abaixo do buy & hold")
    
    print(f"🔄 Número de Trades: {results['num_trades']}")
    print(f"📡 Sinais Gerados: {results['num_signals']}")
    
    if results['num_trades'] > 0:
        print_section("Últimos Trades")
        for trade in results['trades'][-3:]:  # Últimos 3 trades
            trade_type = trade['type']
            emoji = "🟢" if trade_type == "BUY" else "🔴"
            print(f"{emoji} {trade_type}: ${trade['price']:.2f} | {trade['amount']:.4f} BTC | {trade['signal']}")
    
    return results

def save_results(signal, backtest_results, posts_data):
    """Salva todos os resultados em arquivos"""
    print_header("SALVANDO RESULTADOS")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Salva sinal atual
    signal_file = f"bitcoin_signal_{timestamp}.json"
    with open(signal_file, 'w', encoding='utf-8') as f:
        json.dump(signal.to_dict(), f, indent=2, ensure_ascii=False)
    print(f"📄 Sinal atual salvo em: {signal_file}")
    
    # Salva resultados do backtest
    backtest_file = f"backtest_results_{timestamp}.json"
    with open(backtest_file, 'w', encoding='utf-8') as f:
        json.dump(backtest_results, f, indent=2, default=str, ensure_ascii=False)
    print(f"📄 Backtest salvo em: {backtest_file}")
    
    # Salva dados dos posts se disponíveis
    if posts_data:
        posts_file = f"reddit_posts_{timestamp}.json"
        posts_dict = [
            {
                'id': post.id,
                'title': post.title,
                'selftext': post.selftext,
                'subreddit': post.subreddit,
                'score': post.score,
                'num_comments': post.num_comments,
                'created_datetime': post.created_datetime.isoformat()
            }
            for post in posts_data
        ]
        
        with open(posts_file, 'w', encoding='utf-8') as f:
            json.dump(posts_dict, f, indent=2, ensure_ascii=False)
        print(f"📄 Posts do Reddit salvos em: {posts_file}")
    
    print(f"\n✅ Todos os resultados salvos com timestamp: {timestamp}")

def main():
    """Função principal que executa todas as demonstrações"""
    
    print("🚀 SISTEMA DE ANÁLISE DE SENTIMENTO PARA TRADING DE BITCOIN")
    print("Desenvolvido por: Manus AI")
    print("Data: 31 de Julho de 2025")
    print("\nEste sistema combina análise de sentimento de redes sociais")
    print("com indicadores técnicos para gerar sinais de trading de Bitcoin.")
    
    try:
        # 1. Demonstra análise de sentimento
        demonstrate_sentiment_analysis()
        
        # 2. Demonstra coleta do Reddit
        posts, df = demonstrate_reddit_collection()
        
        # 3. Demonstra análise completa
        signal = demonstrate_full_trading_analysis()
        
        # 4. Demonstra backtest
        backtest_results = demonstrate_backtest()
        
        # 5. Salva resultados
        save_results(signal, backtest_results, posts)
        
        # Resumo final
        print_header("RESUMO FINAL")
        print("✅ Todas as demonstrações executadas com sucesso!")
        print("\nO sistema demonstrou capacidade de:")
        print("  • Analisar sentimento de textos relacionados a Bitcoin")
        print("  • Coletar dados relevantes do Reddit")
        print("  • Combinar sentimento com análise técnica")
        print("  • Gerar sinais de trading com confiança")
        print("  • Validar estratégia através de backtest")
        
        print(f"\n📊 Sinal atual: {signal.signal.value} (confiança: {signal.confidence:.1%})")
        print(f"📈 Performance backtest: {backtest_results['outperformance']:+.2%} vs buy & hold")
        
        print("\n🎯 Sistema pronto para uso em ambiente de produção!")
        print("   (Requer integração com APIs reais para dados ao vivo)")
        
    except Exception as e:
        logger.error(f"Erro durante execução: {e}")
        print(f"\n❌ Erro durante execução: {e}")
        print("Verifique os logs para mais detalhes.")

if __name__ == "__main__":
    main()

