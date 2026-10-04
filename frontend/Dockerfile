FROM node:22-alpine AS build

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .

# Empty default: browser calls same-origin /api/*; nginx proxies to BACKEND_API_URL.
ARG VITE_API_BASE_URL=
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

FROM nginx:1.27-alpine AS production

# Rendered at container start via /docker-entrypoint.d/20-envsubst-on-templates.sh
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
# Override at run time (e.g. http://<ecs-public-ip>:8000). Ephemeral ECS IPs require
# updating this env and restarting the frontend task when the backend address changes.
ENV BACKEND_API_URL=http://127.0.0.1:8000
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://127.0.0.1/health || exit 1

CMD ["nginx", "-g", "daemon off;"]

FROM node:22-alpine AS development

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
