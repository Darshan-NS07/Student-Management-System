# Student Management System — Microservices Architecture

A full-stack Student Management System built using React, FastAPI, and SQLite. The project follows a microservices architecture, with separate services for authentication, student management, and course management, accessed through a centralized API Gateway.

## Features

- User registration and login
- JWT-based authentication
- Password hashing
- Student CRUD operations: create, read, update, and delete
- Course CRUD operations: create, read, update, and delete
- Input validation and error handling
- Centralized API Gateway
- React frontend
- SQLite database for persistent storage
- Swagger UI for API exploration

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | React, Vite, JavaScript |
| Backend | Python, FastAPI |
| API Gateway | FastAPI, HTTPX |
| Authentication | JWT |
| Database | SQLite |
| ORM | SQLAlchemy |
| API Documentation | Swagger UI / OpenAPI |
| Version Control | Git, GitHub |

## Architecture

The frontend communicates with the API Gateway. The gateway forwards requests to the appropriate backend service.

- **Frontend:** User interface for authentication, dashboard, students, and courses.
- **Auth Service:** User registration, login, password verification, and token generation.
- **Student Service:** Student record management.
- **Course Service:** Course record management.
- **API Gateway:** Central entry point for frontend API requests and routing to backend services.

### Service Ports

| Service | Local URL |
|---|---|
| Auth Service | `http://127.0.0.1:8000` |
| Student Service | `http://127.0.0.1:8001` |
| Course Service | `http://127.0.0.1:8002` |
| API Gateway | `http://127.0.0.1:8003` |
| Frontend | `http://localhost:5173` |

## Project Structure

```text
Student_Management/
├── api-gateway/
├── auth-service/
├── student-service/
├── course-service/
├── frontend/
├── .gitignore
└── README.md
```

Each backend service maintains its own application code, dependencies, configuration, and database.

## Prerequisites

Install the following before running the project:

- Python
- Node.js and npm
- Git (for version control)

## Setup and Installation

### 1. Clone the repository

```cmd
git clone YOUR_GITHUB_REPOSITORY_URL
cd Student_Management
```

Replace `YOUR_GITHUB_REPOSITORY_URL` with the repository URL.

### 2. Configure the backend services

For each backend directory (`auth-service`, `student-service`, `course-service`, and `api-gateway`):

```cmd
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
```

Configure the required environment variables using the service's environment configuration. Use new local secrets; do not reuse or publish private production secrets.

### 3. Start the backend services

Run each command in a separate Windows CMD window from the project root.

**Auth Service**

```cmd
cd /d C:\Users\ashwa\Desktop\Student_Management\auth-service
venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

**Student Service**

```cmd
cd /d C:\Users\ashwa\Desktop\Student_Management\student-service
venv\Scripts\activate
uvicorn app.main:app --reload --port 8001
```

**Course Service**

```cmd
cd /d C:\Users\ashwa\Desktop\Student_Management\course-service
venv\Scripts\activate
uvicorn app.main:app --reload --port 8002
```

**API Gateway**

```cmd
cd /d C:\Users\ashwa\Desktop\Student_Management\api-gateway
venv\Scripts\activate
uvicorn app.main:app --reload --port 8003
```

Update the gateway's service URLs and JWT configuration to match your local environment.

### 4. Start the frontend

Open another CMD window:

```cmd
cd /d C:\Users\ashwa\Desktop\Student_Management\frontend
npm install
```

Create or configure `frontend/.env`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8003
```

Then run:

```cmd
npm run dev
```

Open `http://localhost:5173` in your browser.

## API Documentation

Once the backend services are running, use the Swagger UI pages:

- API Gateway: `http://127.0.0.1:8003/docs`
- Auth Service: `http://127.0.0.1:8000/docs`
- Student Service: `http://127.0.0.1:8001/docs`
- Course Service: `http://127.0.0.1:8002/docs`

The API Gateway is the intended entry point for frontend requests.



## Current Scope

This project includes authentication, student CRUD, course CRUD, and centralized API routing. Student records and course records are managed independently; student-to-course enrollment is not currently implemented.



## Author

**Darshan NS**

A full-stack project demonstrating Python backend development, REST APIs, JWT authentication, React integration, and microservices architecture.
