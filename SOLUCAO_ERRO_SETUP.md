# ✅ SOLUÇÃO DO ERRO - Setup com Permissões

## 🔴 Erro Encontrado

```
ERROR: Could not install packages due to an OSError: [WinError 5] Acesso negado
ERROR: Could not find a version that satisfies the requirement openpyxl>=3.10.0
```

## ✅ Cause e Solução

Há dois problemas:

1. **Falta de permissões de Administrador** → Pip não consegue atualizar a si mesmo
2. **Versão inválida de openpyxl** → 3.10.0 não existe (máximo é 3.1.5)

---

## 🚀 SOLUÇÃO (escolha uma)

### **Opção A: Rápida (recomendada) - 5 minutos**

1. **Abra PowerShell como ADMINISTRADOR**
   - Pressione `Win + X`
   - Selecione `Windows PowerShell (Admin)` ou `Terminal (Admin)`

2. **Navegue para o projeto**
   ```powershell
   cd c:\licitacoes_pncp
   ```

3. **Execute o recovery script** (já corrigido)
   ```powershell
   .\recovery.bat
   ```

4. **Aguarde até ver: "RECOVERY CONCLUIDO!"**

5. **Teste o sistema**
   ```powershell
   python testar_sistema.py
   ```

✅ **Pronto!** Você está funcionando.

---

### **Opção B: Manual - 10 minutos**

Se o recovery não funcionar, siga manualmente:

1. **Abra PowerShell como ADMINISTRADOR**

2. **Navegue até o projeto**
   ```powershell
   cd c:\licitacoes_pncp
   ```

3. **Remova o ambiente antigo**
   ```powershell
   Remove-Item -Recurse -Force venv
   ```

4. **Crie novo ambiente**
   ```powershell
   python -m venv venv
   ```

5. **Ative**
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

6. **Instale cada dependência**
   ```powershell
   pip install requests==2.31.0
   pip install pandas==2.0.3
   pip install openpyxl==3.1.5
   pip install streamlit==1.28.1
   pip install plotly==5.17.0
   ```

7. **Teste**
   ```powershell
   python testar_sistema.py
   ```

✅ **Pronto!**

---

### **Opção C: Para Desenvolvedores - Conda**

Se usar **Anaconda** em vez de venv:

```powershell
# Abra Anaconda Prompt como Admin

cd c:\licitacoes_pncp

# Crie novo ambiente
conda create -n radar python=3.10 -y

# Ative
conda activate radar

# Instale
pip install -r requirements.txt

# Teste
python testar_sistema.py
```

---

## ✨ PróXimos Passos (após sucesso no teste)

### **1. Primeira Coleta**
```powershell
python pncp_radar_ti_plus.py
```
⏱️ Aguarde 5-15 minutos

### **2. Abrir Dashboard**
```powershell
streamlit run dashboard.py
```
✅ Abrirá no navegador automaticamente

---

## 🔧 Troubleshooting - Se Ainda Tiver Erro

### ❌ "Acesso negado" ao instalar

```powershell
# Limpe o cache e tente novamente
pip cache purge
pip install --upgrade --force-reinstall requests pandas openpyxl streamlit plotly
```

### ❌ "Python não encontrado"

```powershell
# Verifique se python está instalado
python --version

# Se não funcionar, instale:
# https://www.python.org/downloads/ (márque "Add Python to PATH")
```

### ❌ "Permissão negada" para venv

```powershell
# Feche todos os prompts de Python/Visual Studio
# Limpe com script de recovery: .\recovery.bat
```

### ❌ "Usar ModuleNotFoundError" após instalação

```powershell
# Verifique se o ambiente está ativado
.\venv\Scripts\Activate.ps1

# Se não conseguir ativar, refaça a instalação
.\recovery.bat
```

---

## ✅ Verificação Rápida

Use este comando para validar tudo:

```powershell
python testar_sistema.py
```

Deve mostrar:
```
✓ Python 3.10+ OK
✓ arquivo.py OK
✓ requests OK
✓ pandas OK
✓ openpyxl OK
✓ streamlit OK
✓ plotly OK
✓ API PNCP respondendo
✓ Permissão de escrita OK
```

---

## 📊 Checklist

- [ ] PowerShell aberto como **ADMINISTRADOR**
- [ ] `recovery.bat` executado com sucesso
- [ ] `python testar_sistema.py` passou todos os testes
- [ ] `python pncp_radar_ti_plus.py` é executável
- [ ] `streamlit run dashboard.py` abre no navegador

---

## 🆘 Última Resort - Limpeza Total

Se nada funcionar, limpe completamente:

```powershell
# 1. Remova Python venv
Remove-Item -Recurse -Force c:\licitacoes_pncp\venv

# 2. Limpe cache pip
Remove-Item -Recurse -Force $env:APPDATA\Python\Python310\site-packages

# 3. Recrie do zero
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

**Agora deve funcionar! 🎉**

Se persistir o erro, envie:
- Versão do Python: `python --version`
- Resultado de: `pip --version`
- Printscreen do erro exato
