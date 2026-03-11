# Gera certificado SSL auto-assinado para desenvolvimento (Windows)
# Em produção, use Let's Encrypt

New-Item -ItemType Directory -Force -Path "nginx\ssl" | Out-Null

# Requer OpenSSL instalado (disponível via Git for Windows ou chocolatey)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 `
    -keyout "nginx\ssl\key.pem" `
    -out "nginx\ssl\cert.pem" `
    -subj "/C=BR/ST=SP/L=SaoPaulo/O=RadarLicitacoesTI/CN=localhost"

Write-Host "Certificado SSL gerado em nginx\ssl\"
Write-Host "Para producao, substitua por Let's Encrypt"
