FROM node:20-alpine AS build

WORKDIR /app

COPY package-lock.json ./
RUN npm ci

COPY . .
# Baked in at build time, so VITE_API_BASE_URL must point at the public
# backend URL (not an internal Docker hostname) when this is built.
RUN npm run build

FROM nginx:1.27-alpine

COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
