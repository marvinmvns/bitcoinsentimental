#!/usr/bin/env python3
"""
Sistema de Coleta de Dados do Reddit para Análise de Sentimento Bitcoin
Módulo para coletar posts e comentários de subreddits relacionados a Bitcoin
"""

import sys
import json
import time
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

# Adiciona o caminho da API do Manus
sys.path.append('/opt/.manus/.sandbox-runtime')

try:
    from data_api import ApiClient
    MANUS_API_AVAILABLE = True
except ImportError:
    MANUS_API_AVAILABLE = False
    logging.warning("Manus API não disponível, usando dados simulados")

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RedditPost:
    """Estrutura de dados para posts do Reddit"""
    id: str
    title: str
    selftext: str
    author: str
    subreddit: str
    score: int
    num_comments: int
    created_utc: float
    url: str
    permalink: str
    upvote_ratio: Optional[float] = None
    flair_text: Optional[str] = None
    
    @property
    def created_datetime(self) -> datetime:
        """Converte timestamp UTC para datetime"""
        return datetime.fromtimestamp(self.created_utc)
    
    @property
    def full_text(self) -> str:
        """Retorna texto completo (título + conteúdo)"""
        return f"{self.title} {self.selftext}".strip()

@dataclass
class RedditComment:
    """Estrutura de dados para comentários do Reddit"""
    id: str
    body: str
    author: str
    score: int
    created_utc: float
    parent_id: str
    post_id: str
    subreddit: str
    
    @property
    def created_datetime(self) -> datetime:
        """Converte timestamp UTC para datetime"""
        return datetime.fromtimestamp(self.created_utc)

