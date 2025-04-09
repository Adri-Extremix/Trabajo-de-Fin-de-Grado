FROM python:3.12

WORKDIR /app

COPY requirements.txt .
COPY proxy.py .
RUN pip install -r requirements.txt

EXPOSE 8080

CMD ["python", "proxy.py"]
