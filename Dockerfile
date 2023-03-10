FROM python:3.8

WORKDIR /webapp

COPY requirements.txt .

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

COPY webapp/* .

ENTRYPOINT [ "python" ]

CMD [ "app.py" ]