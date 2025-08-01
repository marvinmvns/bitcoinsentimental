#!/usr/bin/env python3
"""
Algoritmo de Trading Bitcoin baseado em Análise de Sentimento e Indicadores Técnicos
Combina dados de sentimento do Reddit com análise técnica para decisões de compra/venda
"""

import sys
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
from enum import Enum
import logging
import json

# Importa módulos locais
from ..sentiment.sentiment_analyzer import create_sentiment_analyzer, SentimentAggregator, SentimentResult
from ..data.reddit_collector import BitcoinSentimentCollector

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SignalType(Enum):
    """Tipos de sinais de trading"""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"

@dataclass
class TechnicalIndicators:
    """Indicadores técnicos calculados"""
    rsi: float
    macd: float
    macd_signal: float
    bollinger_upper: float
    bollinger_lower: float
    bollinger_middle: float
    sma_20: float
    sma_50: float
    ema_12: float
    ema_26: float
    volume_sma: float
    price: float
    timestamp: datetime

@dataclass
class TradingSignal:
    """Sinal de trading gerado pelo algoritmo"""
    signal: SignalType
    confidence: float  # 0.0 a 1.0
    sentiment_score: float
    technical_score: float
    combined_score: float
    reasoning: List[str]
    timestamp: datetime
    price: Optional[float] = None
    
    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        return {
            'signal': self.signal.value,
            'confidence': self.confidence,
            'sentiment_score': self.sentiment_score,
            'technical_score': self.technical_score,
            'combined_score': self.combined_score,
            'reasoning': self.reasoning,
            'timestamp': self.timestamp.isoformat(),
            'price': self.price
        }

class TechnicalAnalyzer:
    """Analisador de indicadores técnicos"""
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
        """Calcula RSI (Relative Strength Index)"""
        if len(prices) < period + 1:
            return 50.0  # Valor neutro se não há dados suficientes
        
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0
    
    @staticmethod
    def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float]:
        """Calcula MACD e linha de sinal"""
        if len(prices) < slow:
            return 0.0, 0.0
        
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal).mean()
        
        return float(macd.iloc[-1]), float(macd_signal.iloc[-1])
    
    @staticmethod
    def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: float = 2) -> Tuple[float, float, float]:
        """Calcula Bollinger Bands"""
        if len(prices) < period:
            current_price = float(prices.iloc[-1])
            return current_price * 1.02, current_price, current_price * 0.98
        
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        
        return float(upper.iloc[-1]), float(sma.iloc[-1]), float(lower.iloc[-1])
    
    @staticmethod
    def calculate_moving_averages(prices: pd.Series) -> Dict[str, float]:
        """Calcula médias móveis"""
        result = {}
        
        if len(prices) >= 20:
            result['sma_20'] = float(prices.rolling(window=20).mean().iloc[-1])
        else:
            result['sma_20'] = float(prices.mean())
        
        if len(prices) >= 50:
            result['sma_50'] = float(prices.rolling(window=50).mean().iloc[-1])
        else:
            result['sma_50'] = float(prices.mean())
        
        if len(prices) >= 12:
            result['ema_12'] = float(prices.ewm(span=12).mean().iloc[-1])
        else:
            result['ema_12'] = float(prices.iloc[-1])
        
        if len(prices) >= 26:
            result['ema_26'] = float(prices.ewm(span=26).mean().iloc[-1])
        else:
            result['ema_26'] = float(prices.iloc[-1])
        
        return result

class BitcoinPriceSimulator:
    """Simulador de preços do Bitcoin para teste"""
    
    def __init__(self, initial_price: float = 45000.0):
        self.current_price = initial_price
        self.price_history = [initial_price]
        self.timestamps = [datetime.now()]
        
    def generate_realistic_price_data(self, hours: int = 168) -> pd.DataFrame:
        """Gera dados de preço realistas para teste"""
        
        # Simula dados horários
        data = []
        current_time = datetime.now() - timedelta(hours=hours)
        
        for i in range(hours):
            # Movimento aleatório com tendência
            change_percent = np.random.normal(0, 0.02)  # 2% volatilidade média
            
            # Adiciona alguns eventos de alta volatilidade
            if np.random.random() < 0.05:  # 5% chance de evento de alta volatilidade
                change_percent *= 3
            
            new_price = self.current_price * (1 + change_percent)
            
            # Simula volume (correlacionado com volatilidade)
            volume = np.random.normal(1000, 200) * (1 + abs(change_percent) * 10)
            volume = max(volume, 100)  # Volume mínimo
            
            data.append({
                'timestamp': current_time + timedelta(hours=i),
                'price': new_price,
                'volume': volume,
                'high': new_price * (1 + abs(np.random.normal(0, 0.005))),
                'low': new_price * (1 - abs(np.random.normal(0, 0.005))),
                'open': self.current_price,
                'close': new_price
            })
            
            self.current_price = new_price
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        
        return df

