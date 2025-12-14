# echo-fastapi

A FastAPI application using Poetry and Python 3.12.

## Requirements

- Python 3.12+
- Poetry

## Installation

```bash
poetry install
```

## Running the Application

```bash
poetry run uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

## API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`