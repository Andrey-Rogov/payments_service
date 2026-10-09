FROM python:3.12

WORKDIR /payment_consumer

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["faststream", "run", "main:app"]