class RedditCollector:
    """Coletor de dados do Reddit usando Manus API"""
    
    def __init__(self):
        self.client = None
        if MANUS_API_AVAILABLE:
            try:
                self.client = ApiClient()
                logger.info("Reddit Collector inicializado com Manus API")
            except Exception as e:
                logger.error(f"Erro ao inicializar Manus API: {e}")
                self.client = None
        
        # Subreddits relacionados a Bitcoin e criptomoedas
        self.bitcoin_subreddits = [
            'Bitcoin',
            'CryptoCurrency', 
            'BitcoinMarkets',
            'btc',
            'CryptoMarkets',
            'BitcoinBeginners',
            'BitcoinDiscussion',
            'CryptoTechnology',
            'investing',
            'stocks'
        ]
        
        # Palavras-chave relacionadas a Bitcoin
        self.bitcoin_keywords = [
            'bitcoin', 'btc', 'cryptocurrency', 'crypto', 'blockchain',
            'satoshi', 'hodl', 'moon', 'diamond hands', 'paper hands',
            'bull market', 'bear market', 'dip', 'pump', 'dump',
            'halving', 'mining', 'wallet', 'exchange', 'trading'
        ]
    
    def get_hot_posts(self, subreddit: str, limit: int = 50) -> List[RedditPost]:
        """Coleta posts quentes de um subreddit"""
        if not self.client:
            logger.warning("API não disponível, retornando dados simulados")
            return self._generate_mock_posts(subreddit, limit)
        
        try:
            logger.info(f"Coletando {limit} posts quentes de r/{subreddit}")
            
            response = self.client.call_api('Reddit/AccessAPI', query={
                'subreddit': subreddit,
                'limit': limit
            })
            
            if not response or 'data' not in response:
                logger.warning(f"API falhou para r/{subreddit}, usando dados simulados")
                return self._generate_mock_posts(subreddit, limit)
            
            posts = []
            children = response['data'].get('children', [])
            
            for child in children:
                if child.get('kind') == 't3':  # Post
                    post_data = child.get('data', {})
                    
                    post = RedditPost(
                        id=post_data.get('id', ''),
                        title=post_data.get('title', ''),
                        selftext=post_data.get('selftext', ''),
                        author=post_data.get('author', ''),
                        subreddit=post_data.get('subreddit', subreddit),
                        score=post_data.get('score', 0),
                        num_comments=post_data.get('num_comments', 0),
                        created_utc=post_data.get('created_utc', 0),
                        url=post_data.get('url', ''),
                        permalink=post_data.get('permalink', ''),
                        upvote_ratio=post_data.get('upvote_ratio'),
                        flair_text=post_data.get('link_flair_text')
                    )
                    
                    posts.append(post)
            
            logger.info(f"Coletados {len(posts)} posts de r/{subreddit}")
            return posts
            
        except Exception as e:
            logger.error(f"Erro ao coletar posts de r/{subreddit}: {e}")
            return []
    
    def collect_bitcoin_posts(self, 
                            subreddits: Optional[List[str]] = None,
                            limit_per_subreddit: int = 25,
                            filter_keywords: bool = True) -> List[RedditPost]:
        """Coleta posts relacionados a Bitcoin de múltiplos subreddits"""
        
        if subreddits is None:
            subreddits = self.bitcoin_subreddits
        
        all_posts = []
        
        for subreddit in subreddits:
            try:
                posts = self.get_hot_posts(subreddit, limit_per_subreddit)
                
                if filter_keywords:
                    # Filtra posts que contêm palavras-chave relacionadas a Bitcoin
                    filtered_posts = []
                    for post in posts:
                        text_to_check = f"{post.title} {post.selftext}".lower()
                        if any(keyword.lower() in text_to_check for keyword in self.bitcoin_keywords):
                            filtered_posts.append(post)
                    
                    logger.info(f"Filtrados {len(filtered_posts)}/{len(posts)} posts com palavras-chave Bitcoin de r/{subreddit}")
                    all_posts.extend(filtered_posts)
                else:
                    all_posts.extend(posts)
                
                # Delay para evitar rate limiting
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Erro ao coletar de r/{subreddit}: {e}")
                continue
        
        # Remove duplicatas baseado no ID
        unique_posts = {}
        for post in all_posts:
            if post.id not in unique_posts:
                unique_posts[post.id] = post
        
        final_posts = list(unique_posts.values())
        logger.info(f"Total de posts únicos coletados: {len(final_posts)}")
        
        return final_posts
    
    def _generate_mock_posts(self, subreddit: str, limit: int) -> List[RedditPost]:
        """Gera posts simulados para teste quando a API não está disponível"""
        
        mock_posts_data = [
            {
                "title": "Bitcoin hits new all-time high! 🚀",
                "selftext": "Just saw BTC break through $100k resistance. This is incredible! HODL strong everyone!",
                "score": 1250,
                "sentiment": "very_positive"
            },
            {
                "title": "Should I sell my Bitcoin now?",
                "selftext": "I'm getting nervous about the recent volatility. What do you think?",
                "score": 45,
                "sentiment": "negative"
            },
            {
                "title": "Bitcoin technical analysis - bullish pattern forming",
                "selftext": "Looking at the charts, I see a clear ascending triangle. Target price $120k.",
                "score": 890,
                "sentiment": "positive"
            },
            {
                "title": "Bitcoin crash incoming? Market looks scary",
                "selftext": "All indicators point to a major correction. Be careful out there.",
                "score": 234,
                "sentiment": "negative"
            },
            {
                "title": "Just bought my first Bitcoin!",
                "selftext": "Finally took the plunge and bought 0.1 BTC. Excited to be part of the community!",
                "score": 567,
                "sentiment": "positive"
            },
            {
                "title": "Bitcoin mining profitability update",
                "selftext": "Current mining difficulty and energy costs analysis. Still profitable for most miners.",
                "score": 123,
                "sentiment": "neutral"
            },
            {
                "title": "HODL vs Trading - what's your strategy?",
                "selftext": "Been holding for 3 years, wondering if I should start trading more actively.",
                "score": 78,
                "sentiment": "neutral"
            },
            {
                "title": "Bitcoin adoption by major corporations",
                "selftext": "More companies are adding BTC to their balance sheets. This is huge for adoption!",
                "score": 445,
                "sentiment": "positive"
            },
            {
                "title": "Regulatory concerns affecting Bitcoin price",
                "selftext": "New regulations might impact crypto markets. What are your thoughts?",
                "score": 156,
                "sentiment": "negative"
            },
            {
                "title": "Bitcoin Lightning Network update",
                "selftext": "Lightning adoption is growing fast. Instant, cheap transactions are the future!",
                "score": 334,
                "sentiment": "positive"
            }
        ]
        
        posts = []
        current_time = datetime.now()
        
        for i, data in enumerate(mock_posts_data[:limit]):
            post = RedditPost(
                id=f"mock_{i}_{subreddit}",
                title=data["title"],
                selftext=data["selftext"],
                author=f"user_{i}",
                subreddit=subreddit,
                score=data["score"],
                num_comments=data["score"] // 10,  # Aproximação
                created_utc=(current_time - timedelta(hours=i)).timestamp(),
                url=f"https://reddit.com/r/{subreddit}/mock_{i}",
                permalink=f"/r/{subreddit}/comments/mock_{i}/",
                upvote_ratio=0.85 + (data["score"] / 10000),  # Simulação
                flair_text="Discussion" if i % 2 == 0 else None
            )
            posts.append(post)
        
        logger.info(f"Gerados {len(posts)} posts simulados para r/{subreddit}")
        return posts
    
    def posts_to_dataframe(self, posts: List[RedditPost]) -> pd.DataFrame:
        """Converte lista de posts para DataFrame pandas"""
        
        data = []
        for post in posts:
            data.append({
                'id': post.id,
                'title': post.title,
                'selftext': post.selftext,
                'full_text': post.full_text,
                'author': post.author,
                'subreddit': post.subreddit,
                'score': post.score,
                'num_comments': post.num_comments,
                'created_utc': post.created_utc,
                'created_datetime': post.created_datetime,
                'url': post.url,
                'permalink': post.permalink,
                'upvote_ratio': post.upvote_ratio,
                'flair_text': post.flair_text
            })
        
        df = pd.DataFrame(data)
        
        if not df.empty:
            # Ordena por score (popularidade) decrescente
            df = df.sort_values('score', ascending=False)
            
            # Adiciona colunas úteis
            df['text_length'] = df['full_text'].str.len()
            df['hours_ago'] = (datetime.now() - df['created_datetime']).dt.total_seconds() / 3600
            
        return df
    
    def save_posts_to_file(self, posts: List[RedditPost], filename: str):
        """Salva posts em arquivo JSON"""
        
        data = []
        for post in posts:
            data.append({
                'id': post.id,
                'title': post.title,
                'selftext': post.selftext,
                'author': post.author,
                'subreddit': post.subreddit,
                'score': post.score,
                'num_comments': post.num_comments,
                'created_utc': post.created_utc,
                'created_datetime': post.created_datetime.isoformat(),
                'url': post.url,
                'permalink': post.permalink,
                'upvote_ratio': post.upvote_ratio,
                'flair_text': post.flair_text
            })
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Posts salvos em {filename}")
    
    def load_posts_from_file(self, filename: str) -> List[RedditPost]:
        """Carrega posts de arquivo JSON"""
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            posts = []
            for item in data:
                post = RedditPost(
                    id=item['id'],
                    title=item['title'],
                    selftext=item['selftext'],
                    author=item['author'],
                    subreddit=item['subreddit'],
                    score=item['score'],
                    num_comments=item['num_comments'],
                    created_utc=item['created_utc'],
                    url=item['url'],
                    permalink=item['permalink'],
                    upvote_ratio=item.get('upvote_ratio'),
                    flair_text=item.get('flair_text')
                )
                posts.append(post)
            
            logger.info(f"Carregados {len(posts)} posts de {filename}")
            return posts
            
        except Exception as e:
            logger.error(f"Erro ao carregar posts de {filename}: {e}")
            return []

