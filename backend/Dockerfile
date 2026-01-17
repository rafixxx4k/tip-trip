FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
# Copy alembic config so migrations can be run inside the image
COPY alembic.ini ./
COPY alembic ./alembic

EXPOSE 8000

# Use a small startup script which runs migrations then launches uvicorn
RUN sed -i 's/\r$//' ./app/start.sh && chmod +x ./app/start.sh || true
SHELL ["sh", "-c"]
CMD sed -i 's/\r$//' ./app/start.sh && exec sh ./app/start.sh
