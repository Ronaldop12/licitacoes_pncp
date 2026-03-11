#!/usr/bin/env pwsh
# -*- coding: utf-8 -*-
<#

CONFIGURAR AGENDAMENTO DE TAREFAS - Sistema Radar TI


Script para agendar execuo automtica do monitor de alertas.

Execuo:
    .\configurar_agendamento.ps1

Pr-requisitos:
    - Executar PowerShell como Administrador
    - Windows 10/11 ou Windows Server
#>

# Verificar privilgios de administrador
$isAdmin = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
if (-not $isAdmin.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host " Erro: Este script precisa ser executado como Administrador!" -ForegroundColor Red
    Write-Host " Clique com boto direito no PowerShell e escolha 'Executar como administrador'" -ForegroundColor Yellow
    exit 1
}

# Cores
$ColorSucesso = "Green"
$ColorErro = "Red"
$ColorInfo = "Cyan"
$ColorAviso = "Yellow"

Write-Host "`n" + "=" * 80
Write-Host " CONFIGURADOR DE AGENDAMENTO - Sistema Radar de Licitaes TI"
Write-Host "=" * 80 + "`n"

# 
# PASSO 1: Verificar diretrio
# 

Write-Host "1  Verificando diretrio..." -ForegroundColor $ColorInfo

$scriptPath = Get-Location
$monitorScript = Join-Path $scriptPath "monitor_alertas.py"

if (-not (Test-Path $monitorScript)) {
    Write-Host " Arquivo monitor_alertas.py no encontrado em: $scriptPath" -ForegroundColor $ColorErro
    Write-Host "   Certifique-se de estar na pasta correta (c:\licitacoes_pncp)" -ForegroundColor $ColorAviso
    exit 1
}

Write-Host " Diretrio verificado: $scriptPath`n" -ForegroundColor $ColorSucesso

# 
# PASSO 2: Obter hora da execuo
# 

Write-Host "2  Configurao de Horrio" -ForegroundColor $ColorInfo
Write-Host "   Padro: 07:00 (diariamente)"
Write-Host "   Alterar? (S/N) " -NoNewline -ForegroundColor $ColorAviso
$resposta = Read-Host

$hora = "07:00"
if ($resposta -eq "S" -or $resposta -eq "s") {
    Write-Host "   Digite a hora (ex: 14:30): " -NoNewline -ForegroundColor $ColorInfo
    $hora_custom = Read-Host
    if ($hora_custom -match "^\d{2}:\d{2}$") {
        $hora = $hora_custom
        Write-Host "    Horrio definido para: $hora`n" -ForegroundColor $ColorSucesso
    } else {
        Write-Host "    Formato invlido! Usando padro: 07:00`n" -ForegroundColor $ColorErro
    }
} else {
    Write-Host "    Usando horrio padro: 07:00`n" -ForegroundColor $ColorSucesso
}

# 
# PASSO 3: Criar atalho para Python
# 

Write-Host "3  Preparando comando..." -ForegroundColor $ColorInfo

# Tentar encontrar venv
$venvirEnv = Join-Path $scriptPath "venv\Scripts\python.exe"
$pythonExe = if (Test-Path $venvirEnv) { $venvirEnv } else { "python.exe" }

Write-Host "   Python: $pythonExe`n" -ForegroundColor $ColorSucesso

$taskCommand = "$pythonExe $monitorScript"

# 
# PASSO 4: Criar tarefa agendada
# 

Write-Host "4  Criando agendamento de tarefas..." -ForegroundColor $ColorInfo

$taskName = "PNCP_Alertas_Diario"
$taskDescription = "Monitora novas licitaes e envia alertas via Telegram/Email (Sistema Radar TI)"

try {
    # Deletar tarefa antiga se existir
    $taskExists = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($taskExists) {
        Write-Host "   Removendo tarefa anterior..." -ForegroundColor $ColorAviso
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
        Start-Sleep -Seconds 1
    }

    # Criar trigger dirio
    $trigger = New-ScheduledTaskTrigger -Daily -At $hora

    # Criar ao
    $action = New-ScheduledTaskAction `
        -Execute $pythonExe `
        -Argument $monitorScript `
        -WorkingDirectory $scriptPath

    # Configuraes de execuo
    $settings = New-ScheduledTaskSettingsSet `
        -MultipleInstances IgnoreNew `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable `
        -DontStopOnIdleEnd

    # Registrar tarefa
    Register-ScheduledTask `
        -TaskName $taskName `
        -TaskPath "\PNCP" `
        -Description $taskDescription `
        -Trigger $trigger `
        -Action $action `
        -Settings $settings `
        -RunLevel Highest | Out-Null

    Write-Host " Tarefa criada com sucesso!`n" -ForegroundColor $ColorSucesso

} catch {
    Write-Host " Erro ao criar tarefa: $_`n" -ForegroundColor $ColorErro
    exit 1
}

# 
# PASSO 5: Verificar tarefa criada
# 

Write-Host "5  Verificando tarefa..." -ForegroundColor $ColorInfo

$task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($task) {
    Write-Host " Tarefa verificada!`n" -ForegroundColor $ColorSucesso
    Write-Host "   Nome: $($task.TaskName)" -ForegroundColor $ColorInfo
    Write-Host "   Caminho: $($task.TaskPath)" -ForegroundColor $ColorInfo
    Write-Host "   Status: $($task.State)" -ForegroundColor $ColorInfo
} else {
    Write-Host " Erro ao verificar tarefa" -ForegroundColor $ColorErro
    exit 1
}

