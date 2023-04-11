FROM python:3.10-slim-buster

RUN mkdir /code

WORKDIR /code

COPY requirements.txt .

COPY app ./app

RUN pip install -r requirements.txt

CMD ["uvicorn", "app.main:app", "--host=0.0.0.0", "--port=8000"]
