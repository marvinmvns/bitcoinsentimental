#!/usr/bin/env python3
"""
Módulo de Análise de Sentimento com Ollama LLM
Integração com modelos locais para análise de sentimento financeiro
"""

import json
import logging
import time
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

try:
    from langchain_community.chat_models import ChatOllama
    from langchain_core.prompts import PromptTemplate
    from langchain_core.output_parsers import JsonOutputParser
    from langchain_core.pydantic_v1 import BaseModel, Field
    from tenacity import retry, stop_after_attempt, wait_exponential, RetryError
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    print(f"Aviso: Langchain não disponível: {e}")
    LANGCHAIN_AVAILABLE = False

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SentimentResult:
    """Resultado da análise de sentimento"""
    sentiment: str  # positive, negative, neutral
    confidence: float  # 0.0 a 1.0
    score: float  # -1.0 a 1.0
    reasoning: str
    model_used: str
    processing_time: float

class FinancialSentimentSchema(BaseModel):
    """Schema para análise de sentimento financeiro"""
    sentiment: str = Field(description="Sentimento: positive, negative, ou neutral")
    confidence: float = Field(description="Confiança da análise (0.0 a 1.0)")
    score: float = Field(description="Score numérico (-1.0 a 1.0)")
    reasoning: str = Field(description="Justificativa da análise")
    financial_impact: str = Field(description="Impacto financeiro: bullish, bearish, ou neutral")
    key_entities: List[str] = Field(description="Entidades financeiras mencionadas")

