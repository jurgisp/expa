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
EXPOSE ${PORT}
COPY --from=build /app/dist /usr/share/nginx/html
RUN chmod -R 755 /usr/share/nginx/html
COPY nginx.conf /etc/nginx/templates/default.conf.template
CMD ["nginx", "-g", "daemon off;"]
