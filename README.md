Task Manager API

A simple RESTful Task Manager API built with Python, FastAPI, and Pydantic. This project demonstrates CRUD operations, request validation, task searching, and HTTP exception handling.

Features

Create Tasks: Add new tasks with a title and completion status.

Get All Tasks: Retrieve all stored tasks.

Get Task by ID: Retrieve an individual task using its ID.

Update Tasks: Modify an existing task.

Delete Tasks: Remove a task by its ID.

Search Tasks: Search tasks by title using case-insensitive matching.

Input Validation: Validate request data using Pydantic models.

Error Handling: Return HTTP 404 errors when a task ID does not exist.

Interactive API Documentation: Test endpoints using Swagger UI.

Technologies Used

Python

FastAPI

Pydantic

Uvicorn

Installation and Setup

1. Clone the repository

git clone <your-repository-url>
cd <your-project-folder>

2. Create a virtual environment

python -m venv venv

3. Activate the virtual environment

Windows:

venv\Scripts\activate

4. Install dependencies

pip install fastapi uvicorn

5. Run the application

If your Python file is named main.py:

uvicorn main:app --reload

Replace main with your actual filename if it is different.

API Endpoints

Method

Endpoint

Description

GET

/

Check API status

POST

/tasks

Create a task

GET

/tasks

Retrieve all tasks

GET

/tasks/search?title=python

Search tasks by title

GET

/tasks/{task_id}

Retrieve a task by ID

PUT

/tasks/{task_id}

Update a task

DELETE

/tasks/{task_id}

Delete a task

Example Request

Create a task using POST /tasks:

{
  "title": "Learn FastAPI",
  "completed": false
}

Example response:

{
  "message": "Task created",
  "task": {
    "title": "Learn FastAPI",
    "completed": false
  }
}

Interactive Documentation

After starting the application, open:

Swagger UI: http://127.0.0.1:8000/docs

ReDoc: http://127.0.0.1:8000/redoc

You can use these interfaces to test all available API endpoints.

Current Limitations

Tasks are stored in an in-memory Python list. The data is lost when the application restarts. Database integration and persistent task IDs can be added in future improvements.

Learning Objectives

This project demonstrates practical experience with REST APIs, FastAPI routing, Pydantic data validation, HTTP methods, query and path parameters, CRUD operations, and error handling.

Authentication and Authorization

All code for this is in auth.py.

Authentication ("who are you?"): register at POST /auth/register, then log in at POST /auth/login to get a token (JWT). Send the token with every request in the header: Authorization: Bearer <token>. Passwords are stored hashed with bcrypt in users.json.

Authorization ("what are you allowed to do?"): every user has a role, "user" or "admin". The first person to register becomes admin.

Tasks (main.py): login required. Users see and edit only their own tasks, admins see all. Only admins can delete.

Documents (json_api.py): any logged-in user can read and search. Only admins can create, update or delete.

Testing in Swagger: open /docs, register, click the "Authorize" button, enter your username and password, and every request will send your token automatically.

Install: pip install -r requirements.txt
