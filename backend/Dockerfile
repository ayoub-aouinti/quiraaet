# Contexte de build : racine du dépôt (docker compose build web)
FROM node:20-slim AS front
WORKDIR /front
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /srv
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/ backend/
COPY data/ data/
COPY fonts/ fonts/
COPY --from=front /front/dist frontend/dist
WORKDIR /srv/backend
ENV QIRAAT_DATA_DIR=/srv/data QIRAAT_FONTS_DIR=/srv/fonts QIRAAT_FRONTEND_DIST=/srv/frontend/dist
RUN DJANGO_SECRET_KEY=build python manage.py collectstatic --noinput
EXPOSE 8000
# migrate à chaque démarrage ; l'import (long) se lance à la main : docker compose exec web python manage.py import_data
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn config.wsgi -b 0.0.0.0:8000 -w 3"]
