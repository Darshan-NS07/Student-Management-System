
import os
from contextlib import asynccontextmanager
from typing import Annotated

import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import Course
from app.schemas import CourseCreate, CourseResponse, CourseUpdate

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

if not JWT_SECRET_KEY or len(JWT_SECRET_KEY) < 32:
    raise RuntimeError("Configure a JWT_SECRET_KEY of at least 32 characters in course-service/.env")

security = HTTPBearer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Course Service API", version="1.0.0", lifespan=lifespan)


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
    return {"status": "healthy", "service": "course-service"}


@app.post("/courses", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(course_data: CourseCreate, db: Database, current_user: CurrentUser):
    existing_course = db.query(Course).filter(Course.code == course_data.code).first()
    if existing_course:
        raise HTTPException(status_code=409, detail="A course with this code already exists.")

    course = Course(**course_data.model_dump())
    try:
        db.add(course)
        db.commit()
        db.refresh(course)
        return course
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="A course with this code already exists.")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Unable to create course.")


@app.get("/courses", response_model=list[CourseResponse])
def get_courses(db: Database, current_user: CurrentUser, skip: int = Query(default=0, ge=0), limit: int = Query(default=100, ge=1, le=100)):
    return db.query(Course).order_by(Course.id).offset(skip).limit(limit).all()


@app.get("/courses/{course_id}", response_model=CourseResponse)
def get_course(course_id: int, db: Database, current_user: CurrentUser):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")
    return course


@app.put("/courses/{course_id}", response_model=CourseResponse)
def update_course(course_id: int, course_data: CourseUpdate, db: Database, current_user: CurrentUser):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")

    update_data = course_data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="Provide at least one field to update.")
    if any(value is None for value in update_data.values()):
        raise HTTPException(status_code=422, detail="Fields cannot be null.")

    if "code" in update_data:
        existing_course = db.query(Course).filter(Course.code == update_data["code"], Course.id != course_id).first()
        if existing_course:
            raise HTTPException(status_code=409, detail="Another course already uses this code.")

    for field, value in update_data.items():
        setattr(course, field, value)

    try:
        db.commit()
        db.refresh(course)
        return course
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="A course with this code already exists.")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Unable to update course.")


@app.delete("/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(course_id: int, db: Database, current_user: CurrentUser):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")

    try:
        db.delete(course)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Unable to delete course.")
