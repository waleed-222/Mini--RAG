# Mini-RAG

This is a minimal implementation of the RAG model for question answering.

## Requirements

- python 3.10 or later

### Install Environment

1) Install MiniConda 

2) Install python 

3) Create environment using this command:

```bash
conda create -n your_environment_name python=3.8
```
4) Activate your Environment using this command:

```bash
conda activate your_environment_name
```
---

## Installation

```bash
pip install -r rquirement.txt
```

### setup environment variables

```bash
cp .env.example .env
```
set your environment variables in the `.env` file. Like `SECRETE_API_KEY`value.

### Run Alembic Migration
```bash
$ alembic upgrade head
```
Set your environment variables in the .env file. Like OPENAI_API_KEY value.

### Run Docker Compose Services
```bash
$ cd docker
$ cp .env.example .env
```
- update .env with your credentials
```bash
$ cd docker
$ sudo docker compose up -d
```
---

## Access Services

- **FastAPI**: http://localhost:8000
- **Flower Dashboard**: http://localhost:5555 (admin/password from env)
- **Grafana**: http://localhost:3000
- **Prometheus**: http://localhost:9090

---

## Run the FastAPI server (Development Mode)

```bash
$ uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
---

# Celery (Development Mode)

For development, you can run Celery services manually instead of using Docker:

To Run the **Celery worker**, you need to run the following command in a separate terminal:

```bash
$ python -m celery -A celery_app worker --queues=default,file_processing,data_indexing --loglevel=info
```

To run the **Beat scheduler**, you can run the following command in a separate terminal:

```bash
$ python -m celery -A celery_app beat --loglevel=info
```

To Run **Flower Dashboard**, you can run the following command in a separate terminal:

```bash
$ python -m celery -A celery_app flower --conf=flowerconfig.py
```


open your browser and go to `http://localhost:5555` to see the dashboard.

---

## Acknowledgements
This project builds upon the foundational work from bakrianoo/mini-rag. The original repository provided the core RAG application logic, models, and database schemas.

Our Enhancements is the Additional LLM Providers – Integrated Gemini and Groq support alongside existing providers.

---