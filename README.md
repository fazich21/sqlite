# Task Manager API

A RESTful Task Manager API developed using **Python, FastAPI, and Pydantic**, featuring CRUD operations, JWT authentication, role-based authorization, and task searching.

## Features
- Create, retrieve, update, and delete tasks.
- Search tasks by title.
- User registration and login using JWT authentication.
- Password hashing using bcrypt.
- Role-based access control (User/Admin).
- Pydantic request validation.
- HTTP exception handling.
- Interactive API documentation with Swagger UI.

## Technologies Used
Python, FastAPI, Pydantic, SQLAlchemy, SQLite, JWT, Bcrypt, Uvicorn, REST APIs.

## Installation & Setup

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

## API Documentation
- Swagger UI: `/docs`
- ReDoc: `/redoc`

## Key Learning Outcomes
REST API development, CRUD operations, authentication, authorization, database integration, request validation, and backend development.
