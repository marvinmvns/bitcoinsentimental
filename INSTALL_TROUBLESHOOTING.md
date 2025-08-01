# Guia de Solução de Problemas - Instalação

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
