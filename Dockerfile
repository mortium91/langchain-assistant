FROM python:3-slim-buster

RUN mkdir /code

WORKDIR /code

COPY requirements.txt .

COPY . .


RUN pip install -r requirements.txt


CMD ["uvicorn", "main:app", "--host=0.0.0.0", "--port=8000"]


# docker build -t fastapi .
# docker compose up