FROM python:3.11-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir ".[server]"

EXPOSE 8000
CMD ["uvicorn", "coding_agent.server:app", "--host", "0.0.0.0", "--port", "8000"]
