# docker/Dockerfile.ml — ML worker (training/inference heavy deps)
FROM python:3.10-slim

ENV APP_HOME=/ml
WORKDIR ${APP_HOME}

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libgomp1 curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# предполагаем ml/requirements.txt с torch/catboost/shap
COPY ml/requirements.txt ${APP_HOME}/requirements.txt
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r ${APP_HOME}/requirements.txt

# copy only ml-related code and data
COPY ml ${APP_HOME}/ml
COPY app/services ${APP_HOME}/services
COPY data ${APP_HOME}/data

EXPOSE 9000

CMD ["python", "-u", "ml/serve_model.py"]
