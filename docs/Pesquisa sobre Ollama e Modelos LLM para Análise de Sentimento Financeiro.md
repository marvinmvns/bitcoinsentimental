# Pesquisa sobre Ollama e Modelos LLM para Análise de Sentimento Financeiro

## Informações Coletadas

### Sobre Ollama
- Ferramenta para gerenciar e executar LLMs localmente
- Suporta modelos como Meta's Llama2, Mistral's Mixtral
- Instalação simples: `curl -fsSL https://ollama.com/install.sh | sh`
- Comando para instalar modelos: `ollama pull mixtral`

### Modelos Recomendados para Análise de Sentimento

#### 1. Gemma 2 9B
- Segundo discussões no Reddit, os novos modelos Gemma são excelentes para análise de sentimento
- Gemma 2 9B deve ter performance superior ao Llama 3
- Modelo mais recente e otimizado

#### 2. Mixtral
- Mencionado como um dos modelos populares no Ollama
- Boa performance para tarefas de NLP
- Tamanho balanceado entre performance e recursos

#### 3. DeepSeek R1
- Mencionado em artigos sobre análise financeira local
- Especializado em raciocínio e análise
- Boa performance em tarefas financeiras

#### 4. Llama 3
- Modelo base popular
- Boa performance geral
- Amplamente testado

### Implementação com Langchain
```python
from langchain_community.chat_models import ChatOllama
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from tenacity import retry, stop_after_attempt, RetryError

class SentimentClassification(BaseModel):
    sentiment: str = Field(
        ...,
        description="The sentiment of the text",
        enum=["positive", "negative", "neutral"],
    )
    score: float = Field(..., description="The score of the sentiment", ge=-1, le=1)
    justification: str = Field(..., description="The justification of the sentiment")
    main_entity: str = Field(..., description="The main entity discussed in the text")

def llm_sentiment(text: str, llm) -> tuple[str, float, str, str]:
    parser = PydanticOutputParser(pydantic_object=SentimentClassification)
    
    prompt = PromptTemplate(
        template="Describe the sentiment of a text of financial news.\\n{format_instructions}\\n{news}",
        input_variables=["news"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    
    chain = prompt | llm | parser
    
    @retry(stop=stop_after_attempt(5))
    def run_chain(text: str, chain) -> dict:
        return chain.invoke({"news": text}).dict()
    
    result = run_chain(text, chain)
    return result['sentiment'], result['score'], result['justification'], result['main_entity']
```

### Vantagens dos LLMs Locais
1. **Privacidade**: Dados não saem do ambiente local
2. **Custo**: Sem custos de API após instalação inicial
3. **Controle**: Controle total sobre o modelo e parâmetros
4. **Latência**: Resposta mais rápida sem chamadas de rede
5. **Customização**: Possibilidade de fine-tuning

### Pesquisas Acadêmicas Relevantes
- "LLMs and NLP models in cryptocurrency sentiment analysis" (2024) - MDPI
- "Finllama: LLM-based financial sentiment analysis for algorithmic trading" (2024)
- "Large language models and sentiment analysis in financial markets" (2024) - IEEE

### Próximos Passos
1. Instalar Ollama no sistema
2. Testar modelos Gemma 2 9B, Mixtral e DeepSeek R1
3. Implementar integração com sistema existente
4. Comparar performance com modelos atuais
5. Otimizar prompts para análise de sentimento financeiro



## Descobertas Adicionais sobre Performance

### Gemma-7B Performance em Análise de Sentimento Financeiro
- **Estudo IEEE 2024**: Fine-tuning do Gemma-7B para análise de sentimento de headlines financeiras
- **Dataset**: FinancialPhraseBank com sentimentos categorizados
- **Comparação**: Gemma-7B vs DistilBERT-base-uncased vs Llama
- **Resultado**: Gemma-7B fine-tuned **superou todos os outros modelos**
- **Métricas**: Maior precision, recall e F1-score
- **Aplicação**: Insights de mercado, gestão de risco, decisões de investimento

### DeepSeek R1 Capabilities
- **Especialização**: Análise financeira com capacidades de raciocínio avançadas
- **Aplicações**: Análise de demonstrações financeiras, interpretação de dados complexos
- **Vantagem**: Raciocínio estruturado e análise orientada por dados
- **Uso**: Construção de analistas financeiros agênticos

### Modelos Recomendados (Ranking por Performance)
1. **Gemma 2 9B** - Melhor para análise de sentimento geral
2. **Gemma-7B (fine-tuned)** - Comprovadamente superior para sentimento financeiro
3. **DeepSeek R1** - Excelente para análise financeira complexa
4. **Mixtral** - Boa performance geral, balanceado
5. **Llama 3** - Baseline sólido

### Considerações Técnicas
- **Gemma 2 9B**: Mais recente, melhor que Llama 3 segundo testes
- **Gemma-7B**: Menor, mas com fine-tuning específico para finanças
- **DeepSeek R1**: Foco em raciocínio e análise estruturada
- **Recursos**: Gemma-7B requer menos recursos que 9B
- **Fine-tuning**: Possibilidade de treinar especificamente para Bitcoin/crypto

