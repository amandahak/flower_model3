FROM python:3.9

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY main.py utils.py models.py ./

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8888"]