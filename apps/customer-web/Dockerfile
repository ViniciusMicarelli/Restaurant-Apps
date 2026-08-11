# syntax=docker/dockerfile:1.7
# Build multi-stage: compila o SPA (Vite/React) no estágio `builder`, serve
# o `dist/` estático via Nginx no estágio final — mesma ideia dos serviços
# Python (imagem final enxuta, sem toolchain de build).
#
# Contexto de build DEVE ser a raiz do repositório (não `apps/customer-web`),
# mesmo motivo dos `services/*/Dockerfile`: consistência de path nos COPY
# abaixo. Ver `infra/docker/docker-compose.prod.yml`.

FROM node:26-alpine AS builder
WORKDIR /app
COPY apps/customer-web/package.json apps/customer-web/package-lock.json* ./
RUN npm ci
COPY apps/customer-web/ ./
# Vite embute `VITE_*` no bundle em BUILD time (não runtime) — precisam
# chegar como build args da Railway, não só variável de ambiente do
# serviço rodando depois (ver docs/deploy/railway_setup.md).
ARG VITE_RESTAURANT_SERVICE_URL
ARG VITE_MENU_SERVICE_URL
ARG VITE_DINING_SERVICE_URL
ARG VITE_ORDER_SERVICE_URL
ARG VITE_PAYMENT_SERVICE_URL
ARG VITE_DEFAULT_RESTAURANT_SLUG
ENV VITE_RESTAURANT_SERVICE_URL=${VITE_RESTAURANT_SERVICE_URL} \
    VITE_MENU_SERVICE_URL=${VITE_MENU_SERVICE_URL} \
    VITE_DINING_SERVICE_URL=${VITE_DINING_SERVICE_URL} \
    VITE_ORDER_SERVICE_URL=${VITE_ORDER_SERVICE_URL} \
    VITE_PAYMENT_SERVICE_URL=${VITE_PAYMENT_SERVICE_URL} \
    VITE_DEFAULT_RESTAURANT_SLUG=${VITE_DEFAULT_RESTAURANT_SLUG}
RUN npm run build

FROM nginx:1.31-alpine AS runtime
COPY apps/customer-web/nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=builder /app/dist /usr/share/nginx/html
# Porta dinâmica (Railway injeta `$PORT` em runtime) — o entrypoint padrão
# da imagem processa o template acima com `envsubst` antes de subir o
# Nginx; default aqui só cobre `docker compose`/execução local sem a var
# setada explicitamente.
ENV PORT=3000
EXPOSE 3000
HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=5 \
    CMD wget --quiet --spider "http://127.0.0.1:${PORT}/" || exit 1
