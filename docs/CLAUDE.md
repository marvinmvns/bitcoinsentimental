# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive Bitcoin Trading System that combines sentiment analysis using Ollama LLM with technical analysis to generate trading signals. The system includes:

- **Sentiment Analysis**: Uses local Ollama LLM models (llama3.2:1b, gemma2:9b, deepseek-r1:7b) combined with traditional sentiment analysis (VADER, TextBlob)
- **Technical Analysis**: Implements RSI, MACD, Bollinger Bands, and moving averages
- **Trading System**: Generates buy/sell/hold signals with confidence scoring
- **Reddit Data Collection**: Collects sentiment data from Bitcoin-related subreddits
- **CLI Interface**: Full command-line interface for all operations
- **Containerization**: Docker and Docker Compose support for deployment

## Architecture

### Core Components

1. **Sentiment Analysis Pipeline**:
   - `sentiment_analyzer.py`: Main sentiment analysis orchestrator
   - `ollama_sentiment_analyzer.py`: Ollama LLM integration
   - `enhanced_sentiment_analyzer.py`: Enhanced multi-model sentiment analysis
   - `reddit_collector.py`: Reddit data collection

2. **Trading System**:
   - `bitcoin_trading_algorithm.py`: Core trading algorithm
   - `bitcoin_trading_system_with_ollama.py`: Integrated system with Ollama
   - Technical indicators and signal generation

3. **User Interfaces**:
   - `btc_trading_cli.py`: Full-featured CLI application
   - `main_demo.py`: Demonstration script showing all features

4. **Testing & Benchmarking**:
   - `sentiment_benchmark.py`: Model performance benchmarking
   - `test_ollama_simple.py`: Basic Ollama functionality tests

### Dependencies

**Python Requirements** (from requirements.txt):
- **LLM & NLP**: langchain==0.3.27, langchain-community==0.3.27, langchain-core==0.3.72
- **Sentiment Analysis**: vaderSentiment==3.3.2, textblob==0.17.1
- **Data Analysis**: numpy==1.24.3, pandas==2.0.3, scipy==1.11.1
- **Visualization**: matplotlib==3.7.2, seaborn==0.12.2, plotly==5.15.0
- **Financial Data**: yfinance==0.2.18, ccxt==4.0.77
- **Testing**: pytest==7.4.0, pytest-asyncio==0.21.1
- **CLI**: click==8.1.6, rich==13.5.2

