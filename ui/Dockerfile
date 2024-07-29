FROM node:latest as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Nginx forwards /api requests to the sidecar container
FROM nginx:stable-alpine as run
ENV PORT="80"
ENV API_HOST="127.0.0.1:8010"
# "off" means no auth, for any other value it is enabled
ENV AUTH_BASIC="off"
ENV AUTH_USER="expa"
ENV AUTH_PASSWORD="expa"
EXPOSE ${PORT}

RUN apk add --no-cache apache2-utils

COPY --from=build /app/dist /usr/share/nginx/html
RUN chmod -R 755 /usr/share/nginx/html
COPY nginx.conf /etc/nginx/templates/default.conf.template

CMD /bin/sh -c 'htpasswd -b -c /etc/nginx/.htpasswd ${AUTH_USER} ${AUTH_PASSWORD} && /docker-entrypoint.sh nginx -g "daemon off;"'
