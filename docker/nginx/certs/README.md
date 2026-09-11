# Nginx SSL Certificates

This directory holds SSL/TLS certificates and private keys used for HTTPS termination in Nginx.

## Generating Local Self-Signed Certificates

For local development or testing with HTTPS, you can generate a self-signed certificate using OpenSSL:

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout docker/nginx/certs/nginx-selfsigned.key \
  -out docker/nginx/certs/nginx-selfsigned.crt \
  -subj "/C=ID/ST=Jakarta/L=Jakarta/O=Dedisalam/OU=DevOps/CN=localhost"
```

> [!NOTE]
> `*.key` and `*.crt` files are explicitly ignored by `.gitignore` to prevent committing private keys or certificates to Git.