**External Dependencies**:
- **Ollama**: Local LLM server (http://localhost:11434)
- **Python 3.11**: Required Python version
- **Docker**: For containerized deployment

## Common Development Tasks

### Installation & Setup

```bash
# Full system installation (requires sudo)
chmod +x scripts/install_system.sh && ./scripts/install_system.sh

# Minimal installation for development
chmod +x scripts/install_minimal.sh && ./scripts/install_minimal.sh

# CLI setup only
chmod +x scripts/setup_cli.sh && ./scripts/setup_cli.sh

# Python setup (configure paths)
python setup.py

# Install Python dependencies
pip install -r requirements.txt
```

### Running the System

```bash
# Run complete demonstration
python examples/main_demo.py

# Start integrated trading system
python src/trading/bitcoin_trading_system_with_ollama.py

# Use CLI interface
python src/cli/btc_trading_cli.py --help
```

### CLI Commands

The system provides a comprehensive CLI (`btc_trading_cli.py`):

```bash
# System status and configuration
btc-trading system status
btc-trading config show
btc-trading config set min_confidence 0.75

# Sentiment analysis
btc-trading sentiment analyze "Bitcoin is going to the moon!"
btc-trading sentiment batch input_file.txt --format json

# Trading operations
btc-trading trading backtest --days 7 --capital 10000
btc-trading trading live --dry-run --duration 60

# Benchmarking
btc-trading benchmark models --models llama3.2:1b gemma2:9b
```

### Testing and Linting

```bash
# Run sentiment benchmarks
python src/core/sentiment_benchmark.py

# Test Ollama integration  
python src/core/test_ollama_simple.py

# CLI-based model benchmarking
python src/cli/btc_trading_cli.py benchmark models

# Run all tests (if pytest is configured)
pytest

# Code formatting and linting
black src/ --check  # Check formatting
flake8 src/        # Lint code
```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose -f docker/docker-compose.yml up -d

# Build standalone Docker image
docker build -f docker/Dockerfile -t bitcoin-trading-system .

# Run with specific configuration
docker run -p 8080:8080 -p 11434:11434 bitcoin-trading-system
```

## Code Architecture Details

### Sentiment Analysis Flow

1. **Text Input** → `enhanced_sentiment_analyzer.py`
2. **Multi-Model Analysis**:
   - Ollama LLM (primary, 60% weight)
   - VADER Sentiment (25% weight)  
   - TextBlob (15% weight)
3. **Weighted Scoring** → Final sentiment score (-1.0 to +1.0)

### Trading Signal Generation

1. **Data Collection**: Market prices + Reddit sentiment data
2. **Technical Analysis**: RSI, MACD, Bollinger Bands calculations
3. **Sentiment Analysis**: Multi-model text analysis
4. **Signal Fusion**: 60% technical + 40% sentiment
5. **Decision**: STRONG_BUY/BUY/HOLD/SELL/STRONG_SELL

### Configuration

The system uses JSON configuration files with the following key settings:

- **Ollama Models**: Primary (llama3.2:1b), Backup (gemma2:9b), Specialized (deepseek-r1:7b)
- **Trading Parameters**: min_confidence=0.6, position_size=0.1, stop_loss=0.05
- **Technical Indicators**: RSI period=14, MACD fast/slow=12/26, BB period=20
- **Data Collection**: 8 subreddits, 300s interval, 24h lookback

## File Organization

The project is properly organized with the following structure:

```
/
├── src/                     # Core source code
│   ├── sentiment/          # Sentiment analysis modules
│   │   ├── sentiment_analyzer.py
│   │   ├── enhanced_sentiment_analyzer.py
│   │   └── ollama_sentiment_analyzer.py
│   ├── trading/            # Trading algorithms
│   │   ├── bitcoin_trading_algorithm.py
│   │   └── bitcoin_trading_system_with_ollama.py
│   ├── data/               # Data collection
│   │   └── reddit_collector.py
│   ├── cli/                # CLI interface
│   │   └── btc_trading_cli.py
│   ├── core/               # Core testing and benchmarking
│   │   ├── sentiment_benchmark.py
│   │   └── test_ollama_simple.py
│   └── utils/              # Utilities
├── scripts/                # Installation/setup scripts
│   ├── install_system.sh
│   ├── install_minimal.sh
│   ├── setup_cli.sh
│   ├── cli_demo.sh
│   └── docker_manager.sh
├── docker/                 # Docker configuration
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── supervisord.conf
├── docs/                   # Documentation
│   ├── CLAUDE.md
│   └── [various .md files]
├── examples/               # Example usage
│   └── main_demo.py
├── tests/                  # Test files (empty)
├── config/                 # Configuration files (empty)
└── requirements.txt        # Python dependencies
```

## Important Notes

### Security Considerations
- Never include API keys or credentials in code
- Use environment variables for sensitive configuration
- The system includes defensive security measures for sentiment analysis only

### Performance
- Ollama models require significant memory (4GB+ recommended)
- Batch processing is more efficient than individual analysis
- Consider model size vs accuracy tradeoffs (1b vs 9b models)

### Monitoring
- System includes Prometheus metrics integration
- Logs are stored in `/opt/bitcoin-trading-system/logs/`
- Health checks available for all services

### Dependencies Management
- Pin all dependency versions for reproducibility
- Test with multiple Python versions if needed
- Ollama server must be running on localhost:11434

## Troubleshooting

### Common Issues
1. **Ollama not responding**: Check `curl http://localhost:11434/api/tags`
2. **Model not found**: Run `ollama pull llama3.2:1b`
3. **Memory issues**: Reduce batch sizes or use smaller models
4. **Import errors**: Ensure virtual environment is activated and run `python setup.py`
5. **Script permissions**: Run `chmod +x scripts/*.sh` for all shell scripts
6. **CLI not found**: Ensure you're running from project root directory

### Performance Optimization
- Use smaller models (1b) for development
- Implement request batching for sentiment analysis
- Cache sentiment results for repeated texts
- Monitor memory usage during backtests

## Development Workflow

1. **Setup**: Run `install_minimal.sh` for development environment
2. **Testing**: Use `main_demo.py` to verify all components work
3. **Development**: Modify individual modules, test with CLI
4. **Integration**: Test full system with `bitcoin_trading_system_with_ollama.py`
5. **Deployment**: Use Docker Compose for production deployment