# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:alpine

RUN pip install --upgrade pip
WORKDIR /
RUN apk update
RUN apk add postgresql-dev gcc python3-dev musl-dev libffi-dev openssl-dev cargo
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5002

CMD ["python", "-m", "webapp.app"]
