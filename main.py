import os
import time
import traceback
import asyncio
from fastapi import FastAPI, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, FileResponse, Response
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from app.common.jobs.delete_folder_contents_job import start_scheduler_delete_folder_contents
from app.common.jobs.reset_generation_limits_job import start_scheduler_reset_generation_limits
from app.common.middlewares.logging_middleware import LoggingMiddleware, db_handler
from app.core.admin_setup import setup_admin
from app.dependencies.db.database import async_session_maker, get_async_session
from app.core.auth.auth import verify_token
from app.routers.api import logs, present, users, settings, tasks, generation, authentication
from app.routers.ws import status
from pydantic import BaseModel
import logging

# ✅ Создаём FastAPI-приложение
app = FastAPI()

# ✅ Настраиваем CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://slides.citorleu.kz", "https://slides.citorleu.kz",
        "http://localhost:1415", "http://localhost:6565"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_admin(app)

# ✅ Логирование
app.add_middleware(LoggingMiddleware)
templates = Jinja2Templates(directory="app/templates")


@app.middleware("http")
async def catch_all_middleware(request: Request, call_next):
    """
    ✅ Middleware раздаёт статику, но если путь НЕ относится к `/db` или `/admin`,
    и НЕ является файлом, возвращаем `index.html`.
    """
    path = request.url.path
    logging.info(f"Requested path: {path}")  # Заменили print() на логирование

    # ✅ Проверяем, является ли путь файлом в `pptx_static`
    static_pptx_path = f"./pptx_static{path.replace('/pptx_static', '')}"
    if os.path.exists(static_pptx_path) and os.path.isfile(static_pptx_path):
        return FileResponse(static_pptx_path)

    # ✅ Проверяем, является ли путь файлом в `templates/static`
    static_file_path = f"./app/templates{path}"
    if os.path.exists(static_file_path) and os.path.isfile(static_file_path):
        return FileResponse(static_file_path)

    # ✅ Пропускаем API и админку
    if path.startswith(("/api", "/admin")):
        return await call_next(request)

    # ✅ Если это НЕ статика и НЕ API/админка → отдаём `index.html`
    return templates.TemplateResponse("index.html", {"request": request})


@app.on_event("startup")
async def startup_event():
    """Запуск планировщиков при старте сервера."""
    start_scheduler_reset_generation_limits(async_session_maker)
    start_scheduler_delete_folder_contents()


@app.middleware("http")
async def add_db_session_to_request(request: Request, call_next):
    async for session in get_async_session():  # Используем async for для генератора
        request.state.db_session = session
        response = await call_next(request)
        return response


# Подключение маршрутизаторов с зависимостью verify_token
app.include_router(
    generation.router,
    prefix="/api/generation",
    tags=["Generation"],
    dependencies=[Depends(verify_token)]
)
app.include_router(
    tasks.router,
    prefix="/api/tasks",
    tags=["Tasks"],
)
app.include_router(
    users.router,
    prefix="/api/users",
    tags=["Users"],
    dependencies=[Depends(verify_token)]
)
app.include_router(
    logs.router,
    prefix="/logs",
    tags=["Logs"],
    dependencies=[Depends(verify_token)]
)
app.include_router(
    present.router,
    prefix="/api/present",
    tags=["Present"],
    dependencies=[Depends(verify_token)]
)
app.include_router(
    authentication.router,
    prefix="/api/auth",
    tags=["Authentication"],
)
app.include_router(
    settings.router,
    prefix="/api/settings",
    tags=["Settings"],
)
app.include_router(
    status.router,
    prefix="/ws/status",
    tags=["Settings"],
)


class LoginRequest(BaseModel):
    login: str
    password: str


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    # Проверяем, начинается ли путь с "/db"
    if request.url.path.startswith("/db"):
        return JSONResponse(
            content={"detail": "Not Found"},
            status_code=404,
        )
    return templates.TemplateResponse("index.html", {"request": request})


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    stack_trace = traceback.format_exc()
    logging.error(f"Exception occurred: {stack_trace}")
    return JSONResponse(status_code=500,
                        content={"detail": "An unexpected error occurred.", "stack_trace": stack_trace})