class BitcoinSentimentCollector:
    """Coletor especializado para análise de sentimento Bitcoin"""
    
    def __init__(self):
        self.reddit_collector = RedditCollector()
        
        # Configurações específicas para Bitcoin
        self.priority_subreddits = [
            'Bitcoin',           # Subreddit principal do Bitcoin
            'BitcoinMarkets',    # Foco em trading e mercados
            'CryptoCurrency',    # Discussões gerais sobre crypto
            'btc'               # Subreddit alternativo do Bitcoin
        ]
        
        self.secondary_subreddits = [
            'CryptoMarkets',
            'BitcoinBeginners',
            'investing',
            'stocks'
        ]
    
    def collect_recent_sentiment_data(self, 
                                    hours_back: int = 24,
                                    min_score: int = 5,
                                    max_posts_per_subreddit: int = 50) -> Tuple[List[RedditPost], pd.DataFrame]:
        """Coleta dados recentes para análise de sentimento"""
        
        logger.info(f"Coletando dados de sentimento das últimas {hours_back} horas")
        
        # Coleta posts dos subreddits prioritários
        all_posts = []
        
        # Subreddits prioritários - mais posts
        for subreddit in self.priority_subreddits:
            posts = self.reddit_collector.get_hot_posts(subreddit, max_posts_per_subreddit)
            all_posts.extend(posts)
            time.sleep(0.5)  # Rate limiting
        
        # Subreddits secundários - menos posts
        for subreddit in self.secondary_subreddits:
            posts = self.reddit_collector.get_hot_posts(subreddit, max_posts_per_subreddit // 2)
            # Filtra apenas posts relacionados a Bitcoin
            bitcoin_posts = []
            for post in posts:
                text = f"{post.title} {post.selftext}".lower()
                if any(keyword in text for keyword in ['bitcoin', 'btc', 'crypto']):
                    bitcoin_posts.append(post)
            all_posts.extend(bitcoin_posts)
            time.sleep(0.5)
        
        # Filtra por tempo e score
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        filtered_posts = []
        
        for post in all_posts:
            if (post.created_datetime >= cutoff_time and 
                post.score >= min_score and
                len(post.full_text.strip()) > 10):  # Texto mínimo
                filtered_posts.append(post)
        
        # Remove duplicatas
        unique_posts = {}
        for post in filtered_posts:
            if post.id not in unique_posts:
                unique_posts[post.id] = post
        
        final_posts = list(unique_posts.values())
        
        # Converte para DataFrame
        df = self.reddit_collector.posts_to_dataframe(final_posts)
        
        logger.info(f"Coletados {len(final_posts)} posts únicos para análise de sentimento")
        
        return final_posts, df
    
    def get_trending_topics(self, posts: List[RedditPost], top_n: int = 10) -> List[Tuple[str, int]]:
        """Identifica tópicos em alta baseado nos títulos dos posts"""
        
        from collections import Counter
        import re
        
        # Extrai palavras dos títulos
        words = []
        for post in posts:
            # Remove pontuação e converte para minúsculas
            title_words = re.findall(r'\b\w+\b', post.title.lower())
            # Filtra palavras muito comuns ou muito curtas
            filtered_words = [
                word for word in title_words 
                if len(word) > 3 and word not in ['bitcoin', 'btc', 'crypto', 'cryptocurrency']
            ]
            words.extend(filtered_words)
        
        # Conta frequência
        word_counts = Counter(words)
        trending = word_counts.most_common(top_n)
        
        logger.info(f"Tópicos em alta: {[word for word, count in trending[:5]]}")
        
        return trending

def main():
    """Função principal para teste do coletor"""
    
    print("=== Sistema de Coleta de Dados Reddit para Bitcoin ===\n")
    
    # Inicializa coletor
    collector = BitcoinSentimentCollector()
    
    # Coleta dados recentes
    print("Coletando dados recentes...")
    posts, df = collector.collect_recent_sentiment_data(
        hours_back=24,
        min_score=10,
        max_posts_per_subreddit=30
    )
    
    if posts:
        print(f"\n✅ Coletados {len(posts)} posts")
        
        # Estatísticas básicas
        print(f"\nEstatísticas:")
        print(f"- Score médio: {df['score'].mean():.1f}")
        print(f"- Comentários médios: {df['num_comments'].mean():.1f}")
        print(f"- Subreddits únicos: {df['subreddit'].nunique()}")
        print(f"- Distribuição por subreddit:")
        for subreddit, count in df['subreddit'].value_counts().head().items():
            print(f"  - r/{subreddit}: {count} posts")
        
        # Tópicos em alta
        trending = collector.get_trending_topics(posts)
        print(f"\nTópicos em alta:")
        for word, count in trending[:5]:
            print(f"  - {word}: {count} menções")
        
        # Mostra alguns posts de exemplo
        print(f"\nExemplos de posts coletados:")
        for i, post in enumerate(posts[:3]):
            print(f"\n{i+1}. [{post.subreddit}] {post.title}")
            print(f"   Score: {post.score} | Comentários: {post.num_comments}")
            print(f"   Texto: {post.selftext[:100]}{'...' if len(post.selftext) > 100 else ''}")
        
        # Salva dados
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bitcoin_posts_{timestamp}.json"
        collector.reddit_collector.save_posts_to_file(posts, filename)
        print(f"\n💾 Dados salvos em {filename}")
        
    else:
        print("❌ Nenhum post coletado")

if __name__ == "__main__":
    main()

