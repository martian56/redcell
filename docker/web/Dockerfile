FROM oven/bun:1 AS build
WORKDIR /app

COPY package.json bun.lock ./
COPY apps/web/package.json ./apps/web/
COPY packages/api-client/package.json ./packages/api-client/
RUN bun install --frozen-lockfile

COPY . .

ARG VITE_API_MODE=http
ARG VITE_API_BASE_URL=/api/v1
ARG VITE_WS_URL=/api/v1/ws
ENV VITE_API_MODE=$VITE_API_MODE \
    VITE_API_BASE_URL=$VITE_API_BASE_URL \
    VITE_WS_URL=$VITE_WS_URL
RUN cd apps/web && bun run build

FROM nginx:1.27-alpine
COPY docker/web/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/apps/web/dist /usr/share/nginx/html
EXPOSE 80
