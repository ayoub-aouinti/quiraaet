# السياق: جذر المستودع. docker build -f apps/api/Dockerfile .
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
COPY apps/api/package.json apps/api/
COPY apps/web/package.json apps/web/
COPY apps/mobile/package.json apps/mobile/
COPY packages/shared/package.json packages/shared/
RUN npm ci -w @jamei/api
COPY apps/api apps/api
RUN npm run build -w @jamei/api

FROM node:22-alpine
ENV NODE_ENV=production PORT=3000 HOST=0.0.0.0
WORKDIR /app
COPY --from=build /app/node_modules node_modules
COPY --from=build /app/apps/api/dist apps/api/dist
COPY apps/api/package.json apps/api/
COPY apps/api/scripts apps/api/scripts
COPY db/app_schema.sql db/app_schema.sql
COPY package.json ./
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD wget -qO- http://127.0.0.1:3000/api/health || exit 1
USER node
CMD ["node", "apps/api/dist/main.js"]
