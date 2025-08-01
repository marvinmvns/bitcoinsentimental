#!/usr/bin/env python3
"""
Script para corrigir problemas de permissão nos scripts de instalação
"""

import os
import re
from pathlib import Path

def fix_install_script():
    """Corrige problemas de permissão no script de instalação"""
    
    script_path = Path(__file__).parent / "scripts" / "install_system.sh"
    
    if not script_path.exists():
        print(f"❌ Script não encontrado: {script_path}")
        return
    
    print("🔧 Corrigindo problemas de permissão no script de instalação...")
    
    try:
        # Ler o conteúdo do script
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Correções específicas para problemas de permissão
        fixes = [
            # Problema principal: chmod sem sudo
            (
                r'chmod 600 "\$INSTALL_DIR/config/\.env"',
                'sudo chmod 600 "$INSTALL_DIR/config/.env"'
            ),
            
            # Outros possíveis problemas de permissão
            (
                r'chmod \+x "\$INSTALL_DIR/quick_start\.sh"',
                'sudo chmod +x "$INSTALL_DIR/quick_start.sh"'
            ),
            
            # Garantir que o arquivo .env seja criado com as permissões corretas
            (
                r'# Proteger arquivo de ambiente\n    chmod 600',
                '# Proteger arquivo de ambiente\n    sudo chmod 600'
            ),
            
            # Corrigir paths para nova estrutura nos comandos do quick_start
            (
                r'python src/bitcoin_trading_system_with_ollama\.py',
                'python src/trading/bitcoin_trading_system_with_ollama.py'
            ),
            (
                r'python src/sentiment_benchmark\.py',
                'python src/core/sentiment_benchmark.py'
            ),
            
            # Atualizar systemd service para usar path correto
            (
                r'ExecStart=\$INSTALL_DIR/venv/bin/python \$INSTALL_DIR/src/bitcoin_trading_system_with_ollama\.py',
                'ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/src/trading/bitcoin_trading_system_with_ollama.py'
            ),
        ]
        
        # Aplicar correções
        modified = False
        for old_pattern, new_text in fixes:
            if re.search(old_pattern, content):
                content = re.sub(old_pattern, new_text, content)
                modified = True
                print(f"✅ Corrigido: {old_pattern}")
        
        # Adicionar função para criar arquivo .env com permissões corretas
        env_function = '''
create_secure_env_file() {
    log_info "Criando arquivo .env com permissões seguras..."
    
    # Criar arquivo temporário
    local temp_env=$(mktemp)
    
    # Escrever conteúdo no arquivo temporário
    cat > "$temp_env" << 'EOF'
# Configurações do Sistema
TRADING_ENV=production
DEBUG=false

# Configurações de Monitoramento
ENABLE_METRICS=true
METRICS_PORT=8080

# Configurações de Segurança
LOG_LEVEL=INFO
MAX_CONCURRENT_REQUESTS=10
EOF
    
    # Mover arquivo para local final com sudo e definir permissões
    sudo mv "$temp_env" "$INSTALL_DIR/config/.env"
    sudo chown "$USER_NAME:$USER_NAME" "$INSTALL_DIR/config/.env"
    sudo chmod 600 "$INSTALL_DIR/config/.env"
    
    log_success "Arquivo .env criado com permissões seguras"
}
'''
        
        # Substituir a função create_configuration_files problemática
        if 'create_configuration_files()' in content:
            # Encontrar e substituir a seção problemática
            pattern = r'(# Arquivo de variáveis de ambiente.*?EOF\s*\n\s*# Proteger arquivo de ambiente.*?chmod 600.*?\.env")'
            replacement = '''# Arquivo de variáveis de ambiente - usar função segura
    create_secure_env_file'''
            
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            
            # Adicionar a função antes da função create_configuration_files
            content = content.replace('create_configuration_files() {', 
                                    env_function + '\ncreate_configuration_files() {')
            modified = True
            print("✅ Função create_secure_env_file adicionada")
        
        # Salvar arquivo modificado se houve mudanças
        if modified:
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Script corrigido salvo em: {script_path}")
        else:
            print("ℹ️  Nenhuma correção necessária")
            
    except Exception as e:
        print(f"❌ Erro ao corrigir script: {e}")

