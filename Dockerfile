FROM python:3.8
RUN apt-get update && apt-get install -y cmake
WORKDIR /webapp

COPY requirements.txt .

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

COPY . .

ENTRYPOINT [ "python" ]

CMD [ "app.py" ]