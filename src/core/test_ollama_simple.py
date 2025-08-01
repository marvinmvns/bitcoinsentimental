#!/usr/bin/env python3
"""
Teste simples da integração com Ollama
"""

import requests
import json
import time

def test_ollama_direct():
    """Teste direto da API Ollama"""
    print("=== Teste Direto da API Ollama ===")
    
    url = "http://localhost:11434/api/generate"
    
    test_text = "Bitcoin is going to the moon! Best investment ever!"
    
    prompt = f"""
Analyze the sentiment of this Bitcoin text: "{test_text}"
Return only one word: positive, negative, or neutral
"""
    
    payload = {
        "model": "llama3.2:1b",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 10
        }
    }
    
    try:
        print(f"Enviando requisição para: {url}")
        print(f"Texto: {test_text}")
        
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=30)
        end_time = time.time()
        
        print(f"Status: {response.status_code}")
        print(f"Tempo: {end_time - start_time:.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Resposta: {result.get('response', 'N/A')}")
            return True
        else:
            print(f"Erro: {response.text}")
            return False
            
    except Exception as e:
        print(f"Erro na requisição: {e}")
        return False

def test_ollama_sentiment_batch():
    """Teste com múltiplos textos"""
    print("\n=== Teste com Múltiplos Textos ===")
    
    texts = [
        "Bitcoin is going to the moon!",
        "Bitcoin is crashing terribly!",
        "Bitcoin price is stable today."
    ]
    
    url = "http://localhost:11434/api/generate"
    
    for i, text in enumerate(texts, 1):
        print(f"\nTeste {i}: {text}")
        
        prompt = f'Analyze sentiment of: "{text}". Return only: positive, negative, or neutral'
        
        payload = {
            "model": "llama3.2:1b",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 5
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=15)
            if response.status_code == 200:
                result = response.json()
                sentiment = result.get('response', 'N/A').strip().lower()
                print(f"Sentimento: {sentiment}")
            else:
                print(f"Erro: {response.status_code}")
        except Exception as e:
            print(f"Erro: {e}")

if __name__ == "__main__":
    success = test_ollama_direct()
    if success:
        test_ollama_sentiment_batch()
    else:
        print("Teste básico falhou, pulando teste em lote.")

