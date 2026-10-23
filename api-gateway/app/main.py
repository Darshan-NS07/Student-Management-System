
import os
from contextlib import asynccontextmanager
from typing import Annotated

import httpx
import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from starlette.responses import Response
from pydantic import BaseModel, ConfigDict, EmailStr, Field

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://127.0.0.1:8000").rstrip("/")
STUDENT_SERVICE_URL = os.getenv("STUDENT_SERVICE_URL", "http://127.0.0.1:8001").rstrip("/")
COURSE_SERVICE_URL = os.getenv("COURSE_SERVICE_URL", "http://127.0.0.1:8002").rstrip("/")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

if not JWT_SECRET_KEY or len(JWT_SECRET_KEY) < 32:
    raise RuntimeError("Configure the same JWT_SECRET_KEY as Auth Service in api-gateway/.env")

security = HTTPBearer(auto_error=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient(timeout=15.0) as client:
        app.state.http_client = client
        yield


app = FastAPI(title="Student Management API Gateway", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def verify_token(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)]) -> dict:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication token is required.")
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        if not payload.get("sub") or not payload.get("exp"):
            raise HTTPException(status_code=401, detail="Invalid token.")
        return payload
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")


CurrentUser = Annotated[dict, Depends(verify_token)]


async def forward_request(request: Request, base_url: str, path: str, require_auth: bool = True) -> Response:
    headers = {}
    content_type = request.headers.get("content-type")
    if content_type:
        headers["Content-Type"] = content_type
    authorization = request.headers.get("authorization")

    if require_auth:
        if not authorization:
            raise HTTPException(status_code=401, detail="Authentication token is required.")
        try:
            scheme, token = authorization.split(" ", 1)
            if scheme.lower() != "bearer" or not token:
                raise ValueError("Invalid authorization header")
            jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        except (ValueError, InvalidTokenError):
            raise HTTPException(status_code=401, detail="Invalid or expired token.")

        headers["Authorization"] = authorization

    content = await request.body()
    query_string = request.url.query
    url = f"{base_url}/{path.lstrip('/')}"
    if query_string:
        url = f"{url}?{query_string}"

    try:
        client: httpx.AsyncClient = request.app.state.http_client
        upstream_response = await client.request(
            method=request.method,
            url=url,
            content=content if content else None,
            headers=headers,
        )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="A backend service timed out.")
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Unable to connect to a backend service.")

    excluded_headers = {"content-encoding", "content-length", "transfer-encoding", "connection"}
    response_headers = {
        key: value for key, value in upstream_response.headers.items()
        if key.lower() not in excluded_headers
    }

    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        headers=response_headers,
        media_type=upstream_response.headers.get("content-type"),
    )


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "api-gateway"}



class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


@app.post("/auth/register")
async def register(data: RegisterRequest, request: Request):
    return await forward_request(request,AUTH_SERVICE_URL,"auth/register", require_auth=False,)


@app.post("/auth/login")
async def login(data: LoginRequest, request: Request):
    return await forward_request(request, AUTH_SERVICE_URL, "auth/login", require_auth=False,)


@app.get("/auth/me")
async def get_me(request: Request):
    return await forward_request(request,AUTH_SERVICE_URL,"auth/me",require_auth=True,)




@app.api_route("/students", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
@app.api_route("/students/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def student_routes(request: Request, path: str = ""):
    return await forward_request(request, STUDENT_SERVICE_URL, f"students/{path}" if path else "students")


@app.api_route("/courses", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
@app.api_route("/courses/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def course_routes(request: Request, path: str = ""):
    return await forward_request(request, COURSE_SERVICE_URL, f"courses/{path}" if path else "courses")


@app.get("/auth-health")
async def auth_health(request: Request):
    return await forward_request(request, AUTH_SERVICE_URL, "health", require_auth=False)


@app.get("/students-health")
async def students_health(request: Request):
    return await forward_request(request, STUDENT_SERVICE_URL, "health", require_auth=False)


@app.get("/courses-health")
async def courses_health(request: Request):
    return await forward_request(request, COURSE_SERVICE_URL, "health", require_auth=False)
