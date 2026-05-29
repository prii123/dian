# ---- Build stage ----
FROM node:24-alpine AS builder

WORKDIR /app

ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

COPY package*.json ./
RUN npm ci

COPY . .

ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# ---- Production stage ----
FROM node:24-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

RUN apk add --no-cache curl

# Copiar la carpeta .next/standalone que contiene el servidor autocontienido
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000

# Script de inicio para mejor debugging
RUN echo '#!/bin/sh' > /start.sh && \
    echo 'echo "Starting Next.js server..."' >> /start.sh && \
    echo 'exec node server.js' >> /start.sh && \
    chmod +x /start.sh

ENTRYPOINT ["/start.sh"]
