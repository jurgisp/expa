FROM node:latest as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:stable-alpine as run
COPY --from=build /app/dist /usr/share/nginx/html
RUN chmod -R 755 /usr/share/nginx/html
# Forward /api requests to the sidecar container
RUN echo "server {" \
         "    listen 80;" \
         "    location / {" \
         "        root /usr/share/nginx/html;" \
         "        index index.html;" \
         "        try_files \$uri \$uri/ /index.html;" \
         "    }" \
         "    location /api/ {" \
         "        proxy_pass http://api:8010/;" \
         "        proxy_http_version 1.1;" \
         "        proxy_set_header Upgrade \$http_upgrade;" \
         "        proxy_set_header Connection 'upgrade';" \
         "        proxy_set_header Host \$host;" \
         "        proxy_cache_bypass \$http_upgrade;" \
         "    }" \
         "}" > /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
