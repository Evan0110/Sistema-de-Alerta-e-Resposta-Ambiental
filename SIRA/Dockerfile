FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501 5000
CMD ["sh", "-c", "mkdir -p /app/data && python database.py && (python backend.py &) && python -m streamlit run frontend.py --server.address=0.0.0.0"]
