# ---- Build stage ----
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
ENV NODE_ENV=development
ENV NPM_CONFIG_PRODUCTION=false
ENV NPM_CONFIG_OMIT=
RUN npm ci --include=dev

COPY . .

# API URL relative so nginx proxy handles routing
ARG VITE_API_URL=/api
ARG VITE_DAILY_READING_URL=/api/daily-reading
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_DAILY_READING_URL=$VITE_DAILY_READING_URL

RUN npx --yes vite build

# ---- Runtime stage ----
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
