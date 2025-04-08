FROM python:3.9-slim

WORKDIR /app

COPY frontend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY frontend/ .

# Set default port for Streamlit
EXPOSE 8082

ENTRYPOINT ["streamlit", "run", "frontend.py", "--server.port=8082", "--server.address=0.0.0.0"]