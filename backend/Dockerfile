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
RUN chmod +x ./app/start.sh || true
CMD ["sh", "./app/start.sh"]
