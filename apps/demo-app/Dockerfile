FROM python:3.11-slim

WORKDIR /site

COPY . .

EXPOSE 3010

CMD ["python", "-m", "http.server", "3010", "--bind", "0.0.0.0"]
