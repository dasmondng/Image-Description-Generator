FROM python:3.11-slim

WORKDIR /app

COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set default port for Streamlit
EXPOSE 8082

ENTRYPOINT ["streamlit", "run", "frontend.py", "--server.port=8082", "--server.address=0.0.0.0"]
