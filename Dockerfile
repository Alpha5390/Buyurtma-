FROM python:3.12-slim

# C kompilyator va pip uchun kerakli kutubxonalar
RUN apt-get update && apt-get install -y build-essential gcc

WORKDIR /app
COPY . /app

ENV PATH="/opt/venv/bin:$PATH"

RUN python -m venv /opt/venv \
 && /opt/venv/bin/pip install --upgrade pip \
 && /opt/venv/bin/pip uninstall -y telegram \
 && /opt/venv/bin/pip install -r requirements.txt

CMD ["python", "main.py"]
