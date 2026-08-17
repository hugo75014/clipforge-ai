# =============================================================================
# Frontend image — multi-stage: build with Node, serve with nginx
# =============================================================================
FROM node:20-alpine AS builder

WORKDIR /app

# Install deps with layer caching
COPY frontend/package.json frontend/package-lock.json* /app/
RUN npm install --no-audit --no-fund

COPY frontend/ /app/
RUN npm run build

# ---- runtime ----
FROM nginx:1.27-alpine

# Replace default config with one that proxies /api & /media to the backend
RUN rm /etc/nginx/conf.d/default.conf
COPY docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
HEALTHCHECK CMD wget -qO- http://localhost/healthz || exit 1
