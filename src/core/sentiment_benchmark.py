#!/usr/bin/env python3
"""
Sistema de Benchmark para Análise de Sentimento
Compara performance entre Ollama LLM e métodos tradicionais
"""

import time
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import numpy as np

# Importar analisadores
try:
    from ..sentiment.enhanced_sentiment_analyzer import EnhancedSentimentAnalyzer
    ENHANCED_AVAILABLE = True
except ImportError:
    print("Analisador aprimorado não disponível")
    ENHANCED_AVAILABLE = False

try:
    from .test_ollama_simple import test_ollama_direct
    SIMPLE_OLLAMA_AVAILABLE = True
except ImportError:
    print("Teste simples Ollama não disponível")
    SIMPLE_OLLAMA_AVAILABLE = False

@dataclass
class BenchmarkResult:
    """Resultado de benchmark"""
    text: str
    expected_sentiment: str
    
    # Resultados dos modelos
    ollama_sentiment: str
    ollama_confidence: float
    ollama_time: float
    
    traditional_sentiment: str = "neutral"
    traditional_confidence: float = 0.0
    traditional_time: float = 0.0
    
    # Métricas
    ollama_correct: bool = False
    traditional_correct: bool = False
    
    # Metadados
    timestamp: str = ""

class SentimentBenchmark:
    """Sistema de benchmark para análise de sentimento"""
    
    def __init__(self):
        """Inicializa o sistema de benchmark"""
        self.analyzer = None
        self.results = []
        
        if ENHANCED_AVAILABLE:
            try:
                self.analyzer = EnhancedSentimentAnalyzer()
                print("✅ Analisador aprimorado inicializado")
            except Exception as e:
                print(f"❌ Erro ao inicializar analisador: {e}")
    
    def create_test_dataset(self) -> List[Tuple[str, str]]:
        """
        Cria dataset de teste com sentimentos conhecidos
        
        Returns:
            Lista de (texto, sentimento_esperado)
        """
        test_data = [
            # Sentimentos POSITIVOS
            ("Bitcoin is going to the moon! Best investment ever!", "positive"),
            ("HODL! Diamond hands! Bitcoin will reach $100k soon!", "positive"),
            ("Bitcoin just broke all-time high! Incredible gains!", "positive"),
            ("This Bitcoin rally is amazing! Buying more!", "positive"),
            ("Bitcoin adoption is growing fast! Bullish!", "positive"),
            ("Just made huge profits on Bitcoin! To the moon!", "positive"),
            ("Bitcoin is the future of money! Revolutionary!", "positive"),
            ("Institutional investors are buying Bitcoin! Bullish signal!", "positive"),
            ("Bitcoin network is stronger than ever! Optimistic!", "positive"),
            ("Bitcoin price surge is just the beginning!", "positive"),
            
            # Sentimentos NEGATIVOS
            ("Bitcoin is crashing! Worst investment ever! I lost everything!", "negative"),
            ("This Bitcoin dump is terrible, selling everything now.", "negative"),
            ("Bitcoin is a scam! Don't invest in this bubble!", "negative"),
            ("Bitcoin crash wiped out my savings! Disaster!", "negative"),
            ("Bitcoin is dead! No future for this coin!", "negative"),
            ("Massive Bitcoin selloff! Market is collapsing!", "negative"),
            ("Bitcoin regulation will kill the market! Bearish!", "negative"),
            ("Bitcoin energy consumption is destroying the planet!", "negative"),
            ("Bitcoin volatility is too risky! Stay away!", "negative"),
            ("Bitcoin whale manipulation is ruining the market!", "negative"),
            
            # Sentimentos NEUTROS
            ("Bitcoin price is stable today, no major movements.", "neutral"),
            ("Bitcoin trading volume is normal for this time.", "neutral"),
            ("Bitcoin price analysis shows mixed signals.", "neutral"),
            ("Bitcoin market cap remains unchanged today.", "neutral"),
            ("Bitcoin technical indicators are inconclusive.", "neutral"),
            ("Bitcoin price consolidating in current range.", "neutral"),
            ("Bitcoin market showing sideways movement.", "neutral"),
            ("Bitcoin price action is range-bound today.", "neutral"),
            ("Bitcoin volatility decreased compared to yesterday.", "neutral"),
            ("Bitcoin market waiting for next catalyst.", "neutral"),
        ]
        
        return test_data
    
    def run_benchmark(self) -> List[BenchmarkResult]:
        """
        Executa benchmark completo
        
        Returns:
            Lista de BenchmarkResult
        """
        if not self.analyzer:
            print("❌ Analisador não disponível")
            return []
        
        test_data = self.create_test_dataset()
        results = []
        
        print(f"🚀 Iniciando benchmark com {len(test_data)} textos...")
        print("="*60)
        
        for i, (text, expected) in enumerate(test_data, 1):
            print(f"\n[{i}/{len(test_data)}] Analisando: {text[:50]}...")
            
            try:
                # Análise com analisador aprimorado
                start_time = time.time()
                enhanced_result = self.analyzer.analyze_sentiment(text)
                total_time = time.time() - start_time
                
                # Verificar acurácia
                ollama_correct = enhanced_result.ollama_sentiment == expected
                final_correct = enhanced_result.final_sentiment == expected
                
                result = BenchmarkResult(
                    text=text,
                    expected_sentiment=expected,
                    ollama_sentiment=enhanced_result.ollama_sentiment,
                    ollama_confidence=enhanced_result.ollama_confidence,
                    ollama_time=enhanced_result.ollama_time,
                    traditional_sentiment=enhanced_result.final_sentiment,
                    traditional_confidence=enhanced_result.final_confidence,
                    traditional_time=total_time,
                    ollama_correct=ollama_correct,
                    traditional_correct=final_correct,
                    timestamp=datetime.now().isoformat()
                )
                
                results.append(result)
                
                # Feedback em tempo real
                ollama_status = "✅" if ollama_correct else "❌"
                final_status = "✅" if final_correct else "❌"
                
                print(f"  Esperado: {expected}")
                print(f"  Ollama: {enhanced_result.ollama_sentiment} {ollama_status} (conf: {enhanced_result.ollama_confidence:.2f})")
                print(f"  Final: {enhanced_result.final_sentiment} {final_status} (conf: {enhanced_result.final_confidence:.2f})")
                print(f"  Tempo: {enhanced_result.ollama_time:.2f}s")
                
            except Exception as e:
                print(f"  ❌ Erro: {e}")
                continue
        
        self.results = results
        return results
    
    def calculate_metrics(self, results: List[BenchmarkResult]) -> Dict:
        """Calcula métricas de performance"""
        if not results:
            return {}
        
        # Acurácia
        ollama_accuracy = sum(r.ollama_correct for r in results) / len(results)
        traditional_accuracy = sum(r.traditional_correct for r in results) / len(results)
        
        # Tempo médio
        avg_ollama_time = np.mean([r.ollama_time for r in results])
        avg_traditional_time = np.mean([r.traditional_time for r in results])
        
        # Confiança média
        avg_ollama_confidence = np.mean([r.ollama_confidence for r in results])
        avg_traditional_confidence = np.mean([r.traditional_confidence for r in results])
        
        # Acurácia por sentimento
        by_sentiment = {}
        for sentiment in ['positive', 'negative', 'neutral']:
            sentiment_results = [r for r in results if r.expected_sentiment == sentiment]
            if sentiment_results:
                ollama_acc = sum(r.ollama_correct for r in sentiment_results) / len(sentiment_results)
                trad_acc = sum(r.traditional_correct for r in sentiment_results) / len(sentiment_results)
                by_sentiment[sentiment] = {
                    'ollama_accuracy': ollama_acc,
                    'traditional_accuracy': trad_acc,
                    'count': len(sentiment_results)
                }
        
        return {
            'overall': {
                'ollama_accuracy': ollama_accuracy,
                'traditional_accuracy': traditional_accuracy,
                'avg_ollama_time': avg_ollama_time,
                'avg_traditional_time': avg_traditional_time,
                'avg_ollama_confidence': avg_ollama_confidence,
                'avg_traditional_confidence': avg_traditional_confidence,
                'total_samples': len(results)
            },
            'by_sentiment': by_sentiment
        }
    
    def generate_report(self, results: List[BenchmarkResult], metrics: Dict) -> str:
        """Gera relatório detalhado"""
        report = []
        report.append("="*80)
        report.append("📊 RELATÓRIO DE BENCHMARK - ANÁLISE DE SENTIMENTO")
        report.append("="*80)
        report.append(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total de amostras: {metrics['overall']['total_samples']}")
        report.append("")
        
        # Métricas gerais
        report.append("🎯 MÉTRICAS GERAIS")
        report.append("-" * 40)
        report.append(f"Acurácia Ollama LLM:     {metrics['overall']['ollama_accuracy']:.1%}")
        report.append(f"Acurácia Sistema Final:  {metrics['overall']['traditional_accuracy']:.1%}")
        report.append(f"Tempo médio Ollama:      {metrics['overall']['avg_ollama_time']:.2f}s")
        report.append(f"Tempo médio Total:       {metrics['overall']['avg_traditional_time']:.2f}s")
        report.append(f"Confiança média Ollama:  {metrics['overall']['avg_ollama_confidence']:.2f}")
        report.append(f"Confiança média Final:   {metrics['overall']['avg_traditional_confidence']:.2f}")
        report.append("")
        
        # Métricas por sentimento
        report.append("📈 ACURÁCIA POR SENTIMENTO")
        report.append("-" * 40)
        for sentiment, data in metrics['by_sentiment'].items():
            report.append(f"{sentiment.upper()}:")
            report.append(f"  Ollama:  {data['ollama_accuracy']:.1%} ({data['count']} amostras)")
            report.append(f"  Final:   {data['traditional_accuracy']:.1%}")
            report.append("")
        
        # Análise comparativa
        report.append("🔍 ANÁLISE COMPARATIVA")
        report.append("-" * 40)
        
        ollama_acc = metrics['overall']['ollama_accuracy']
        final_acc = metrics['overall']['traditional_accuracy']
        
        if final_acc > ollama_acc:
            improvement = (final_acc - ollama_acc) * 100
            report.append(f"✅ Sistema final {improvement:.1f}% mais preciso que Ollama sozinho")
        elif ollama_acc > final_acc:
            degradation = (ollama_acc - final_acc) * 100
            report.append(f"⚠️  Ollama sozinho {degradation:.1f}% mais preciso que sistema final")
        else:
            report.append("🔄 Performance similar entre Ollama e sistema final")
        
        # Recomendações
        report.append("")
        report.append("💡 RECOMENDAÇÕES")
        report.append("-" * 40)
        
        if ollama_acc >= 0.8:
            report.append("✅ Ollama LLM mostra excelente performance para análise de sentimento")
        elif ollama_acc >= 0.6:
            report.append("⚠️  Ollama LLM mostra performance moderada, considere fine-tuning")
        else:
            report.append("❌ Ollama LLM precisa de melhorias significativas")
        
        if metrics['overall']['avg_ollama_time'] > 10:
            report.append("⏱️  Tempo de resposta do Ollama pode ser otimizado")
        
        if metrics['overall']['avg_ollama_confidence'] < 0.7:
            report.append("🎯 Confiança do modelo pode ser melhorada com prompts mais específicos")
        
        return "\n".join(report)
    
    def save_results(self, results: List[BenchmarkResult], filename: str = "benchmark_results.json"):
        """Salva resultados em arquivo JSON"""
        data = [asdict(result) for result in results]
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"💾 Resultados salvos em {filename}")
    
    def create_visualizations(self, results: List[BenchmarkResult], metrics: Dict):
        """Cria visualizações dos resultados"""
        if not results:
            return
        
        # Configurar estilo
        plt.style.use('seaborn-v0_8')
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Benchmark Análise de Sentimento - Ollama vs Tradicional', fontsize=16, fontweight='bold')
        
        # 1. Acurácia por modelo
        models = ['Ollama LLM', 'Sistema Final']
        accuracies = [metrics['overall']['ollama_accuracy'], metrics['overall']['traditional_accuracy']]
        
        axes[0,0].bar(models, accuracies, color=['#FF6B6B', '#4ECDC4'])
        axes[0,0].set_title('Acurácia Geral')
        axes[0,0].set_ylabel('Acurácia')
        axes[0,0].set_ylim(0, 1)
        for i, v in enumerate(accuracies):
            axes[0,0].text(i, v + 0.02, f'{v:.1%}', ha='center', fontweight='bold')
        
        # 2. Tempo de processamento
        times = [metrics['overall']['avg_ollama_time'], metrics['overall']['avg_traditional_time']]
        axes[0,1].bar(models, times, color=['#FFE66D', '#FF6B6B'])
        axes[0,1].set_title('Tempo Médio de Processamento')
        axes[0,1].set_ylabel('Tempo (segundos)')
        for i, v in enumerate(times):
            axes[0,1].text(i, v + 0.1, f'{v:.2f}s', ha='center', fontweight='bold')
        
        # 3. Acurácia por sentimento
        sentiments = list(metrics['by_sentiment'].keys())
        ollama_by_sentiment = [metrics['by_sentiment'][s]['ollama_accuracy'] for s in sentiments]
        final_by_sentiment = [metrics['by_sentiment'][s]['traditional_accuracy'] for s in sentiments]
        
        x = np.arange(len(sentiments))
        width = 0.35
        
        axes[1,0].bar(x - width/2, ollama_by_sentiment, width, label='Ollama LLM', color='#FF6B6B')
        axes[1,0].bar(x + width/2, final_by_sentiment, width, label='Sistema Final', color='#4ECDC4')
        axes[1,0].set_title('Acurácia por Tipo de Sentimento')
        axes[1,0].set_ylabel('Acurácia')
        axes[1,0].set_xticks(x)
        axes[1,0].set_xticklabels([s.capitalize() for s in sentiments])
        axes[1,0].legend()
        axes[1,0].set_ylim(0, 1)
        
        # 4. Distribuição de confiança
        ollama_confidences = [r.ollama_confidence for r in results]
        final_confidences = [r.traditional_confidence for r in results]
        
        axes[1,1].hist(ollama_confidences, alpha=0.7, label='Ollama LLM', color='#FF6B6B', bins=10)
        axes[1,1].hist(final_confidences, alpha=0.7, label='Sistema Final', color='#4ECDC4', bins=10)
        axes[1,1].set_title('Distribuição de Confiança')
        axes[1,1].set_xlabel('Confiança')
        axes[1,1].set_ylabel('Frequência')
        axes[1,1].legend()
        
        plt.tight_layout()
        plt.savefig('benchmark_results.png', dpi=300, bbox_inches='tight')
        print("📊 Visualizações salvas em benchmark_results.png")
        plt.show()

def run_full_benchmark():
    """Executa benchmark completo"""
    print("🚀 Iniciando Benchmark Completo de Análise de Sentimento")
    print("="*60)
    
    benchmark = SentimentBenchmark()
    
    # Executar benchmark
    results = benchmark.run_benchmark()
    
    if not results:
        print("❌ Nenhum resultado obtido")
        return
    
    # Calcular métricas
    metrics = benchmark.calculate_metrics(results)
    
    # Gerar relatório
    report = benchmark.generate_report(results, metrics)
    print("\n" + report)
    
    # Salvar resultados
    benchmark.save_results(results)
    
    # Criar visualizações
    try:
        benchmark.create_visualizations(results, metrics)
    except Exception as e:
        print(f"⚠️  Erro ao criar visualizações: {e}")
    
    # Salvar relatório
    with open('benchmark_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    print("📄 Relatório salvo em benchmark_report.txt")
    
    return results, metrics

if __name__ == "__main__":
    run_full_benchmark()

