# -------------------------------------------------------------------
# Stage 1: Build static assets with Node.js
# -------------------------------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /app

# Cache dependencies
COPY package*.json ./
RUN npm ci

# Copy source and build
COPY . .

# Pass API URL at build time (defaults to root relative path for Nginx reverse proxy)
ARG VITE_API_URL=/api/v1
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# -------------------------------------------------------------------
# Stage 2: Serve with unprivileged, slim Nginx
# -------------------------------------------------------------------
FROM nginx:alpine

# Remove default static files and config
RUN rm -rf /usr/share/nginx/html/* /etc/nginx/conf.d/default.conf

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy production build from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]