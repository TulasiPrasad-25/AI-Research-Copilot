FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir streamlit==1.35.0 httpx==0.27.0 python-dotenv==1.0.1

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
