FROM python:3.10-slim
WORKDIR /app
COPY server.py .
COPY webrtc_remote_recorder.html .
COPY cert.pem .
COPY key.pem .
RUN pip install --no-cache-dir quart quart-cors nest-asyncio uvicorn
EXPOSE 5000
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "5000", "--ssl-keyfile", "key.pem", "--ssl-certfile", "cert.pem"]