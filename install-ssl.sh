#!/bin/bash

# === Settings ===
CERT_DIR="./certs"
KEY_FILE="$CERT_DIR/key.pem"
CERT_FILE="$CERT_DIR/cert.pem"
DAYS_VALID=365

# === Create cert directory if not exists ===
mkdir -p "$CERT_DIR"

# === Generate self-signed certificate ===
echo "Generating self-signed SSL certificate for localhost..."

openssl req -x509 -newkey rsa:2048 \
  -keyout "$KEY_FILE" \
  -out "$CERT_FILE" \
  -days $DAYS_VALID \
  -nodes \
  -subj "//CN=localhost"

# === Done ===
echo ""
echo "✅ Certificate generated!"
echo "🔐 Key:  $KEY_FILE"
echo "📄 Cert: $CERT_FILE"
echo "📆 Valid for: $DAYS_VALID days"
echo ""
echo "👉 Use these in your dev server (FastAPI, Node, etc)."
