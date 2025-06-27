FROM python:3.12-slim

WORKDIR /app
COPY . /app

ENV PATH="/opt/venv/bin:$PATH"

RUN python -m venv /opt/venv \
 && /opt/venv/bin/pip install --upgrade pip \
 && /opt/venv/bin/pip install -r requirements.txt

CMD ["python", "main.py"]
