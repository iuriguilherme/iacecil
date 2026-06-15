FROM python:3.11

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir .[all]

RUN mkdir -p instance && \
    cp -r docs/instance.example/* instance/

EXPOSE 8000/tcp

CMD ["iacecil", "connectors_v3"]
