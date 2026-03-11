#!/bin/bash
# Gera certificado SSL auto-assinado para desenvolvimento
# Em produção, use Let's Encrypt (certbot)

mkdir -p nginx/ssl

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/ssl/key.pem \
    -out nginx/ssl/cert.pem \
    -subj "/C=BR/ST=SP/L=SaoPaulo/O=RadarLicitacoesTI/CN=localhost"

echo "Certificado SSL gerado em nginx/ssl/"
echo "Para produção, substitua por Let's Encrypt:"
echo "  certbot certonly --webroot -w /var/www/certbot -d seu-dominio.com"
