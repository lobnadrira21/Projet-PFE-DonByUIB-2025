FROM node:20 AS build
WORKDIR /app

COPY package*.json ./
# ✅ Ignore peer-dep conflicts without touching your deps
RUN npm config set legacy-peer-deps true
RUN npm ci

COPY . .
RUN npm run build -- --configuration production

FROM nginx:alpine
ARG DIST_DIR=dist
COPY --from=build /app/${DIST_DIR} /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
