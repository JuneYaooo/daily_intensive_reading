FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
ENV PIP_DEFAULT_TIMEOUT=120
RUN pip install --no-cache-dir --retries 10 --timeout 120 -i https://pypi.tuna.tsinghua.edu.cn/simple --prefer-binary -r requirements.txt

COPY . .

RUN chmod +x docker-entrypoint.sh

EXPOSE 5000

ENTRYPOINT ["./docker-entrypoint.sh"]