# 
# PASSO 6: Configurao de Email (Opcional)
# 

Write-Host "`n" + "=" * 80
Write-Host "6  CONFIGURAO DE EMAIL (Opcional)" -ForegroundColor $ColorInfo
Write-Host "=" * 80

Write-Host "`n   Deseja receber alertas tambm por EMAIL?" -ForegroundColor $ColorAviso
Write-Host "   (S/N) " -NoNewline -ForegroundColor $ColorAviso
$configEmail = Read-Host

if ($configEmail -eq "S" -or $configEmail -eq "s") {
    Write-Host "`n    CONFIGURAO DE EMAIL" -ForegroundColor $ColorInfo
    Write-Host "   " -ForegroundColor DarkGray
    Write-Host "    Para usar Gmail:                                           " -ForegroundColor DarkGray
    Write-Host "                                                               " -ForegroundColor DarkGray
    Write-Host "    1. Acesse: https://myaccount.google.com/apppasswords      " -ForegroundColor DarkGray
    Write-Host "                                                               " -ForegroundColor DarkGray
    Write-Host "    2. Selecione 'Mail' e 'Windows'                            " -ForegroundColor DarkGray
    Write-Host "                                                               " -ForegroundColor DarkGray
    Write-Host "    3. Copie a 'Senha de Aplicativo' gerada                    " -ForegroundColor DarkGray
    Write-Host "                                                               " -ForegroundColor DarkGray
    Write-Host "   " -ForegroundColor DarkGray

    Write-Host "`n   Digite seu EMAIL: " -NoNewline -ForegroundColor $ColorAviso
    $email = Read-Host

    Write-Host "   Digite a SENHA DE APLICATIVO: " -NoNewline -ForegroundColor $ColorAviso
    $senhaApp = Read-Host -AsSecureString
    $senhaAppPlain = [System.Net.NetworkCredential]::new('', $senhaApp).Password

    Write-Host "   Email destinatrio (mesma conta ou outro?): " -NoNewline -ForegroundColor $ColorAviso
    $emailDest = Read-Host
    if ([String]::IsNullOrWhiteSpace($emailDest)) {
        $emailDest = $email
    }

    # Atualizar config JSON
    $configJsonPath = Join-Path $scriptPath "config\alertas_config.json"
    
    if (Test-Path $configJsonPath) {
        try {
            $config = Get-Content $configJsonPath -Raw | ConvertFrom-Json
            
            $config.email_config.ativo = $true
            $config.email_config.email_from = $email
            $config.email_config.senha_app = $senhaAppPlain
            $config.email_config.email_destinatario = $emailDest
            
            $config | ConvertTo-Json -Depth 10 | Set-Content $configJsonPath
            
            Write-Host "`n    Configurao de email salva!" -ForegroundColor $ColorSucesso
            Write-Host "    Email: $email" -ForegroundColor $ColorInfo
            Write-Host "    Destinatrio: $emailDest`n" -ForegroundColor $ColorInfo
        } catch {
            Write-Host "    Erro ao atualizar config: $_" -ForegroundColor $ColorErro
        }
    }
}

# 
# RESUMO FINAL
# 

Write-Host "`n" + "=" * 80
Write-Host " AGENDAMENTO CONFIGURADO COM SUCESSO!" -ForegroundColor $ColorSucesso
Write-Host "=" * 80 + "`n"

Write-Host " RESUMO:" -ForegroundColor $ColorInfo
Write-Host "    Tarefa: $taskName" -ForegroundColor $ColorInfo
Write-Host "    Horrio: $hora (diariamente)" -ForegroundColor $ColorInfo
Write-Host "    Script: $monitorScript" -ForegroundColor $ColorInfo
Write-Host "    Pasta: $scriptPath" -ForegroundColor $ColorInfo

Write-Host "`n FUNCIONALIDADES:" -ForegroundColor $ColorInfo
Write-Host "    Monitora licitaes do PNCP" -ForegroundColor $ColorSucesso
Write-Host "    Detecta novas licitaes" -ForegroundColor $ColorSucesso
Write-Host "    Envia alertas via Telegram" -ForegroundColor $ColorSucesso
if ($configEmail -eq "S" -or $configEmail -eq "s") {
    Write-Host "    Envia resumo por EMAIL" -ForegroundColor $ColorSucesso
}

Write-Host "`n PRXIMOS PASSOS:" -ForegroundColor $ColorAviso
Write-Host "   1. Abra 'Agendador de Tarefas' (Pressione WIN + R e digite 'taskschd.msc')" -ForegroundColor $ColorAviso
Write-Host "   2. Procure por 'PNCP_Alertas_Diario' em Biblioteca de Tarefas > PNCP" -ForegroundColor $ColorAviso
Write-Host "   3. Clique com boto direito e escolha 'Executar' para testar agora" -ForegroundColor $ColorAviso
Write-Host "   4. Amanh s $hora a tarefa executar automaticamente" -ForegroundColor $ColorAviso

Write-Host "`n DICAS:" -ForegroundColor $ColorInfo
Write-Host "    Para editar: Clique com boto direito na tarefa em Agendador de Tarefas" -ForegroundColor $ColorInfo
Write-Host "    Para desativar: Clique com boto direito > Desabilitar" -ForegroundColor $ColorInfo
Write-Host "    Logs esto em: logs\monitor_alertas.log" -ForegroundColor $ColorInfo

Write-Host "`n" + "=" * 80 + "`n"

Write-Host " Agendamento pronto! Voc receber alertas automaticamente s $hora todos os dias." -ForegroundColor $ColorSucesso


