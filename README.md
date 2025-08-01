# Bitcoin Trading System with Ollama LLM

A comprehensive Bitcoin trading system that combines sentiment analysis using local Ollama LLM models with technical analysis to generate intelligent trading signals.

## 🚀 Features

- **Multi-Model Sentiment Analysis**: Uses Ollama LLM (llama3.2:1b, gemma2:9b, deepseek-r1:7b) combined with VADER and TextBlob
- **Technical Analysis**: RSI, MACD, Bollinger Bands, and moving averages
- **Reddit Data Collection**: Automated sentiment data collection from Bitcoin-related subreddits
- **CLI Interface**: Comprehensive command-line interface for all operations
- **Docker Support**: Full containerization with Docker Compose
- **Backtesting**: Historical performance testing with detailed metrics
- **Real-time Trading**: Live trading capabilities with risk management

## 📁 Project Structure

```
├── src/                          # Source code
│   ├── sentiment/               # Sentiment analysis modules
│   │   ├── sentiment_analyzer.py
│   │   ├── enhanced_sentiment_analyzer.py
│   │   └── ollama_sentiment_analyzer.py
│   ├── trading/                 # Trading algorithms
│   │   ├── bitcoin_trading_algorithm.py
│   │   └── bitcoin_trading_system_with_ollama.py
│   ├── data/                    # Data collection
│   │   └── reddit_collector.py
│   ├── cli/                     # Command-line interface
│   │   └── btc_trading_cli.py
│   ├── core/                    # Core testing and benchmarking
│   │   ├── sentiment_benchmark.py
│   │   └── test_ollama_simple.py
│   └── utils/                   # Utilities (to be added)
├── scripts/                      # Installation and setup scripts
│   ├── install_system.sh       # Full system installation
│   ├── install_minimal.sh      # Minimal installation
│   ├── setup_cli.sh            # CLI setup
│   ├── cli_demo.sh             # CLI demonstration
│   └── docker_manager.sh       # Docker management
├── docker/                      # Docker configuration
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── supervisord.conf
├── docs/                        # Documentation
│   ├── CLAUDE.md               # Development guidance
│   └── *.md                    # Technical documentation
├── examples/                    # Example usage
│   └── main_demo.py            # Complete system demonstration
├── tests/                       # Test files (to be added)
├── config/                      # Configuration files (to be added)
└── requirements.txt             # Python dependencies
```

## 🛠️ Installation

### Quick Start (Recommended)

```bash
# Full system installation with Ollama and all dependencies
chmod +x scripts/install_system.sh
./scripts/install_system.sh
```

### Minimal Installation (Development)

```bash
# For development and testing
chmod +x scripts/install_minimal.sh
./scripts/install_minimal.sh
```

### Docker Installation

```bash
# Using Docker Compose
docker-compose -f docker/docker-compose.yml up -d
```

## 🎯 Usage

### Command Line Interface

```bash
# Run the CLI
python src/cli/btc_trading_cli.py --help

# Analyze sentiment
python src/cli/btc_trading_cli.py sentiment analyze "Bitcoin is going to the moon!"

# Run backtest
python src/cli/btc_trading_cli.py trading backtest --days 7 --capital 10000

# Check system status
python src/cli/btc_trading_cli.py system status
```

### Complete Demonstration

```bash
# Run comprehensive demo showing all features
python examples/main_demo.py
```

### CLI Demo

```bash
# Interactive CLI demonstration
./scripts/cli_demo.sh
```

## 📊 Core Components

### Sentiment Analysis
- **Ollama Integration**: Local LLM models for advanced sentiment analysis
- **Traditional Methods**: VADER and TextBlob for baseline comparison
- **Weighted Scoring**: 60% Ollama, 25% VADER, 15% TextBlob

### Trading System
- **Signal Generation**: STRONG_BUY/BUY/HOLD/SELL/STRONG_SELL
- **Technical Indicators**: RSI, MACD, Bollinger Bands, Moving Averages
- **Risk Management**: Position sizing, stop-loss, take-profit
- **Confidence Scoring**: Only trade when confidence > threshold

### Data Collection
- **Reddit Integration**: Automated collection from Bitcoin subreddits
- **Real-time Processing**: Continuous sentiment monitoring
- **Trend Analysis**: Identification of emerging topics

## ⚙️ Configuration

Key configuration parameters:

- **Ollama Models**: Primary (llama3.2:1b), Backup (gemma2:9b), Specialized (deepseek-r1:7b)
- **Trading**: min_confidence=0.6, position_size=0.1, stop_loss=0.05
- **Technical**: RSI period=14, MACD=(12,26,9), BB period=20
- **Data**: 8 subreddits, 5min intervals, 24h lookback

## 🧪 Testing

```bash
# Run sentiment benchmarks
python src/core/sentiment_benchmark.py

# Test Ollama integration
python src/core/test_ollama_simple.py

# CLI benchmark
python src/cli/btc_trading_cli.py benchmark models
```

## 🐳 Docker Deployment

```bash
# Build and run
cd docker/
docker-compose up -d

# View logs
docker-compose logs -f bitcoin-trading

# Stop services
docker-compose down
```

## 📈 Performance

- **Sentiment Analysis**: ~1s per text with Ollama models
- **Trading Signals**: Generated every 5 minutes
- **Backtesting**: Historical analysis up to 30 days
- **Memory Usage**: ~4GB RAM recommended for Ollama

## 🛡️ Security

- **Defensive Focus**: Only defensive security analysis
- **No API Keys**: Uses local models and public data
- **Risk Management**: Built-in position limits and stop-losses
- **Environment Variables**: Secure configuration management

## 🤝 Contributing

1. Follow the organized project structure
2. Add tests for new features
3. Update documentation
4. Use the CLI for testing changes

## 📄 License

This project is for educational and research purposes. Use at your own risk for actual trading.

## ⚠️ Disclaimer

This system is for educational purposes only. Cryptocurrency trading involves significant risk. Never trade with money you cannot afford to lose. Always test thoroughly before using real funds.

## 🔗 Documentation

- See `docs/CLAUDE.md` for development guidance
- Check `docs/` folder for technical documentation
- Run `python src/cli/btc_trading_cli.py --help` for CLI usage