def create_install_fix_guide():
    """Cria um guia para resolver problemas de instalação"""
    
    guide_path = Path(__file__).parent / "INSTALL_TROUBLESHOOTING.md"
    
    guide_content = '''# Guia de Solução de Problemas - Instalação

## Problema: "chmod: alterando permissões de '/opt/bitcoin-trading-system/config/.env': Operação não permitida"

### Causa
O script está tentando alterar permissões de um arquivo sem usar `sudo`, ou o arquivo não existe.

### Soluções

#### Solução 1: Executar o script corrigido
```bash
# Use o script corrigido que agora tem sudo nos comandos chmod
./scripts/install_system.sh
```

#### Solução 2: Correção manual
Se ainda houver problemas, execute os comandos manualmente:

```bash
# Corrigir permissões do arquivo .env
sudo chown bitcoin-trader:bitcoin-trader /opt/bitcoin-trading-system/config/.env
sudo chmod 600 /opt/bitcoin-trading-system/config/.env

# Corrigir permissões de outros arquivos se necessário
sudo chown -R bitcoin-trader:bitcoin-trader /opt/bitcoin-trading-system
sudo chmod -R 755 /opt/bitcoin-trading-system
sudo chmod 600 /opt/bitcoin-trading-system/config/.env
```

#### Solução 3: Instalação alternativa
Use o script de instalação mínima para desenvolvimento:

```bash
./scripts/install_minimal.sh
```

### Verificação
Após a correção, verifique se está funcionando:

```bash
# Verificar permissões
ls -la /opt/bitcoin-trading-system/config/.env

# Testar o sistema
python3 setup.py
python3 examples/main_demo.py
```

### Problemas Comuns Adicionais

#### Problema: Ollama não inicia
```bash
sudo systemctl start ollama
sudo systemctl enable ollama
```

#### Problema: Dependências Python faltando
```bash
cd /opt/bitcoin-trading-system
source venv/bin/activate
pip install -r requirements.txt
```

#### Problema: Usuário sem permissões sudo
```bash
# Adicionar usuário ao grupo sudo
sudo usermod -aG sudo bitcoin-trader

# Ou executar instalação em diretório do usuário
./scripts/install_system.sh --dir /home/$USER/bitcoin-trading-system
```

## Prevenção

Para evitar problemas futuros:

1. **Execute sempre com usuário não-root** que tenha privilégios sudo
2. **Verifique se o Ollama está funcionando** antes da instalação
3. **Use o script corrigido** que tem todas as permissões adequadas
4. **Para desenvolvimento**, prefira `install_minimal.sh`

## Logs

Verificar logs em caso de problemas:
```bash
# Logs do sistema
sudo journalctl -u bitcoin-trading-system -f

# Logs do Ollama
sudo journalctl -u ollama -f

# Logs de instalação
tail -f /tmp/bitcoin-trading-install.log
```
'''
    
    try:
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(guide_content)
        print(f"✅ Guia de solução de problemas criado: {guide_path}")
    except Exception as e:
        print(f"❌ Erro ao criar guia: {e}")

def main():
    """Função principal"""
    print("🛠️  CORREÇÃO DE PROBLEMAS DE INSTALAÇÃO")
    print("=" * 50)
    
    fix_install_script()
    create_install_fix_guide()
    
    print("\n✅ Correções aplicadas!")
    print("\nAgora você pode:")
    print("1. Executar: ./scripts/install_system.sh")
    print("2. Ou se ainda houver problemas, consultar: INSTALL_TROUBLESHOOTING.md")
    print("3. Para desenvolvimento: ./scripts/install_minimal.sh")

if __name__ == "__main__":
    main()