class BitcoinTradingAlgorithm:
    """Algoritmo principal de trading Bitcoin"""
    
    def __init__(self, 
                 sentiment_weight: float = 0.4,
                 technical_weight: float = 0.6,
                 min_confidence: float = 0.6):
        
        self.sentiment_weight = sentiment_weight
        self.technical_weight = technical_weight
        self.min_confidence = min_confidence
        
        # Inicializa componentes
        self.sentiment_analyzer = create_sentiment_analyzer("ensemble")
        self.reddit_collector = BitcoinSentimentCollector()
        self.technical_analyzer = TechnicalAnalyzer()
        self.price_simulator = BitcoinPriceSimulator()
        
        logger.info("Bitcoin Trading Algorithm inicializado")
        logger.info(f"Pesos: Sentimento={sentiment_weight}, Técnico={technical_weight}")
    
    def analyze_sentiment(self, hours_back: int = 24) -> Tuple[float, List[SentimentResult]]:
        """Analisa sentimento dos posts recentes do Reddit"""
        
        logger.info(f"Analisando sentimento das últimas {hours_back} horas")
        
        # Coleta posts recentes
        posts, _ = self.reddit_collector.collect_recent_sentiment_data(
            hours_back=hours_back,
            min_score=5,
            max_posts_per_subreddit=20
        )
        
        if not posts:
            logger.warning("Nenhum post coletado para análise de sentimento")
            return 0.0, []
        
        # Analisa sentimento de cada post
        sentiment_results = []
        for post in posts:
            try:
                result = self.sentiment_analyzer.analyze(post.full_text)
                sentiment_results.append(result)
            except Exception as e:
                logger.warning(f"Erro na análise de sentimento: {e}")
                continue
        
        if not sentiment_results:
            return 0.0, []
        
        # Calcula score ponderado
        weighted_sentiment = SentimentAggregator.calculate_weighted_sentiment(sentiment_results)
        
        # Normaliza score para -1 a 1
        max_possible_score = len(sentiment_results)  # Se todos fossem positivos com confiança 1.0
        normalized_score = weighted_sentiment.weighted_score / max_possible_score if max_possible_score > 0 else 0.0
        normalized_score = max(-1.0, min(1.0, normalized_score))  # Clamp entre -1 e 1
        
        logger.info(f"Score de sentimento: {normalized_score:.3f} (baseado em {len(sentiment_results)} posts)")
        
        return normalized_score, sentiment_results
    
    def analyze_technical_indicators(self, price_data: pd.DataFrame) -> Tuple[float, TechnicalIndicators]:
        """Analisa indicadores técnicos"""
        
        if len(price_data) < 2:
            logger.warning("Dados de preço insuficientes para análise técnica")
            current_price = 45000.0
            return 0.0, TechnicalIndicators(
                rsi=50.0, macd=0.0, macd_signal=0.0,
                bollinger_upper=current_price*1.02, bollinger_lower=current_price*0.98, bollinger_middle=current_price,
                sma_20=current_price, sma_50=current_price, ema_12=current_price, ema_26=current_price,
                volume_sma=1000.0, price=current_price, timestamp=datetime.now()
            )
        
        prices = price_data['price']
        volumes = price_data['volume']
        current_price = float(prices.iloc[-1])
        
        # Calcula indicadores
        rsi = self.technical_analyzer.calculate_rsi(prices)
        macd, macd_signal = self.technical_analyzer.calculate_macd(prices)
        bollinger_upper, bollinger_middle, bollinger_lower = self.technical_analyzer.calculate_bollinger_bands(prices)
        moving_averages = self.technical_analyzer.calculate_moving_averages(prices)
        volume_sma = float(volumes.rolling(window=20).mean().iloc[-1]) if len(volumes) >= 20 else float(volumes.mean())
        
        indicators = TechnicalIndicators(
            rsi=rsi,
            macd=macd,
            macd_signal=macd_signal,
            bollinger_upper=bollinger_upper,
            bollinger_lower=bollinger_lower,
            bollinger_middle=bollinger_middle,
            sma_20=moving_averages['sma_20'],
            sma_50=moving_averages['sma_50'],
            ema_12=moving_averages['ema_12'],
            ema_26=moving_averages['ema_26'],
            volume_sma=volume_sma,
            price=current_price,
            timestamp=datetime.now()
        )
        
        # Calcula score técnico (-1 a 1)
        technical_score = self._calculate_technical_score(indicators)
        
        logger.info(f"Score técnico: {technical_score:.3f}")
        logger.info(f"RSI: {rsi:.1f}, MACD: {macd:.2f}, Preço vs Bollinger: {self._get_bollinger_position(indicators)}")
        
        return technical_score, indicators
    
    def _calculate_technical_score(self, indicators: TechnicalIndicators) -> float:
        """Calcula score técnico baseado nos indicadores"""
        
        scores = []
        
        # RSI Score (-1 a 1)
        if indicators.rsi > 70:
            rsi_score = -1.0  # Sobrecomprado
        elif indicators.rsi < 30:
            rsi_score = 1.0   # Sobrevendido
        else:
            # Normaliza RSI de 30-70 para -0.5 a 0.5
            rsi_score = (indicators.rsi - 50) / 50
        scores.append(rsi_score * 0.3)  # 30% peso
        
        # MACD Score
        macd_score = 1.0 if indicators.macd > indicators.macd_signal else -1.0
        scores.append(macd_score * 0.2)  # 20% peso
        
        # Bollinger Bands Score
        if indicators.price > indicators.bollinger_upper:
            bollinger_score = -0.8  # Próximo ao topo
        elif indicators.price < indicators.bollinger_lower:
            bollinger_score = 0.8   # Próximo ao fundo
        else:
            # Posição dentro das bandas
            band_range = indicators.bollinger_upper - indicators.bollinger_lower
            position = (indicators.price - indicators.bollinger_middle) / (band_range / 2)
            bollinger_score = -position * 0.5  # Inverte: preço alto = score baixo
        scores.append(bollinger_score * 0.25)  # 25% peso
        
        # Moving Average Score
        ma_score = 0.0
        if indicators.price > indicators.sma_20 > indicators.sma_50:
            ma_score = 0.8  # Tendência de alta
        elif indicators.price < indicators.sma_20 < indicators.sma_50:
            ma_score = -0.8  # Tendência de baixa
        elif indicators.price > indicators.sma_20:
            ma_score = 0.3  # Acima da média de curto prazo
        elif indicators.price < indicators.sma_20:
            ma_score = -0.3  # Abaixo da média de curto prazo
        scores.append(ma_score * 0.25)  # 25% peso
        
        total_score = sum(scores)
        return max(-1.0, min(1.0, total_score))  # Clamp entre -1 e 1
    
    def _get_bollinger_position(self, indicators: TechnicalIndicators) -> str:
        """Retorna posição do preço em relação às Bollinger Bands"""
        if indicators.price > indicators.bollinger_upper:
            return "Acima da banda superior"
        elif indicators.price < indicators.bollinger_lower:
            return "Abaixo da banda inferior"
        else:
            return "Dentro das bandas"
    
    def generate_trading_signal(self, 
                              sentiment_score: float,
                              technical_score: float,
                              indicators: TechnicalIndicators) -> TradingSignal:
        """Gera sinal de trading combinando sentimento e análise técnica"""
        
        # Score combinado ponderado
        combined_score = (sentiment_score * self.sentiment_weight + 
                         technical_score * self.technical_weight)
        
        # Calcula confiança baseada na concordância entre sinais
        agreement = 1.0 - abs(sentiment_score - technical_score) / 2.0
        base_confidence = abs(combined_score)
        confidence = (base_confidence + agreement) / 2.0
        
        # Determina sinal
        reasoning = []
        
        if combined_score > 0.6 and confidence > self.min_confidence:
            signal = SignalType.STRONG_BUY
            reasoning.append(f"Score combinado muito positivo: {combined_score:.3f}")
        elif combined_score > 0.2 and confidence > self.min_confidence:
            signal = SignalType.BUY
            reasoning.append(f"Score combinado positivo: {combined_score:.3f}")
        elif combined_score < -0.6 and confidence > self.min_confidence:
            signal = SignalType.STRONG_SELL
            reasoning.append(f"Score combinado muito negativo: {combined_score:.3f}")
        elif combined_score < -0.2 and confidence > self.min_confidence:
            signal = SignalType.SELL
            reasoning.append(f"Score combinado negativo: {combined_score:.3f}")
        else:
            signal = SignalType.HOLD
            reasoning.append(f"Score neutro ou baixa confiança: {combined_score:.3f} (conf: {confidence:.3f})")
        
        # Adiciona detalhes do raciocínio
        if sentiment_score > 0.3:
            reasoning.append(f"Sentimento positivo: {sentiment_score:.3f}")
        elif sentiment_score < -0.3:
            reasoning.append(f"Sentimento negativo: {sentiment_score:.3f}")
        
        if technical_score > 0.3:
            reasoning.append(f"Indicadores técnicos positivos: {technical_score:.3f}")
        elif technical_score < -0.3:
            reasoning.append(f"Indicadores técnicos negativos: {technical_score:.3f}")
        
        # Adiciona detalhes específicos dos indicadores
        if indicators.rsi > 70:
            reasoning.append(f"RSI sobrecomprado: {indicators.rsi:.1f}")
        elif indicators.rsi < 30:
            reasoning.append(f"RSI sobrevendido: {indicators.rsi:.1f}")
        
        if indicators.macd > indicators.macd_signal:
            reasoning.append("MACD acima da linha de sinal")
        else:
            reasoning.append("MACD abaixo da linha de sinal")
        
        reasoning.append(f"Preço: ${indicators.price:.2f} ({self._get_bollinger_position(indicators)})")
        
        return TradingSignal(
            signal=signal,
            confidence=confidence,
            sentiment_score=sentiment_score,
            technical_score=technical_score,
            combined_score=combined_score,
            reasoning=reasoning,
            timestamp=datetime.now(),
            price=indicators.price
        )
    
    def run_analysis(self, hours_back: int = 24) -> TradingSignal:
        """Executa análise completa e gera sinal de trading"""
        
        logger.info("=== Iniciando Análise Completa ===")
        
        # 1. Análise de Sentimento
        sentiment_score, sentiment_results = self.analyze_sentiment(hours_back)
        
        # 2. Gera dados de preço (simulados para teste)
        price_data = self.price_simulator.generate_realistic_price_data(hours=hours_back * 2)
        
        # 3. Análise Técnica
        technical_score, indicators = self.analyze_technical_indicators(price_data)
        
        # 4. Gera Sinal
        signal = self.generate_trading_signal(sentiment_score, technical_score, indicators)
        
        logger.info(f"=== Sinal Gerado: {signal.signal.value} ===")
        logger.info(f"Confiança: {signal.confidence:.3f}")
        logger.info(f"Preço atual: ${signal.price:.2f}")
        
        return signal
    
    def backtest_strategy(self, days: int = 30) -> Dict:
        """Executa backtest da estratégia"""
        
        logger.info(f"Iniciando backtest de {days} dias")
        
        # Gera dados históricos
        price_data = self.price_simulator.generate_realistic_price_data(hours=days * 24)
        
        signals = []
        portfolio_value = 10000.0  # $10k inicial
        btc_holdings = 0.0
        cash = portfolio_value
        trades = []
        
        # Simula sinais a cada 6 horas
        for i in range(0, len(price_data), 6):
            if i + 24 > len(price_data):  # Precisa de pelo menos 24h de dados
                break
            
            # Dados até o momento atual
            current_data = price_data.iloc[:i+24]
            current_price = current_data['price'].iloc[-1]
            
            # Simula análise de sentimento (aleatória para backtest)
            sentiment_score = np.random.normal(0, 0.3)
            sentiment_score = max(-1.0, min(1.0, sentiment_score))
            
            # Análise técnica real
            technical_score, indicators = self.analyze_technical_indicators(current_data)
            
            # Gera sinal
            signal = self.generate_trading_signal(sentiment_score, technical_score, indicators)
            signal.price = current_price
            signals.append(signal)
            
            # Executa trade baseado no sinal
            if signal.signal in [SignalType.STRONG_BUY, SignalType.BUY] and signal.confidence > self.min_confidence:
                if cash > 100:  # Mínimo para comprar
                    btc_to_buy = cash * 0.5 / current_price  # Compra 50% do cash
                    btc_holdings += btc_to_buy
                    cash -= btc_to_buy * current_price
                    trades.append({
                        'type': 'BUY',
                        'price': current_price,
                        'amount': btc_to_buy,
                        'timestamp': current_data.index[-1],
                        'signal': signal.signal.value
                    })
            
            elif signal.signal in [SignalType.STRONG_SELL, SignalType.SELL] and signal.confidence > self.min_confidence:
                if btc_holdings > 0.001:  # Mínimo para vender
                    btc_to_sell = btc_holdings * 0.5  # Vende 50% do BTC
                    btc_holdings -= btc_to_sell
                    cash += btc_to_sell * current_price
                    trades.append({
                        'type': 'SELL',
                        'price': current_price,
                        'amount': btc_to_sell,
                        'timestamp': current_data.index[-1],
                        'signal': signal.signal.value
                    })
        
        # Calcula performance final
        final_price = price_data['price'].iloc[-1]
        final_portfolio_value = cash + (btc_holdings * final_price)
        total_return = (final_portfolio_value - portfolio_value) / portfolio_value
        
        # Calcula buy and hold return
        initial_price = price_data['price'].iloc[0]
        buy_hold_return = (final_price - initial_price) / initial_price
        
        results = {
            'initial_value': portfolio_value,
            'final_value': final_portfolio_value,
            'total_return': total_return,
            'buy_hold_return': buy_hold_return,
            'outperformance': total_return - buy_hold_return,
            'num_trades': len(trades),
            'num_signals': len(signals),
            'trades': trades,
            'signals': [s.to_dict() for s in signals[-10:]]  # Últimos 10 sinais
        }
        
        logger.info(f"Backtest concluído:")
        logger.info(f"- Retorno da estratégia: {total_return:.2%}")
        logger.info(f"- Retorno buy & hold: {buy_hold_return:.2%}")
        logger.info(f"- Outperformance: {(total_return - buy_hold_return):.2%}")
        logger.info(f"- Número de trades: {len(trades)}")
        
        return results