class OllamaSentimentAnalyzer:
    """Analisador de sentimento usando modelos Ollama locais"""
    
    def __init__(self, model_name: str = "llama3.2:1b", base_url: str = "http://localhost:11434"):
        """
        Inicializa o analisador
        
        Args:
            model_name: Nome do modelo Ollama
            base_url: URL base do servidor Ollama
        """
        self.model_name = model_name
        self.base_url = base_url
        self.llm = None
        self.parser = JsonOutputParser(pydantic_object=FinancialSentimentSchema)
        
        if LANGCHAIN_AVAILABLE:
            self._initialize_llm()
        else:
            logger.warning("Langchain não disponível. Usando fallback simples.")
    
    def _initialize_llm(self):
        """Inicializa o modelo LLM"""
        try:
            self.llm = ChatOllama(
                model=self.model_name,
                base_url=self.base_url,
                temperature=0.1,  # Baixa temperatura para consistência
                num_predict=512,  # Limite de tokens
                format="json"  # Força saída JSON
            )
            logger.info(f"Modelo {self.model_name} inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao inicializar modelo {self.model_name}: {e}")
            self.llm = None
    
    def _create_prompt_template(self) -> PromptTemplate:
        """Cria template de prompt otimizado para análise de sentimento financeiro"""
        template = """
Você é um especialista em análise de sentimento financeiro. Analise o texto sobre Bitcoin/criptomoedas abaixo e retorne APENAS um JSON válido.

TEXTO: {text}

Analise considerando:
1. Sentimento geral (positive/negative/neutral)
2. Confiança na análise (0.0 a 1.0)
3. Score numérico (-1.0 negativo a +1.0 positivo)
4. Impacto financeiro (bullish/bearish/neutral)
5. Entidades financeiras mencionadas

{format_instructions}

Retorne APENAS o JSON, sem texto adicional:
"""
        
        return PromptTemplate(
            template=template,
            input_variables=["text"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def _analyze_with_llm(self, text: str) -> Dict:
        """Analisa texto usando LLM com retry"""
        if not self.llm:
            raise Exception("Modelo LLM não inicializado")
        
        prompt_template = self._create_prompt_template()
        chain = prompt_template | self.llm | self.parser
        
        result = chain.invoke({"text": text})
        return result
    
    def _fallback_analysis(self, text: str) -> Dict:
        """Análise de fallback simples quando LLM não está disponível"""
        text_lower = text.lower()
        
        # Palavras-chave positivas para Bitcoin
        positive_keywords = [
            'moon', 'bullish', 'buy', 'pump', 'rally', 'surge', 'gain', 'profit',
            'hodl', 'diamond hands', 'to the moon', 'best investment', 'going up',
            'breakout', 'all time high', 'ath', 'bull run', 'institutional adoption'
        ]
        
        # Palavras-chave negativas
        negative_keywords = [
            'crash', 'dump', 'bearish', 'sell', 'loss', 'drop', 'fall', 'decline',
            'worst investment', 'bubble', 'scam', 'dead', 'worthless', 'panic',
            'bear market', 'correction', 'dip', 'blood bath'
        ]
        
        positive_count = sum(1 for word in positive_keywords if word in text_lower)
        negative_count = sum(1 for word in negative_keywords if word in text_lower)
        
        if positive_count > negative_count:
            sentiment = "positive"
            score = min(0.8, 0.3 + (positive_count * 0.1))
            financial_impact = "bullish"
        elif negative_count > positive_count:
            sentiment = "negative"
            score = max(-0.8, -0.3 - (negative_count * 0.1))
            financial_impact = "bearish"
        else:
            sentiment = "neutral"
            score = 0.0
            financial_impact = "neutral"
        
        return {
            "sentiment": sentiment,
            "confidence": 0.6,  # Confiança moderada para fallback
            "score": score,
            "reasoning": f"Análise baseada em palavras-chave: {positive_count} positivas, {negative_count} negativas",
            "financial_impact": financial_impact,
            "key_entities": ["Bitcoin", "BTC"] if any(term in text_lower for term in ['bitcoin', 'btc']) else []
        }
    
    def analyze_sentiment(self, text: str) -> SentimentResult:
        """
        Analisa sentimento de um texto
        
        Args:
            text: Texto para análise
            
        Returns:
            SentimentResult com resultado da análise
        """
        start_time = time.time()
        
        try:
            if self.llm and LANGCHAIN_AVAILABLE:
                # Tenta análise com LLM
                result = self._analyze_with_llm(text)
                logger.info(f"Análise LLM bem-sucedida com {self.model_name}")
            else:
                # Usa fallback
                result = self._fallback_analysis(text)
                logger.info("Usando análise de fallback")
            
            processing_time = time.time() - start_time
            
            return SentimentResult(
                sentiment=result.get("sentiment", "neutral"),
                confidence=result.get("confidence", 0.5),
                score=result.get("score", 0.0),
                reasoning=result.get("reasoning", "Análise automática"),
                model_used=self.model_name if self.llm else "fallback",
                processing_time=processing_time
            )
            
        except RetryError as e:
            logger.error(f"Falha após múltiplas tentativas: {e}")
            # Fallback em caso de erro
            result = self._fallback_analysis(text)
            processing_time = time.time() - start_time
            
            return SentimentResult(
                sentiment=result.get("sentiment", "neutral"),
                confidence=0.3,  # Baixa confiança devido ao erro
                score=result.get("score", 0.0),
                reasoning=f"Fallback após erro: {str(e)[:100]}",
                model_used="fallback_error",
                processing_time=processing_time
            )
        
        except Exception as e:
            logger.error(f"Erro na análise de sentimento: {e}")
            processing_time = time.time() - start_time
            
            return SentimentResult(
                sentiment="neutral",
                confidence=0.1,
                score=0.0,
                reasoning=f"Erro na análise: {str(e)[:100]}",
                model_used="error",
                processing_time=processing_time
            )
    
    def analyze_batch(self, texts: List[str]) -> List[SentimentResult]:
        """
        Analisa múltiplos textos
        
        Args:
            texts: Lista de textos para análise
            
        Returns:
            Lista de SentimentResult
        """
        results = []
        for i, text in enumerate(texts):
            logger.info(f"Analisando texto {i+1}/{len(texts)}")
            result = self.analyze_sentiment(text)
            results.append(result)
            
            # Pequena pausa para não sobrecarregar o modelo
            if i < len(texts) - 1:
                time.sleep(0.1)
        
        return results
    
    def get_model_info(self) -> Dict:
        """Retorna informações sobre o modelo"""
        return {
            "model_name": self.model_name,
            "base_url": self.base_url,
            "langchain_available": LANGCHAIN_AVAILABLE,
            "llm_initialized": self.llm is not None,
            "timestamp": datetime.now().isoformat()
        }

def test_ollama_analyzer():
    """Função de teste do analisador Ollama"""
    print("=== Teste do Analisador de Sentimento Ollama ===")
    
    # Inicializa analisador
    analyzer = OllamaSentimentAnalyzer(model_name="llama3.2:1b")
    
    # Textos de teste
    test_texts = [
        "Bitcoin is going to the moon! Best investment ever!",
        "Bitcoin is crashing! Worst investment ever! I lost everything!",
        "Bitcoin price is stable today, no major movements.",
        "HODL! Diamond hands! Bitcoin will reach $100k soon!",
        "This Bitcoin dump is terrible, selling everything now."
    ]
    
    print(f"\nInfo do modelo: {analyzer.get_model_info()}")
    print("\n" + "="*60)
    
    for i, text in enumerate(test_texts, 1):
        print(f"\nTeste {i}: {text}")
        print("-" * 50)
        
        result = analyzer.analyze_sentiment(text)
        
        print(f"Sentimento: {result.sentiment}")
        print(f"Confiança: {result.confidence:.2f}")
        print(f"Score: {result.score:.2f}")
        print(f"Modelo: {result.model_used}")
        print(f"Tempo: {result.processing_time:.2f}s")
        print(f"Justificativa: {result.reasoning}")

if __name__ == "__main__":
    test_ollama_analyzer()

