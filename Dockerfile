FROM python:3.10-slim

COPY . /app
WORKDIR  /app

# Environment variable
ENV PORT 8080

# Install required packages
RUN apt-get update -y \
    && apt-get install -y tini \
    && pip install --upgrade pip \
    && pip install -r requirements.txt

# Use tini to manage zombie processes and signal forwarding
ENTRYPOINT ["/usr/bin/tini", "--"]

# Pass the startup script as arguments to Tini
EXPOSE 8080
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT}