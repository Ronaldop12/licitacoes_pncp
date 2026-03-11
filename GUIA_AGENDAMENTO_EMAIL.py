#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
════════════════════════════════════════════════════════════════════════════════
GUIA DE CONFIGURAÇÃO - Alertas por Email e Agendamento Automático
════════════════════════════════════════════════════════════════════════════════

Este arquivo contém instruções passo-a-passo para configurar:
1. Alertas por EMAIL via Gmail
2. Agendamento automático no Windows (todos os dias às 7h)
"""

# ════════════════════════════════════════════════════════════════════════════════
# PARTE 1: CONFIGURAR EMAIL VIA GMAIL
# ════════════════════════════════════════════════════════════════════════════════

"""
PASSO 1: Gerar Senha de Aplicativo no Gmail
═════════════════════════════════════════════

1. Acesse sua conta Google:
   https://myaccount.google.com/

2. Clique em "Segurança" no menu esquerdo

3. Role para baixo e procure por "App passwords"
   (Se não aparecer, ative a Autenticação em 2 etapas primeiro)

4. Selecione:
   - App: Mail
   - Device: Windows

5. Clique em "Gerar"

6. Google gerará uma senha de 16 caracteres
   Exemplo: jxyz abcd efgh ijkl
   
   ⚠️  COPIE ESTA SENHA (com ou sem espaços)


PASSO 2: Editar arquivo de configuração
════════════════════════════════════════

Abra: config/alertas_config.json

Procure pela seção "email_config":

{
  "email_config": {
    "ativo": false,                              👈 Mude para: true
    "smtp_server": "smtp.gmail.com",             👈 Padrão Gmail (não altere)
    "smtp_port": 587,                            👈 Padrão Gmail (não altere)
    "email_from": "seu_email@gmail.com",         👈 Seu email do Gmail
    "senha_app": "sua_senha_app_aqui",           👈 Cole a senha gerada AQUI
    "email_destinatario": "seu_email@gmail.com", 👈 Pode ser igual ou diferente
    "enviar_resumo": true,                        👈 true = 1 email com resume das novas licitações
    "notas": "Para Gmail, use 'Senha de Aplicativo' ..."
  }
}

Exemplo preenchido:

{
  "email_config": {
    "ativo": true,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "email_from": "meu_email@gmail.com",
    "senha_app": "jxyzabcdefghijkl",            👈 Sem espaços
    "email_destinatario": "meu_email@gmail.com",
    "enviar_resumo": true,
    "notas": "Para Gmail, use 'Senha de Aplicativo' em https://myaccount.google.com/apppasswords"
  }
}

PASSO 3: Testar envio de email
═══════════════════════════════

Abra PowerShell e rode:

    python -c "from utils_email import EmailAlerter; bot = EmailAlerter('smtp.gmail.com', 587, 'seu_email@gmail.com', 'sua_senha_app'); print('✓ Testando...' if bot.validar_configuracao() else '✗ Erro!')"

Se aparecer: "✓ Testando..." = SUCESSO!
Se aparecer erro: Verifique email/senha


PASSO 4: Ativar email no monitor (OPCIONAL)
════════════════════════════════════════════

Se quiser receber EMAILS quando o monitor detectar licitações,
edite novamente config/alertas_config.json:

    "email_config": {
        "ativo": true,  👈 ISSO ATI VA O ENVIO
        ...
    }

Agora o monitor_alertas.py vai enviar emails automaticamente!


════════════════════════════════════════════════════════════════════════════════
PARTE 2: AGENDAR EXECUÇÃO AUTOMÁTICA NO WINDOWS
════════════════════════════════════════════════════════════════════════════════

OPÇÃO A: Script PowerShell Automático (RECOMENDADO)
═════════════════════════════════════════════════

1. Abra PowerShell como ADMINISTRADOR
   (Clique com botão direito > Executar como administrador)

2. Navigate até a pasta do projeto:
   cd c:\licitacoes_pncp

3. Execute o script:
   .\configurar_agendamento.ps1

4. Siga as instruções:
   - Digite S/N para alterar horário (padrão 07:00)
   - Digite S/N para ativar alertas por email (opcional)
   - Se ativar email, preencha seus dados

5. Pronto! A tarefa foi criada automaticamente.


OPÇÃO B: Agendador de Tarefas Manual
═════════════════════════════════════

1. Abra Agendador de Tarefas:
   Pressione WIN + R
   Digite: taskschd.msc
   Pressione ENTER

2. No painel esquerdo, clique em "Biblioteca de Tarefas"
   Se não houver pasta "PNCP", crie uma:
   - Clique com botão direito em "Biblioteca de Tarefas"
   - Clique em "Nova pasta"
   - Digite: PNCP

3. Clique em PNCP (a pasta que você criou)

4. No painel direito, clique em "Criar Tarefa..."

5. Preencha:
   Nome: PNCP_Alertas_Diario
   Descrição: Monitora licitações e envia alertas
   Marque: ☑ Executar com privilégios mais altos

6. Clique em "Disparadores" (ou "Triggers")
   Cloque em "Novo..."
   
   Configurar como:
   - Inicial: "Diariamente"
   - Hora: 07:00 (ou a hora que preferir)
   - Marque: ☑ Habilitado

7. Clique em "Ações"
   Clique em "Novo..."
   
   Configurar como:
   - Programa/script: C:\licitacoes_pncp\venv\Scripts\python.exe
   - Adicionar argumentos: C:\licitacoes_pncp\monitor_alertas.py
   - Iniciar em: C:\licitacoes_pncp

8. Clique em "OK" e salve


VERIFICAR AGENDAMENTO
════════════════════

Para verifcar se foi criado corretamente:

1. Abra Agendador de Tarefas (WIN + R > taskschd.msc)

2. Na árvore à esquerda, vá até:
   Biblioteca de Tarefas > PNCP > PNCP_Alertas_Diario

3. Clique com botão direito > "Executar"
   Teste agora antes de confiar na automação

4. Clique com botão direito > "Propriedades"
   Veja os detalhes da execução


DICAS IMPORTANTES
═════════════════

✅ CERTIFICAR QUE ESTÁ FUNCIONANDO:

   1. Abra os logs:
      c:\licitacoes_pncp\logs\monitor_alertas.log

   2. Procure por:
      - "✓ Email enviado" = sucesso Email
      - "✓ Alerta enviado" = sucesso Telegram
      - "✗ Erro" = algo deu errado

✅ DESATIVAR TEMPORARIAMENTE:

   Agendador de Tarefas > PNCP_Alertas_Diario
   Clique com botão direito > Desabilitar
   (Reclique para reabilitar)

✅ MODIFICAR HORÁRIO:

   Agendador de Tarefas > PNCP_Alertas_Diario
   Clique com botão direito > Propriedades > Disparadores
   Dê duplo-clique no disparador > altere a hora

✅ RECEBER MAIS FREQUÊNCIA:

   Por padrão, executa 1x por dia às 7h

   Para mudar, repita OPÇÃO A ou B com horário diferente
   (Você pode criar várias tarefas com horários diferentes)


TROUBLESHOOTING
═══════════════

PROBLEMA: "Senha de aplicativo não aceita"
SOLUÇÃO:
  1. Certifique-se de que copiou no Gmail
  2. Retirou os espaços (jx yz... → jxyz...)
  3. Ativou a Autenticação em 2 etapas
  4. Tente novamente no Gmail

PROBLEMA: Email não recebe
SOLUÇÃO:
  1. Verify "email_config": "ativo": true
  2. Check "email_destinatario": "seu_email..."
  3. Procure por "Email enviado" ou "✗ Erro" nos logs
  4. Execute manualmente para testar:
     python monitor_alertas.py

PROBLEMA: Agendador não executa
SOLUÇÃO:
  1. Abra Agendador > Procure a tarefa PNCP_Alertas_Diario
  2. Clique com botão direito > "Executar"
  3. Se deu erro, clique em "Histórico" para ver detalhes
  4. Verifique os logs em: logs/monitor_alertas.log

PROBLEMA: Recebe email mas não tem Telegram
SOLUÇÃO:
  1. Verifique se o token Telegram está correto
  2. Confira a configuração em: config/alertas_config.json
  3. Execute manualmente: python monitor_alertas.py


════════════════════════════════════════════════════════════════════════════════
RESUMO RÁPIDO
════════════════════════════════════════════════════════════════════════════════

PARA SETUP COMPLETO COM EMAIL + AGENDAMENTO:

1. Gerar App Password no Gmail ⬇️
   https://myaccount.google.com/apppasswords

2. Editar config/alertas_config.json
   Preencha: email_from, senha_app, ativo=true

3. Executar script de agendamento
   .\configurar_agendamento.ps1

4. Responder S/S para ativar tudo

5. PRONTO! ✅

Todos os dias às 7h você receberá:
   📱 Alertas no Telegram (instantaneamente)
   📧 Resumo por email (mesmo horário)


════════════════════════════════════════════════════════════════════════════════
"""

# Referência rápida JSON
EXEMPLO_CONFIG_COMPLETO = """{
  "telegram_token": "8775070167:AAGjAIkwPsyVpw1TyaYDkQVrzk7-IaiFIpw",
  "email_config": {
    "ativo": true,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "email_from": "seu.email@gmail.com",
    "senha_app": "xyzj abcd efgh ijkl",
    "email_destinatario": "seu.email@gmail.com",
    "enviar_resumo": true,
    "notas": "Altere esses valores com seus dados!"
  },
  "alertas": [...],
  "monitoramento": {...}
}"""

print(__doc__)
