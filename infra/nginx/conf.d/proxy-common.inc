# Cabeçalhos padrão de proxy reverso, incluídos por toda rota de serviço em
# api-gateway.conf — evita repetir os mesmos 6 `proxy_set_header` doze vezes.
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_connect_timeout 5s;
proxy_read_timeout 30s;