def main():
    """Função principal para demonstração"""
    
    print("=== Sistema de Trading Bitcoin com Análise de Sentimento ===\n")
    
    # Inicializa algoritmo
    algorithm = BitcoinTradingAlgorithm(
        sentiment_weight=0.4,
        technical_weight=0.6,
        min_confidence=0.6
    )
    
    # Executa análise atual
    print("1. Executando análise atual...")
    current_signal = algorithm.run_analysis(hours_back=24)
    
    print(f"\n📊 SINAL ATUAL: {current_signal.signal.value}")
    print(f"💪 Confiança: {current_signal.confidence:.1%}")
    print(f"💰 Preço: ${current_signal.price:.2f}")
    print(f"📈 Score Sentimento: {current_signal.sentiment_score:.3f}")
    print(f"📉 Score Técnico: {current_signal.technical_score:.3f}")
    print(f"⚖️ Score Combinado: {current_signal.combined_score:.3f}")
    
    print(f"\n🧠 Raciocínio:")
    for reason in current_signal.reasoning:
        print(f"  • {reason}")
    
    # Salva sinal atual
    with open('current_signal.json', 'w') as f:
        json.dump(current_signal.to_dict(), f, indent=2)
    print(f"\n💾 Sinal salvo em current_signal.json")
    
    # Executa backtest
    print(f"\n2. Executando backtest de 30 dias...")
    backtest_results = algorithm.backtest_strategy(days=30)
    
    print(f"\n📈 RESULTADOS DO BACKTEST:")
    print(f"💵 Valor inicial: ${backtest_results['initial_value']:,.2f}")
    print(f"💵 Valor final: ${backtest_results['final_value']:,.2f}")
    print(f"📊 Retorno estratégia: {backtest_results['total_return']:.2%}")
    print(f"📊 Retorno buy & hold: {backtest_results['buy_hold_return']:.2%}")
    print(f"🎯 Outperformance: {backtest_results['outperformance']:.2%}")
    print(f"🔄 Número de trades: {backtest_results['num_trades']}")
    
    # Salva resultados do backtest
    with open('backtest_results.json', 'w') as f:
        json.dump(backtest_results, f, indent=2, default=str)
    print(f"\n💾 Resultados do backtest salvos em backtest_results.json")
    
    print(f"\n✅ Análise completa finalizada!")

if __name__ == "__main__":
    main()

