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

## Run the FastAPI server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 5000
```
---

## Postman Collection