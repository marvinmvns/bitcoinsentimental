#!/usr/bin/env python3
"""
Analisador de Sentimento Aprimorado com Ollama
Integração do sistema existente com modelos LLM locais
"""

import requests
import json
import time
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

# Importar analisadores existentes
try:
    from .sentiment_analyzer import SentimentAnalyzer
    EXISTING_ANALYZER_AVAILABLE = True
except ImportError:
    print("Aviso: Analisador existente não encontrado")
    EXISTING_ANALYZER_AVAILABLE = False

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EnhancedSentimentResult:
    """Resultado aprimorado da análise de sentimento"""
    # Resultado do Ollama
    ollama_sentiment: str
    ollama_confidence: float
    ollama_score: float
    ollama_time: float
    
    # Resultado dos analisadores tradicionais
    vader_sentiment: str = "neutral"
    vader_score: float = 0.0
    textblob_sentiment: str = "neutral"
    textblob_score: float = 0.0
    
    # Resultado combinado
    final_sentiment: str = "neutral"
    final_score: float = 0.0
    final_confidence: float = 0.0
    
    # Metadados
    text_analyzed: str = ""
    timestamp: str = ""
    models_used: List[str] = None

class EnhancedSentimentAnalyzer:
    """Analisador de sentimento aprimorado combinando Ollama + métodos tradicionais"""
    
    def __init__(self, ollama_model: str = "llama3.2:1b", ollama_url: str = "http://localhost:11434"):
        """
        Inicializa o analisador aprimorado
        
        Args:
            ollama_model: Nome do modelo Ollama
            ollama_url: URL do servidor Ollama
        """
        self.ollama_model = ollama_model
        self.ollama_url = ollama_url
        self.traditional_analyzer = None
        
        # Inicializar analisador tradicional se disponível
        if EXISTING_ANALYZER_AVAILABLE:
            try:
                self.traditional_analyzer = SentimentAnalyzer()
                logger.info("Analisador tradicional inicializado")
            except Exception as e:
                logger.warning(f"Erro ao inicializar analisador tradicional: {e}")
        
        # Testar conexão com Ollama
        self._test_ollama_connection()
    
    def _test_ollama_connection(self) -> bool:
        """Testa conexão com Ollama"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                if self.ollama_model in model_names:
                    logger.info(f"Conexão com Ollama OK. Modelo {self.ollama_model} disponível.")
                    return True
                else:
                    logger.warning(f"Modelo {self.ollama_model} não encontrado. Modelos disponíveis: {model_names}")
                    return False
            else:
                logger.error(f"Erro ao conectar com Ollama: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Erro de conexão com Ollama: {e}")
            return False
    
    def _analyze_with_ollama(self, text: str) -> Tuple[str, float, float]:
        """
        Analisa sentimento usando Ollama
        
        Returns:
            Tuple[sentiment, confidence, score, processing_time]
        """
        start_time = time.time()
        
        # Prompt otimizado para análise de sentimento financeiro
        prompt = f"""
Analyze the sentiment of this Bitcoin/cryptocurrency text: "{text}"

Consider:
- Financial context and market implications
- Emotional tone and intensity
- Investment sentiment (bullish/bearish)

