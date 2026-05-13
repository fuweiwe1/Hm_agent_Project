#!/bin/bash
# 生成自签证书（仅用于开发测试，生产环境请用 Let's Encrypt）

SSL_DIR="$(dirname "$0")/../nginx/ssl"
mkdir -p "$SSL_DIR"

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$SSL_DIR/key.pem" \
    -out "$SSL_DIR/cert.pem" \
    -subj "/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

echo "自签证书已生成: $SSL_DIR/{cert,key}.pem"
echo "浏览器访问时会提示不安全，点击高级→继续访问即可。"
