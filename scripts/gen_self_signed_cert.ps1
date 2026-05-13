# Generate self-signed certificate for local dev/testing
# Requires OpenSSL (comes with Git for Windows)

$SSL_DIR = "$PSScriptRoot\..\nginx\ssl"
New-Item -ItemType Directory -Force -Path $SSL_DIR | Out-Null

openssl req -x509 -nodes -days 365 -newkey rsa:2048 `
    -keyout "$SSL_DIR\key.pem" `
    -out "$SSL_DIR\cert.pem" `
    -subj "/CN=localhost" `
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"

Write-Host "Cert created: $SSL_DIR/cert.pem, $SSL_DIR/key.pem"
Write-Host "Browser will show warning - click Advanced -> Proceed."
