FROM python:3.13.0-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists*

COPY requirements.txt ./

RUN pip3 install -r requirements.txt

COPY .streamlit/ ./.streamlit/
COPY src/ ./src/
COPY images/ ./images/
COPY app.py ./

EXPOSE 8000

ENTRYPOINT ["streamlit", "run", "./app.py", "--server.port=8000", "--server.address=0.0.0.0"]


