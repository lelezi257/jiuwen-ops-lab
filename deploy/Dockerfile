FROM python:3.11-slim-bookworm
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y --no-install-recommends git docker.io && rm -rf /var/lib/apt/lists/*
COPY deploy /app/deploy
COPY scripts /app/scripts
COPY lab /app/lab
COPY contracts /app/contracts
COPY web /app/web
CMD ["python","-m","uvicorn","lab.control:app","--host","0.0.0.0","--port","8080"]
