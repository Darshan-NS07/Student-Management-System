
import os
from contextlib import asynccontextmanager
from typing import Annotated
import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import Student
from app.schemas import StudentCreate, StudentResponse, StudentUpdate

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

if not JWT_SECRET_KEY or len(JWT_SECRET_KEY) < 32:
    raise RuntimeError("Configure a JWT_SECRET_KEY of at least 32 characters in student-service/.env")

security = HTTPBearer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Student Service API", version="1.0.0", lifespan=lifespan)


def get_current_user(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        if not payload.get("sub") or not payload.get("exp"):
            raise HTTPException(status_code=401, detail="Invalid token.")
        return payload
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")


CurrentUser = Annotated[dict, Depends(get_current_user)]
Database = Annotated[Session, Depends(get_db)]


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "student-service"}


@app.post("/students", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(student_data: StudentCreate, db: Database, current_user: CurrentUser):
    existing_student = db.query(Student).filter(func.lower(Student.email) == str(student_data.email).lower()).first()
    if existing_student:
        raise HTTPException(status_code=409, detail="A student with this email already exists.")

    student = Student(**student_data.model_dump())
    try:
        db.add(student)
        db.commit()
        db.refresh(student)
        return student
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Unable to create student.")


@app.get("/students", response_model=list[StudentResponse])
def get_students(db: Database, current_user: CurrentUser, skip: int = Query(default=0, ge=0), limit: int = Query(default=100, ge=1, le=100)):
    return db.query(Student).order_by(Student.id).offset(skip).limit(limit).all()


@app.get("/students/{student_id}", response_model=StudentResponse)
def get_student(student_id: int, db: Database, current_user: CurrentUser):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")
    return student


@app.put("/students/{student_id}", response_model=StudentResponse)
def update_student(student_id: int, student_data: StudentUpdate, db: Database, current_user: CurrentUser):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    update_data = student_data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="Provide at least one field to update.")
    if any(value is None for value in update_data.values()):
        raise HTTPException(status_code=422, detail="Fields cannot be null.")

    if "email" in update_data:
        email = str(update_data["email"]).lower()
        existing_student = db.query(Student).filter(func.lower(Student.email) == email, Student.id != student_id).first()
        if existing_student:
            raise HTTPException(status_code=409, detail="Another student already uses this email.")
        update_data["email"] = email

    for field, value in update_data.items():
        setattr(student, field, value)

    try:
        db.commit()
        db.refresh(student)
        return student
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Unable to update student.")


@app.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(student_id: int, db: Database, current_user: CurrentUser):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    try:
        db.delete(student)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Unable to delete student")