Return your analysis in this exact format:
Sentiment: [positive/negative/neutral]
Confidence: [0.0-1.0]
Score: [-1.0 to 1.0]
Reasoning: [brief explanation]
"""
        
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 100
            }
        }
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=30
            )
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '').strip()
                
                # Parse da resposta
                sentiment, confidence, score = self._parse_ollama_response(response_text)
                
                logger.info(f"Ollama análise: {sentiment} (conf: {confidence:.2f}, score: {score:.2f})")
                return sentiment, confidence, score, processing_time
            else:
                logger.error(f"Erro Ollama: {response.status_code}")
                return "neutral", 0.0, 0.0, processing_time
                
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Erro na análise Ollama: {e}")
            return "neutral", 0.0, 0.0, processing_time
    
    def _parse_ollama_response(self, response_text: str) -> Tuple[str, float, float]:
        """Parse da resposta do Ollama"""
        sentiment = "neutral"
        confidence = 0.5
        score = 0.0
        
        try:
            lines = response_text.lower().split('\n')
            
            for line in lines:
                if 'sentiment:' in line:
                    if 'positive' in line:
                        sentiment = "positive"
                    elif 'negative' in line:
                        sentiment = "negative"
                    else:
                        sentiment = "neutral"
                
                elif 'confidence:' in line:
                    # Extrair número da linha
                    import re
                    numbers = re.findall(r'0\.\d+|\d+\.\d+', line)
                    if numbers:
                        confidence = min(1.0, max(0.0, float(numbers[0])))
                
                elif 'score:' in line:
                    import re
                    numbers = re.findall(r'-?\d+\.\d+|-?\d+', line)
                    if numbers:
                        score = min(1.0, max(-1.0, float(numbers[0])))
            
            # Fallback: análise simples se parsing falhar
            if sentiment == "neutral" and confidence == 0.5:
                response_lower = response_text.lower()
                if any(word in response_lower for word in ['positive', 'bullish', 'good', 'buy']):
                    sentiment = "positive"
                    score = 0.6
                    confidence = 0.7
                elif any(word in response_lower for word in ['negative', 'bearish', 'bad', 'sell']):
                    sentiment = "negative"
                    score = -0.6
                    confidence = 0.7
        
        except Exception as e:
            logger.warning(f"Erro no parsing da resposta Ollama: {e}")
        
        return sentiment, confidence, score
    
    def _analyze_traditional(self, text: str) -> Tuple[str, float, str, float]:
        """Analisa usando métodos tradicionais"""
        if not self.traditional_analyzer:
            return "neutral", 0.0, "neutral", 0.0
        
        try:
            # Usar analisador existente
            vader_result = self.traditional_analyzer.analyze_vader(text)
            textblob_result = self.traditional_analyzer.analyze_textblob(text)
            
            # Converter scores para sentimentos
            vader_sentiment = "positive" if vader_result > 0.1 else "negative" if vader_result < -0.1 else "neutral"
            textblob_sentiment = "positive" if textblob_result > 0.1 else "negative" if textblob_result < -0.1 else "neutral"
            
            return vader_sentiment, vader_result, textblob_sentiment, textblob_result
            
        except Exception as e:
            logger.warning(f"Erro na análise tradicional: {e}")
            return "neutral", 0.0, "neutral", 0.0
    
    def _combine_results(self, ollama_sentiment: str, ollama_score: float, ollama_confidence: float,
                        vader_sentiment: str, vader_score: float,
                        textblob_sentiment: str, textblob_score: float) -> Tuple[str, float, float]:
        """
        Combina resultados de diferentes analisadores
        
        Pesos: Ollama 60%, VADER 25%, TextBlob 15%
        """
        
        # Converter sentimentos para scores numéricos
        def sentiment_to_score(sentiment: str) -> float:
            return 1.0 if sentiment == "positive" else -1.0 if sentiment == "negative" else 0.0
        
        ollama_numeric = sentiment_to_score(ollama_sentiment)
        vader_numeric = sentiment_to_score(vader_sentiment)
        textblob_numeric = sentiment_to_score(textblob_sentiment)
        
        # Ponderação baseada na confiança do Ollama
        ollama_weight = 0.6 * ollama_confidence
        vader_weight = 0.25
        textblob_weight = 0.15
        
        # Normalizar pesos
        total_weight = ollama_weight + vader_weight + textblob_weight
        ollama_weight /= total_weight
        vader_weight /= total_weight
        textblob_weight /= total_weight
        
        # Score combinado
        combined_score = (
            ollama_score * ollama_weight +
            vader_score * vader_weight +
            textblob_score * textblob_weight
        )
        
        # Sentimento combinado
        if combined_score > 0.1:
            final_sentiment = "positive"
        elif combined_score < -0.1:
            final_sentiment = "negative"
        else:
            final_sentiment = "neutral"
        
        # Confiança baseada na concordância entre modelos
        agreements = 0
        if ollama_sentiment == vader_sentiment:
            agreements += 1
        if ollama_sentiment == textblob_sentiment:
            agreements += 1
        if vader_sentiment == textblob_sentiment:
            agreements += 1
        
        # Confiança: base do Ollama + bônus por concordância
        final_confidence = min(1.0, ollama_confidence * 0.7 + (agreements / 3) * 0.3)
        
        return final_sentiment, combined_score, final_confidence
    
    def analyze_sentiment(self, text: str) -> EnhancedSentimentResult:
        """
        Análise completa de sentimento
        
        Args:
            text: Texto para análise
            
        Returns:
            EnhancedSentimentResult com análise completa
        """
        timestamp = datetime.now().isoformat()
        models_used = []
        
        # Análise com Ollama
        ollama_sentiment, ollama_confidence, ollama_score, ollama_time = self._analyze_with_ollama(text)
        models_used.append(f"ollama:{self.ollama_model}")
        
        # Análise tradicional
        vader_sentiment, vader_score, textblob_sentiment, textblob_score = self._analyze_traditional(text)
        if self.traditional_analyzer:
            models_used.extend(["vader", "textblob"])
        
        # Combinar resultados
        final_sentiment, final_score, final_confidence = self._combine_results(
            ollama_sentiment, ollama_score, ollama_confidence,
            vader_sentiment, vader_score,
            textblob_sentiment, textblob_score
        )
        
        return EnhancedSentimentResult(
            # Ollama
            ollama_sentiment=ollama_sentiment,
            ollama_confidence=ollama_confidence,
            ollama_score=ollama_score,
            ollama_time=ollama_time,
            
            # Tradicionais
            vader_sentiment=vader_sentiment,
            vader_score=vader_score,
            textblob_sentiment=textblob_sentiment,
            textblob_score=textblob_score,
            
            # Combinado
            final_sentiment=final_sentiment,
            final_score=final_score,
            final_confidence=final_confidence,
            
            # Metadados
            text_analyzed=text,
            timestamp=timestamp,
            models_used=models_used
        )
    
    def analyze_batch(self, texts: List[str]) -> List[EnhancedSentimentResult]:
        """Análise em lote"""
        results = []
        for i, text in enumerate(texts):
            logger.info(f"Analisando texto {i+1}/{len(texts)}")
            result = self.analyze_sentiment(text)
            results.append(result)
            
            # Pausa para não sobrecarregar
            if i < len(texts) - 1:
                time.sleep(0.2)
        
        return results

def test_enhanced_analyzer():
    """Teste do analisador aprimorado"""
    print("=== Teste do Analisador Aprimorado ===")
    
    analyzer = EnhancedSentimentAnalyzer()
    
    test_texts = [
        "Bitcoin is going to the moon! Best investment ever!",
        "Bitcoin is crashing! Worst investment ever! I lost everything!",
        "Bitcoin price is stable today, no major movements.",
        "HODL! Diamond hands! Bitcoin will reach $100k soon!",
        "This Bitcoin dump is terrible, selling everything now."
    ]
    
    print("\n" + "="*80)
    
    for i, text in enumerate(test_texts, 1):
        print(f"\nTeste {i}: {text}")
        print("-" * 60)
        
        result = analyzer.analyze_sentiment(text)
        
        print(f"Ollama: {result.ollama_sentiment} (conf: {result.ollama_confidence:.2f}, score: {result.ollama_score:.2f})")
        print(f"VADER: {result.vader_sentiment} (score: {result.vader_score:.2f})")
        print(f"TextBlob: {result.textblob_sentiment} (score: {result.textblob_score:.2f})")
        print(f"FINAL: {result.final_sentiment} (conf: {result.final_confidence:.2f}, score: {result.final_score:.2f})")
        print(f"Modelos: {', '.join(result.models_used)}")
        print(f"Tempo Ollama: {result.ollama_time:.2f}s")

if __name__ == "__main__":
    test_enhanced_analyzer()

