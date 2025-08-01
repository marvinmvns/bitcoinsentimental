#!/usr/bin/env python3
"""
Sistema de Análise de Sentimento para Bitcoin Trading
Módulo principal com diferentes abordagens de análise de sentimento
"""

import re
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SentimentResult:
    """Resultado da análise de sentimento"""
    text: str
    sentiment: str  # 'positive', 'negative', 'neutral'
    score: float    # -1.0 a 1.0
    confidence: float  # 0.0 a 1.0
    model_used: str
    timestamp: datetime

@dataclass
class WeightedSentimentScore:
    """Score de sentimento ponderado para múltiplos textos"""
    positive_score: float
    negative_score: float
    neutral_score: float
    weighted_score: float  # Score final ponderado
    total_texts: int
    timestamp: datetime

class SentimentAnalyzer(ABC):
    """Classe base abstrata para analisadores de sentimento"""
    
    def __init__(self, name: str):
        self.name = name
        self.model = None
        
    @abstractmethod
    def analyze(self, text: str) -> SentimentResult:
        """Analisa o sentimento de um texto"""
        pass
    
    @abstractmethod
    def batch_analyze(self, texts: List[str]) -> List[SentimentResult]:
        """Analisa o sentimento de múltiplos textos"""
        pass
    
    def preprocess_text(self, text: str) -> str:
        """Pré-processamento básico do texto"""
        if not text:
            return ""
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove menções (@username)
        text = re.sub(r'@\w+', '', text)
        
        # Remove hashtags mas mantém o texto
        text = re.sub(r'#(\w+)', r'\1', text)
        
        # Remove caracteres especiais excessivos
        text = re.sub(r'[^\w\s\.\!\?\,\;\:\-\(\)]', ' ', text)
        
        # Remove espaços múltiplos
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()

class VADERSentimentAnalyzer(SentimentAnalyzer):
    """Analisador de sentimento usando VADER"""
    
    def __init__(self):
        super().__init__("VADER")
        try:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            self.model = SentimentIntensityAnalyzer()
            logger.info("VADER Sentiment Analyzer inicializado")
        except ImportError:
            logger.error("VADER não está instalado. Execute: pip install vaderSentiment")
            raise
    
    def analyze(self, text: str) -> SentimentResult:
        """Analisa sentimento usando VADER"""
        if not self.model:
            raise RuntimeError("Modelo VADER não inicializado")
        
        processed_text = self.preprocess_text(text)
        scores = self.model.polarity_scores(processed_text)
        
        # Determina sentimento baseado no compound score
        compound = scores['compound']
        if compound >= 0.05:
            sentiment = 'positive'
        elif compound <= -0.05:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        # Confidence baseado na magnitude do compound score
        confidence = abs(compound)
        
        return SentimentResult(
            text=text,
            sentiment=sentiment,
            score=compound,
            confidence=confidence,
            model_used=self.name,
            timestamp=datetime.now()
        )
    
    def batch_analyze(self, texts: List[str]) -> List[SentimentResult]:
        """Análise em lote usando VADER"""
        return [self.analyze(text) for text in texts]

class TextBlobSentimentAnalyzer(SentimentAnalyzer):
    """Analisador de sentimento usando TextBlob"""
    
    def __init__(self):
        super().__init__("TextBlob")
        try:
            from textblob import TextBlob
            self.TextBlob = TextBlob
            logger.info("TextBlob Sentiment Analyzer inicializado")
        except ImportError:
            logger.error("TextBlob não está instalado. Execute: pip install textblob")
            raise
    
    def analyze(self, text: str) -> SentimentResult:
        """Analisa sentimento usando TextBlob"""
        processed_text = self.preprocess_text(text)
        blob = self.TextBlob(processed_text)
        
        polarity = blob.sentiment.polarity  # -1 a 1
        subjectivity = blob.sentiment.subjectivity  # 0 a 1
        
        # Determina sentimento
        if polarity > 0.1:
            sentiment = 'positive'
        elif polarity < -0.1:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        # Confidence baseado na subjetividade
        confidence = subjectivity
        
        return SentimentResult(
            text=text,
            sentiment=sentiment,
            score=polarity,
            confidence=confidence,
            model_used=self.name,
            timestamp=datetime.now()
        )
    
    def batch_analyze(self, texts: List[str]) -> List[SentimentResult]:
        """Análise em lote usando TextBlob"""
        return [self.analyze(text) for text in texts]

