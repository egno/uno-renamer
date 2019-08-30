FROM python:3.7

COPY . /app

RUN pip install --no-cache-dir -r /app/requirements.txt

WORKDIR /app

VOLUME ["/app","/opt/data/images"]

CMD ["python", "app.py"]

