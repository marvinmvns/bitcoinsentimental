#!/usr/bin/env python3
"""
Sistema Integrado de Trading Bitcoin com Ollama LLM
Combina análise de sentimento avançada com indicadores técnicos
"""

import json
import time
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict

# Importar módulos existentes e novos
try:
    from ..sentiment.enhanced_sentiment_analyzer import EnhancedSentimentAnalyzer, EnhancedSentimentResult
    OLLAMA_AVAILABLE = True
except ImportError:
    print("⚠️  Ollama não disponível, usando análise tradicional")
    OLLAMA_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TradingSignal:
    """Sinal de trading gerado pelo sistema"""
    timestamp: str
    signal_type: str  # STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL
    confidence: float  # 0.0 a 1.0
    price: float
    
    # Componentes do sinal
    sentiment_score: float
    sentiment_confidence: float
    technical_score: float
    
    # Detalhes técnicos
    rsi: float
    macd_signal: str
    bb_position: str
    
    # Metadados
    reasoning: str
    model_used: str

@dataclass
class BacktestResult:
    """Resultado de backtest"""
    initial_capital: float
    final_capital: float
    total_return: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    max_drawdown: float
    sharpe_ratio: float
    trades: List[Dict]

class BitcoinTradingSystemWithOllama:
    """Sistema de trading Bitcoin integrado com Ollama LLM"""
    
    def __init__(self, initial_capital: float = 10000.0):
        """
        Inicializa o sistema de trading
        
        Args:
            initial_capital: Capital inicial para trading
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.position = 0.0  # Quantidade de Bitcoin
        self.trades = []
        
        # Inicializar analisador de sentimento
        if OLLAMA_AVAILABLE:
            try:
                self.sentiment_analyzer = EnhancedSentimentAnalyzer()
                logger.info("✅ Analisador Ollama inicializado")
            except Exception as e:
                logger.error(f"❌ Erro ao inicializar Ollama: {e}")
                self.sentiment_analyzer = None
        else:
            self.sentiment_analyzer = None
        
        # Configurações de trading
        self.min_confidence = 0.6  # Confiança mínima para trading
        self.position_size = 0.1   # 10% do capital por trade
        self.stop_loss = 0.05      # 5% stop loss
        self.take_profit = 0.15    # 15% take profit
        
        logger.info(f"🚀 Sistema de trading inicializado com ${initial_capital:,.2f}")
    
    def get_bitcoin_price(self) -> float:
        """
        Obtém preço atual do Bitcoin (simulado)
        Em produção, conectaria a uma API real
        """
        # Simulação de preço baseada em timestamp
        base_price = 45000
        variation = np.sin(time.time() / 1000) * 5000
        noise = np.random.normal(0, 1000)
        return max(1000, base_price + variation + noise)
    
    def calculate_technical_indicators(self, prices: List[float]) -> Dict:
        """
        Calcula indicadores técnicos
        
        Args:
            prices: Lista de preços históricos
            
        Returns:
            Dict com indicadores calculados
        """
        if len(prices) < 20:
            return {
                'rsi': 50.0,
                'macd_signal': 'NEUTRAL',
                'bb_position': 'MIDDLE',
                'sma_20': prices[-1] if prices else 45000,
                'sma_50': prices[-1] if prices else 45000
            }
        
        prices_array = np.array(prices)
        
        # RSI (14 períodos)
        def calculate_rsi(prices, period=14):
            deltas = np.diff(prices)
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            avg_gain = np.mean(gains[-period:])
            avg_loss = np.mean(losses[-period:])
            
            if avg_loss == 0:
                return 100
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        
        # MACD
        def calculate_macd(prices):
            ema_12 = pd.Series(prices).ewm(span=12).mean().iloc[-1]
            ema_26 = pd.Series(prices).ewm(span=26).mean().iloc[-1]
            macd_line = ema_12 - ema_26
            
            if macd_line > 0:
                return 'BULLISH'
            elif macd_line < 0:
                return 'BEARISH'
            else:
                return 'NEUTRAL'
        
        # Bollinger Bands
        def calculate_bb_position(prices, period=20):
            sma = np.mean(prices[-period:])
            std = np.std(prices[-period:])
            upper_band = sma + (2 * std)
            lower_band = sma - (2 * std)
            current_price = prices[-1]
            
            if current_price > upper_band:
                return 'UPPER'
            elif current_price < lower_band:
                return 'LOWER'
            else:
                return 'MIDDLE'
        
        # Médias móveis
        sma_20 = np.mean(prices[-20:])
        sma_50 = np.mean(prices[-50:]) if len(prices) >= 50 else sma_20
        
        return {
            'rsi': calculate_rsi(prices),
            'macd_signal': calculate_macd(prices),
            'bb_position': calculate_bb_position(prices),
            'sma_20': sma_20,
            'sma_50': sma_50
        }
    
    def calculate_technical_score(self, indicators: Dict) -> float:
        """
        Calcula score técnico baseado nos indicadores
        
        Returns:
            Score de -1.0 (muito bearish) a +1.0 (muito bullish)
        """
        score = 0.0
        
        # RSI (peso: 30%)
        rsi = indicators['rsi']
        if rsi < 30:
            score += 0.3  # Oversold - bullish
        elif rsi > 70:
            score -= 0.3  # Overbought - bearish
        else:
            score += (50 - rsi) / 50 * 0.1  # Tendência para o meio
        
        # MACD (peso: 25%)
        macd_signal = indicators['macd_signal']
        if macd_signal == 'BULLISH':
            score += 0.25
        elif macd_signal == 'BEARISH':
            score -= 0.25
        
        # Bollinger Bands (peso: 20%)
        bb_position = indicators['bb_position']
        if bb_position == 'LOWER':
            score += 0.2  # Oversold
        elif bb_position == 'UPPER':
            score -= 0.2  # Overbought
        
        # Médias móveis (peso: 25%)
        sma_20 = indicators['sma_20']
        sma_50 = indicators['sma_50']
        if sma_20 > sma_50:
            score += 0.25  # Tendência de alta
        else:
            score -= 0.25  # Tendência de baixa
        
        return max(-1.0, min(1.0, score))
    
    def analyze_market_sentiment(self, news_texts: List[str]) -> Tuple[float, float, str]:
        """
        Analisa sentimento do mercado usando Ollama LLM
        
        Args:
            news_texts: Lista de textos para análise
            
        Returns:
            Tuple[sentiment_score, confidence, model_used]
        """
        if not self.sentiment_analyzer or not news_texts:
            return 0.0, 0.0, "none"
        
        try:
            # Analisar todos os textos
            results = self.sentiment_analyzer.analyze_batch(news_texts)
            
            if not results:
                return 0.0, 0.0, "none"
            
            # Calcular médias ponderadas pela confiança
            total_weighted_score = 0.0
            total_weight = 0.0
            model_used = results[0].models_used[0] if results[0].models_used else "unknown"
            
            for result in results:
                weight = result.ollama_confidence
                total_weighted_score += result.ollama_score * weight
                total_weight += weight
            
            if total_weight == 0:
                return 0.0, 0.0, model_used
            
            avg_score = total_weighted_score / total_weight
            avg_confidence = total_weight / len(results)
            
            logger.info(f"📊 Sentimento: {avg_score:.2f} (conf: {avg_confidence:.2f}) - {len(results)} textos")
            
            return avg_score, avg_confidence, model_used
            
        except Exception as e:
            logger.error(f"❌ Erro na análise de sentimento: {e}")
            return 0.0, 0.0, "error"
    
    def generate_trading_signal(self, price: float, prices_history: List[float], 
                              news_texts: List[str]) -> TradingSignal:
        """
        Gera sinal de trading baseado em análise técnica e sentimento
        
        Args:
            price: Preço atual
            prices_history: Histórico de preços
            news_texts: Textos para análise de sentimento
            
        Returns:
            TradingSignal com recomendação
        """
        # Análise técnica
        indicators = self.calculate_technical_indicators(prices_history)
        technical_score = self.calculate_technical_score(indicators)
        
        # Análise de sentimento
        sentiment_score, sentiment_confidence, model_used = self.analyze_market_sentiment(news_texts)
        
        # Combinar scores (60% técnico, 40% sentimento)
        if sentiment_confidence > 0.3:  # Usar sentimento apenas se confiança > 30%
            combined_score = (technical_score * 0.6) + (sentiment_score * 0.4)
            final_confidence = (0.8 + sentiment_confidence) / 2  # Confiança base + sentimento
        else:
            combined_score = technical_score
            final_confidence = 0.6  # Confiança apenas técnica
        
        # Determinar tipo de sinal
        if combined_score > 0.6 and final_confidence > self.min_confidence:
            signal_type = "STRONG_BUY"
        elif combined_score > 0.3 and final_confidence > self.min_confidence:
            signal_type = "BUY"
        elif combined_score < -0.6 and final_confidence > self.min_confidence:
            signal_type = "STRONG_SELL"
        elif combined_score < -0.3 and final_confidence > self.min_confidence:
            signal_type = "SELL"
        else:
            signal_type = "HOLD"
        
        # Criar reasoning
        reasoning_parts = []
        reasoning_parts.append(f"Técnico: {technical_score:.2f}")
        reasoning_parts.append(f"RSI: {indicators['rsi']:.1f}")
        reasoning_parts.append(f"MACD: {indicators['macd_signal']}")
        reasoning_parts.append(f"BB: {indicators['bb_position']}")
        
        if sentiment_confidence > 0.3:
            reasoning_parts.append(f"Sentimento: {sentiment_score:.2f} (conf: {sentiment_confidence:.2f})")
        
        reasoning = " | ".join(reasoning_parts)
        
        return TradingSignal(
            timestamp=datetime.now().isoformat(),
            signal_type=signal_type,
            confidence=final_confidence,
            price=price,
            sentiment_score=sentiment_score,
            sentiment_confidence=sentiment_confidence,
            technical_score=technical_score,
            rsi=indicators['rsi'],
            macd_signal=indicators['macd_signal'],
            bb_position=indicators['bb_position'],
            reasoning=reasoning,
            model_used=model_used
        )
    
    def execute_trade(self, signal: TradingSignal) -> Optional[Dict]:
        """
        Executa trade baseado no sinal
        
        Args:
            signal: Sinal de trading
            
        Returns:
            Dict com detalhes do trade ou None se não executado
        """
        if signal.signal_type == "HOLD":
            return None
        
        trade_amount = self.current_capital * self.position_size
        
        if signal.signal_type in ["BUY", "STRONG_BUY"] and self.position == 0:
            # Comprar Bitcoin
            btc_amount = trade_amount / signal.price
            self.position = btc_amount
            self.current_capital -= trade_amount
            
            trade = {
                'timestamp': signal.timestamp,
                'type': 'BUY',
                'price': signal.price,
                'amount': btc_amount,
                'value': trade_amount,
                'signal_type': signal.signal_type,
                'confidence': signal.confidence,
                'reasoning': signal.reasoning
            }
            
            self.trades.append(trade)
            logger.info(f"🟢 COMPRA: {btc_amount:.6f} BTC @ ${signal.price:,.2f} (conf: {signal.confidence:.2f})")
            return trade
            
        elif signal.signal_type in ["SELL", "STRONG_SELL"] and self.position > 0:
            # Vender Bitcoin
            trade_value = self.position * signal.price
            self.current_capital += trade_value
            
            trade = {
                'timestamp': signal.timestamp,
                'type': 'SELL',
                'price': signal.price,
                'amount': self.position,
                'value': trade_value,
                'signal_type': signal.signal_type,
                'confidence': signal.confidence,
                'reasoning': signal.reasoning
            }
            
            self.trades.append(trade)
            logger.info(f"🔴 VENDA: {self.position:.6f} BTC @ ${signal.price:,.2f} (conf: {signal.confidence:.2f})")
            
            self.position = 0.0
            return trade
        
        return None
    
    def get_portfolio_value(self, current_price: float) -> float:
        """Calcula valor atual do portfólio"""
        return self.current_capital + (self.position * current_price)
    
    def run_simulation(self, days: int = 30, news_frequency: int = 4) -> BacktestResult:
        """
        Executa simulação de trading
        
        Args:
            days: Número de dias para simular
            news_frequency: Número de análises de sentimento por dia
            
        Returns:
            BacktestResult com resultados da simulação
        """
        logger.info(f"🚀 Iniciando simulação de {days} dias...")
        
        prices_history = []
        all_trades = []
        portfolio_values = []
        
        # Gerar dados simulados
        for day in range(days):
            for hour in range(0, 24, 24 // news_frequency):
                # Gerar preço
                price = self.get_bitcoin_price()
                prices_history.append(price)
                
                # Gerar textos de notícias simulados
                news_texts = self._generate_sample_news()
                
                # Gerar sinal
                signal = self.generate_trading_signal(price, prices_history, news_texts)
                
                # Executar trade
                trade = self.execute_trade(signal)
                if trade:
                    all_trades.append(trade)
                
                # Registrar valor do portfólio
                portfolio_value = self.get_portfolio_value(price)
                portfolio_values.append(portfolio_value)
                
                # Log periódico
                if len(prices_history) % 10 == 0:
                    logger.info(f"📊 Dia {day+1}, Preço: ${price:,.2f}, Portfólio: ${portfolio_value:,.2f}, Sinal: {signal.signal_type}")
                
                time.sleep(0.1)  # Simular tempo
        
        # Calcular métricas finais
        final_value = self.get_portfolio_value(prices_history[-1])
        total_return = (final_value - self.initial_capital) / self.initial_capital
        
        # Análise de trades
        winning_trades = len([t for t in all_trades if t['type'] == 'SELL' and self._calculate_trade_profit(t, all_trades) > 0])
        losing_trades = len([t for t in all_trades if t['type'] == 'SELL' and self._calculate_trade_profit(t, all_trades) <= 0])
        win_rate = winning_trades / max(1, winning_trades + losing_trades)
        
        # Drawdown máximo
        max_drawdown = self._calculate_max_drawdown(portfolio_values)
        
        # Sharpe ratio (simplificado)
        returns = np.diff(portfolio_values) / portfolio_values[:-1]
        sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        
        result = BacktestResult(
            initial_capital=self.initial_capital,
            final_capital=final_value,
            total_return=total_return,
            total_trades=len(all_trades),
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            trades=all_trades
        )
        
        self._print_results(result)
        return result
    
    def _generate_sample_news(self) -> List[str]:
        """Gera textos de notícias simulados para teste"""
        positive_news = [
            "Bitcoin breaks new all-time high as institutional adoption accelerates!",
            "Major bank announces Bitcoin treasury allocation, bullish signal for crypto market",
            "Bitcoin network hash rate reaches record levels, showing strong fundamentals",
            "Regulatory clarity boosts Bitcoin confidence among institutional investors"
        ]
        
        negative_news = [
            "Bitcoin faces regulatory pressure as government considers new restrictions",
            "Major exchange hack causes Bitcoin price volatility and investor concerns",
            "Environmental concerns over Bitcoin mining spark debate among policymakers",
            "Market correction hits Bitcoin as investors take profits after recent gains"
        ]
        
        neutral_news = [
            "Bitcoin price consolidates in current range as market awaits next catalyst",
            "Technical analysis shows Bitcoin in sideways trading pattern",
            "Bitcoin trading volume remains steady amid mixed market signals",
            "Cryptocurrency market shows mixed performance across different assets"
        ]
        
        # Selecionar aleatoriamente 2-4 notícias
        import random
        all_news = positive_news + negative_news + neutral_news
        return random.sample(all_news, random.randint(2, 4))
    
    def _calculate_trade_profit(self, sell_trade: Dict, all_trades: List[Dict]) -> float:
        """Calcula lucro de um trade de venda"""
        # Encontrar trade de compra correspondente
        for trade in reversed(all_trades):
            if trade['type'] == 'BUY' and trade['timestamp'] < sell_trade['timestamp']:
                return sell_trade['value'] - trade['value']
        return 0.0
    
    def _calculate_max_drawdown(self, portfolio_values: List[float]) -> float:
        """Calcula drawdown máximo"""
        peak = portfolio_values[0]
        max_dd = 0.0
        
        for value in portfolio_values:
            if value > peak:
                peak = value
            
            drawdown = (peak - value) / peak
            if drawdown > max_dd:
                max_dd = drawdown
        
        return max_dd
    
    def _print_results(self, result: BacktestResult):
        """Imprime resultados da simulação"""
        print("\n" + "="*60)
        print("📊 RESULTADOS DA SIMULAÇÃO DE TRADING")
        print("="*60)
        print(f"💰 Capital Inicial:     ${result.initial_capital:,.2f}")
        print(f"💰 Capital Final:       ${result.final_capital:,.2f}")
        print(f"📈 Retorno Total:       {result.total_return:.2%}")
        print(f"🔄 Total de Trades:     {result.total_trades}")
        print(f"✅ Trades Vencedores:   {result.winning_trades}")
        print(f"❌ Trades Perdedores:   {result.losing_trades}")
        print(f"🎯 Taxa de Acerto:      {result.win_rate:.1%}")
        print(f"📉 Drawdown Máximo:     {result.max_drawdown:.1%}")
        print(f"📊 Sharpe Ratio:        {result.sharpe_ratio:.2f}")
        
        if OLLAMA_AVAILABLE:
            print(f"🤖 Modelo LLM:          Ollama integrado")
        else:
            print(f"🤖 Modelo LLM:          Não disponível")
        
        print("="*60)

def main():
    """Função principal"""
    print("🚀 Sistema de Trading Bitcoin com Ollama LLM")
    print("="*50)
    
    # Inicializar sistema
    trading_system = BitcoinTradingSystemWithOllama(initial_capital=10000.0)
    
    # Executar simulação
    result = trading_system.run_simulation(days=30, news_frequency=4)
    
    # Salvar resultados
    with open('trading_simulation_results.json', 'w') as f:
        json.dump(asdict(result), f, indent=2, default=str)
    
    print("\n💾 Resultados salvos em 'trading_simulation_results.json'")
    
    return result

if __name__ == "__main__":
    main()

