# syntax=docker/dockerfile:1.7
# Build multi-stage: compila o SPA (Vite/React) no estágio `builder`, serve
# o `dist/` estático via Nginx no estágio final — mesma ideia dos serviços
# Python (imagem final enxuta, sem toolchain de build).
#
# Contexto de build DEVE ser a raiz do repositório (não `apps/admin-web`),
# mesmo motivo dos `services/*/Dockerfile`: consistência de path nos COPY
# abaixo. Ver `infra/docker/docker-compose.prod.yml`.

FROM node:20-alpine AS builder
WORKDIR /app
COPY apps/admin-web/package.json apps/admin-web/package-lock.json* ./
RUN npm ci
COPY apps/admin-web/ ./
# Vite embute `VITE_*` no bundle em BUILD time (não runtime) — precisam
# chegar como build args da Railway, não só variável de ambiente do
# serviço rodando depois (ver docs/deploy/railway_setup.md).
ARG VITE_AUTH_SERVICE_URL
ARG VITE_RESTAURANT_SERVICE_URL
ARG VITE_DINING_SERVICE_URL
ARG VITE_KITCHEN_SERVICE_URL
ARG VITE_KITCHEN_WS_URL
ARG VITE_ORDER_SERVICE_URL
ARG VITE_PAYMENT_SERVICE_URL
ARG VITE_NOTIFICATION_SERVICE_URL
ARG VITE_CUSTOMER_WEB_URL
ENV VITE_AUTH_SERVICE_URL=${VITE_AUTH_SERVICE_URL} \
    VITE_RESTAURANT_SERVICE_URL=${VITE_RESTAURANT_SERVICE_URL} \
    VITE_DINING_SERVICE_URL=${VITE_DINING_SERVICE_URL} \
    VITE_KITCHEN_SERVICE_URL=${VITE_KITCHEN_SERVICE_URL} \
    VITE_KITCHEN_WS_URL=${VITE_KITCHEN_WS_URL} \
    VITE_ORDER_SERVICE_URL=${VITE_ORDER_SERVICE_URL} \
    VITE_PAYMENT_SERVICE_URL=${VITE_PAYMENT_SERVICE_URL} \
    VITE_NOTIFICATION_SERVICE_URL=${VITE_NOTIFICATION_SERVICE_URL} \
    VITE_CUSTOMER_WEB_URL=${VITE_CUSTOMER_WEB_URL}
RUN npm run build

FROM nginx:1.31-alpine AS runtime
COPY apps/admin-web/nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=builder /app/dist /usr/share/nginx/html
# Porta dinâmica (Railway injeta `$PORT` em runtime) — o entrypoint padrão
# da imagem processa o template acima com `envsubst` antes de subir o
# Nginx; default aqui só cobre `docker compose`/execução local sem a var
# setada explicitamente.
ENV PORT=3001
EXPOSE 3001
HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=5 \
    CMD wget --quiet --spider "http://127.0.0.1:${PORT}/" || exit 1
