# 🔧 SOLUÇÃO RÁPIDA - Instalar Pacotes Faltantes

## 📊 Seu Status Atual

```
✗ streamlit       - NÃO INSTALADO
✗ plotly          - NÃO INSTALADO
```

Os outros pacotes estão OK, só faltam estes 2.

---

## ✅ SOLUÇÃO (Escolha uma)

### **Opção A: Script Automático (recomendado)**

1. **No seu PowerShell atual**, execute:
```powershell
.\instalar_faltantes.bat
```

Pronto! Aguarde terminar.

---

### **Opção B: Comandos Manuais no PowerShell**

1. **Abra PowerShell** (pode ser normal, não precisa admin)

2. **Navegue para a pasta**:
```powershell
cd c:\licitacoes_pncp
```

3. **Ative o ambiente virtual**:
```powershell
.\venv\Scripts\Activate.ps1
```

Se der erro de permissão, execute:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Depois tente ativar novamente.

4. **Instale streamlit**:
```powershell
pip install streamlit==1.28.1
```

5. **Instale plotly**:
```powershell
pip install plotly==5.17.0
```

Aguarde ambos terminarem (pode levar 2-3 minutos).

---

### **Opção C: Reinstalar Tudo de uma vez**

Se quiser reinstalar tudo junto:

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt --force-reinstall
```

---

## ✅ VERIFICAR SE FUNCIONOU

Após instalar, execute:

```powershell
python testar_sistema.py
```

Deve mostrar:
```
✓ streamlit       - Dashboard
✓ plotly          - Gráficos
```

E no final:
```
================================================================
RESULTADO: 11 OK, 0 ERRO
================================================================

✓ SISTEMA PRONTO!
```

---

## 🚀 PRÓXIMOS PASSOS

Quando o teste passar com 100% OK:

### **1. Primeira Coleta de Dados**
```powershell
python pncp_radar_ti_plus.py
```
⏱️ Aguarde 5-15 minutos

### **2. Abrir Dashboard Interativo**
```powershell
streamlit run dashboard.py
```
✅ Abrirá no navegador automaticamente em `http://localhost:8501`

---

## 🆘 Troubleshooting

### ❌ "Permissão Negada" ao ativar venv

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Depois tente novamente.

### ❌ "Access denied" durante instalação

Use o script de recovery (já criado):
```powershell
.\recovery.bat
```

### ❌ Instalação travou

Pressione `Ctrl + C` para parar, depois:
```powershell
pip install --no-cache-dir streamlit==1.28.1
pip install --no-cache-dir plotly==5.17.0
```

---

## ✨ Dica Pro

Coloque este comando em um arquivo `.bat` para deixar tudo em um clique:

**run_full.bat**:
```batch
@echo off
call venv\Scripts\activate.bat
pip install streamlit==1.28.1 plotly==5.17.0 --no-cache-dir
python testar_sistema.py
pause
```

Execute com duplo clique sempre que precisar!

---

**Quando terminar, você terá:**
- ✅ Todos os pacotes instalados
- ✅ Sistema 100% testado
- ✅ Dados sendo coletados
- ✅ Dashboard bonito no navegador

Boa sorte! 🚀
