FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY requirements.lock.txt ./
RUN pip install --no-cache-dir -r requirements.lock.txt \
    && groupadd --system foodify \
    && useradd --system --gid foodify --no-create-home foodify

COPY --chown=foodify:foodify app ./app
COPY --chown=foodify:foodify migrations ./migrations
COPY --chown=foodify:foodify scripts ./scripts
COPY --chown=foodify:foodify alembic.ini run.py ./
USER foodify
EXPOSE 8000
CMD ["python", "run.py", "--host", "0.0.0.0"]