class TransformerSentimentAnalyzer(SentimentAnalyzer):
    """Analisador de sentimento usando modelos Transformer (BERT, FinBERT, CryptoBERT)"""
    
    def __init__(self, model_name: str = "ElKulako/cryptobert"):
        super().__init__(f"Transformer-{model_name}")
        self.model_name = model_name
        try:
            from transformers import pipeline
            self.model = pipeline(
                "sentiment-analysis",
                model=model_name,
                return_all_scores=True
            )
            logger.info(f"Transformer Sentiment Analyzer inicializado com {model_name}")
        except ImportError:
            logger.error("Transformers não está instalado. Execute: pip install transformers torch")
            raise
        except Exception as e:
            logger.error(f"Erro ao carregar modelo {model_name}: {e}")
            # Fallback para modelo padrão
            try:
                self.model = pipeline("sentiment-analysis", return_all_scores=True)
                logger.info("Usando modelo padrão de sentiment analysis")
            except:
                raise RuntimeError("Não foi possível inicializar nenhum modelo transformer")
    
    def analyze(self, text: str) -> SentimentResult:
        """Analisa sentimento usando modelo Transformer"""
        if not self.model:
            raise RuntimeError("Modelo Transformer não inicializado")
        
        processed_text = self.preprocess_text(text)
        if not processed_text:
            return SentimentResult(
                text=text,
                sentiment='neutral',
                score=0.0,
                confidence=0.0,
                model_used=self.name,
                timestamp=datetime.now()
            )
        
        try:
            results = self.model(processed_text)[0]
            
            # Processa resultados
            sentiment_scores = {result['label'].lower(): result['score'] for result in results}
            
            # Determina sentimento dominante
            max_label = max(sentiment_scores, key=sentiment_scores.get)
            max_score = sentiment_scores[max_label]
            
            # Mapeia labels para formato padrão
            if 'positive' in max_label or 'pos' in max_label:
                sentiment = 'positive'
                score = max_score
            elif 'negative' in max_label or 'neg' in max_label:
                sentiment = 'negative'
                score = -max_score
            else:
                sentiment = 'neutral'
                score = 0.0
            
            return SentimentResult(
                text=text,
                sentiment=sentiment,
                score=score,
                confidence=max_score,
                model_used=self.name,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Erro na análise transformer: {e}")
            return SentimentResult(
                text=text,
                sentiment='neutral',
                score=0.0,
                confidence=0.0,
                model_used=self.name,
                timestamp=datetime.now()
            )
    
    def batch_analyze(self, texts: List[str]) -> List[SentimentResult]:
        """Análise em lote usando Transformer"""
        return [self.analyze(text) for text in texts]

class EnsembleSentimentAnalyzer:
    """Analisador ensemble que combina múltiplos modelos"""
    
    def __init__(self, analyzers: List[SentimentAnalyzer], weights: Optional[List[float]] = None):
        self.analyzers = analyzers
        self.weights = weights or [1.0] * len(analyzers)
        
        if len(self.weights) != len(self.analyzers):
            raise ValueError("Número de pesos deve ser igual ao número de analisadores")
        
        # Normaliza pesos
        total_weight = sum(self.weights)
        self.weights = [w / total_weight for w in self.weights]
        
        logger.info(f"Ensemble inicializado com {len(analyzers)} analisadores")
    
    def analyze(self, text: str) -> SentimentResult:
        """Análise ensemble combinando múltiplos modelos"""
        results = []
        
        for analyzer in self.analyzers:
            try:
                result = analyzer.analyze(text)
                results.append(result)
            except Exception as e:
                logger.warning(f"Erro no analisador {analyzer.name}: {e}")
                continue
        
        if not results:
            return SentimentResult(
                text=text,
                sentiment='neutral',
                score=0.0,
                confidence=0.0,
                model_used="Ensemble-Failed",
                timestamp=datetime.now()
            )
        
        # Combina resultados usando pesos
        weighted_score = 0.0
        weighted_confidence = 0.0
        sentiment_votes = {'positive': 0, 'negative': 0, 'neutral': 0}
        
        for i, result in enumerate(results):
            weight = self.weights[i] if i < len(self.weights) else 1.0
            weighted_score += result.score * weight
            weighted_confidence += result.confidence * weight
            sentiment_votes[result.sentiment] += weight
        
        # Determina sentimento final por votação ponderada
        final_sentiment = max(sentiment_votes, key=sentiment_votes.get)
        
        return SentimentResult(
            text=text,
            sentiment=final_sentiment,
            score=weighted_score,
            confidence=weighted_confidence,
            model_used="Ensemble",
            timestamp=datetime.now()
        )
    
    def batch_analyze(self, texts: List[str]) -> List[SentimentResult]:
        """Análise em lote usando ensemble"""
        return [self.analyze(text) for text in texts]

class SentimentAggregator:
    """Agregador para calcular scores de sentimento ponderados"""
    
    @staticmethod
    def calculate_weighted_sentiment(results: List[SentimentResult]) -> WeightedSentimentScore:
        """Calcula score de sentimento ponderado baseado na metodologia UC Berkeley"""
        if not results:
            return WeightedSentimentScore(0.0, 0.0, 0.0, 0.0, 0, datetime.now())
        
        positive_score = 0.0
        negative_score = 0.0
        neutral_score = 0.0
        
        for result in results:
            if result.sentiment == 'positive':
                positive_score += result.confidence
            elif result.sentiment == 'negative':
                negative_score += result.confidence
            else:
                neutral_score += result.confidence
        
        # Score ponderado final: positivos - negativos
        weighted_score = positive_score - negative_score
        
        return WeightedSentimentScore(
            positive_score=positive_score,
            negative_score=negative_score,
            neutral_score=neutral_score,
            weighted_score=weighted_score,
            total_texts=len(results),
            timestamp=datetime.now()
        )
    
    @staticmethod
    def aggregate_by_timeframe(
        results: List[SentimentResult], 
        timeframe: str = '1H'
    ) -> Dict[datetime, WeightedSentimentScore]:
        """Agrega resultados por período de tempo"""
        if not results:
            return {}
        
        # Converte para DataFrame para facilitar agregação
        df = pd.DataFrame([
            {
                'timestamp': result.timestamp,
                'sentiment': result.sentiment,
                'score': result.score,
                'confidence': result.confidence
            }
            for result in results
        ])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        # Agrupa por período
        grouped = df.groupby(pd.Grouper(freq=timeframe))
        
        aggregated = {}
        for timestamp, group in grouped:
            if len(group) > 0:
                group_results = [
                    SentimentResult(
                        text="",
                        sentiment=row['sentiment'],
                        score=row['score'],
                        confidence=row['confidence'],
                        model_used="",
                        timestamp=timestamp
                    )
                    for _, row in group.iterrows()
                ]
                
                weighted_score = SentimentAggregator.calculate_weighted_sentiment(group_results)
                aggregated[timestamp] = weighted_score
        
        return aggregated

def create_sentiment_analyzer(analyzer_type: str = "ensemble") -> Union[SentimentAnalyzer, EnsembleSentimentAnalyzer]:
    """Factory function para criar analisadores de sentimento"""
    
    if analyzer_type.lower() == "vader":
        return VADERSentimentAnalyzer()
    
    elif analyzer_type.lower() == "textblob":
        return TextBlobSentimentAnalyzer()
    
    elif analyzer_type.lower() == "transformer":
        return TransformerSentimentAnalyzer()
    
    elif analyzer_type.lower() == "cryptobert":
        return TransformerSentimentAnalyzer("ElKulako/cryptobert")
    
    elif analyzer_type.lower() == "finbert":
        return TransformerSentimentAnalyzer("ProsusAI/finbert")
    
    elif analyzer_type.lower() == "ensemble":
        analyzers = []
        weights = []
        
        # Tenta criar VADER
        try:
            analyzers.append(VADERSentimentAnalyzer())
            weights.append(0.3)  # 30% peso para VADER
        except:
            logger.warning("VADER não disponível")
        
        # Tenta criar TextBlob
        try:
            analyzers.append(TextBlobSentimentAnalyzer())
            weights.append(0.2)  # 20% peso para TextBlob
        except:
            logger.warning("TextBlob não disponível")
        
        # Tenta criar CryptoBERT
        try:
            analyzers.append(TransformerSentimentAnalyzer("ElKulako/cryptobert"))
            weights.append(0.5)  # 50% peso para CryptoBERT
        except:
            logger.warning("CryptoBERT não disponível, tentando modelo padrão")
            try:
                analyzers.append(TransformerSentimentAnalyzer())
                weights.append(0.5)
            except:
                logger.warning("Nenhum modelo transformer disponível")
        
        if not analyzers:
            raise RuntimeError("Nenhum analisador de sentimento disponível")
        
        return EnsembleSentimentAnalyzer(analyzers, weights)
    
    else:
        raise ValueError(f"Tipo de analisador não suportado: {analyzer_type}")

if __name__ == "__main__":
    # Teste básico
    print("Testando Sistema de Análise de Sentimento")
    
    # Textos de teste relacionados a Bitcoin
    test_texts = [
        "Bitcoin is going to the moon! 🚀 Best investment ever!",
        "BTC is crashing hard, time to sell everything",
        "Bitcoin price is stable today, waiting for next move",
        "HODL Bitcoin, diamond hands! 💎🙌",
        "Bitcoin bubble is about to burst, be careful"
    ]
    
    try:
        # Testa diferentes analisadores
        for analyzer_type in ["vader", "textblob", "ensemble"]:
            print(f"\n--- Testando {analyzer_type.upper()} ---")
            
            try:
                analyzer = create_sentiment_analyzer(analyzer_type)
                
                for text in test_texts:
                    result = analyzer.analyze(text)
                    print(f"Texto: {text[:50]}...")
                    print(f"Sentimento: {result.sentiment} | Score: {result.score:.3f} | Confiança: {result.confidence:.3f}")
                    print()
                    
            except Exception as e:
                print(f"Erro ao testar {analyzer_type}: {e}")
                
    except Exception as e:
        print(f"Erro geral: {e}")

