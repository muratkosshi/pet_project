import json
import logging
import traceback
import uuid
from datetime import datetime, timedelta

import httpx
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from loguru import logger
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.future import select
from app.dependencies.db.database import get_async_session
from app.core.auth.auth import decode_jwt_token, SECRET_KEY, ALGORITHM, fetch_user_profile, JWT_AUDIENCE, \
    create_access_token
from app.core.auth.security import verify_password
from app.core.config import BILIMAL_MAIN_URL, BILIMAL_PROFILE_URL, BILIMAL_API_URL
from app.models import ExternalUserModel, RoleModel
from starlette.responses import JSONResponse


router = APIRouter()

Base = declarative_base()
# Константы для API Bilimal

# Модели для входных и выходных данных
class LoginRequest(BaseModel):
    login: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class MeResponse(BaseModel):
    id: int
    login: str




async def fetch_bilimal_data(url: str, token: str):
    """Функция запроса данных пользователя через Bilimal API."""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if not (200 <= response.status_code < 300):
            raise HTTPException(status_code=401, detail="Invalid token")
        return response.json()


@router.get("/authenticate_user")
async def authenticate_user(request: Request, session: AsyncSession = Depends(get_async_session)):
    """Аутентификация пользователя и получение данных профиля."""
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(status_code=400, detail="Требуется токен авторизации")

    token = token.split("Bearer ")[1]

    try:
        # ✅ Проверяем JWT
        try:
            decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], audience=JWT_AUDIENCE)
            user_id = decoded.get("user_id")

            if not user_id:
                raise HTTPException(status_code=400, detail="Invalid JWT payload: user_id not found")

            logger.info(f"✅ JWT token verified successfully for user_id={user_id}")

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")

        # ✅ Проверяем пользователя в БД
        existing_user_query = await session.execute(
            select(ExternalUserModel).where(ExternalUserModel.external_id == user_id)
        )
        existing_user = existing_user_query.scalars().first()

        if existing_user:
            logger.info(f"✅ Пользователь {user_id} найден в БД, используем локальные данные")
        else:
            logger.info(f"🔍 Пользователь {user_id} не найден, загружаем данные из Bilimal API")
            user_data = await fetch_user_profile(user_id, token)

            if isinstance(user_data, list) and user_data:
                user_data = user_data[0]

            role_id = user_data.get("role_id")
            first_name = user_data.get("first_name") or "Unknown"
            middle_name = user_data.get("middle_name", "")
            last_name = user_data.get("last_name") or "Unknown"
            source_id = user_data.get("source", 1)
            login = user_data.get("uin")

            existing_user = ExternalUserModel(
                external_id=user_id,
                first_name=first_name,
                last_name=last_name,
                user_type=role_id,
                access_token=token,
                registered_at=datetime.utcnow(),
                reset_generation_at=datetime.utcnow() + timedelta(days=30),
                generation_count=0,
                login=login
            )
            session.add(existing_user)
            await session.commit()

        return JSONResponse(
            content={
                "user_id": existing_user.id,
                "generation_limit": existing_user.generation_limit,
                "generation_count": existing_user.generation_count,
                "reset_generation_at": (
                    existing_user.reset_generation_at.isoformat() if existing_user.reset_generation_at else None
                ),
                "first_name": existing_user.first_name,
                "last_name": existing_user.last_name,
            }
        )

    except Exception as e:
        await session.rollback()
        logger.error(f"Ошибка при аутентификации: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при аутентификации пользователя")


async def verify_token_bilimal(token: str):
    """Если токен не является JWT, верифицируем его через Bilimal API."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(BILIMAL_MAIN_URL, headers=headers)

        if not (200 <= response.status_code < 300):
            logging.info(f"Invalid authToken{token}, https://api.bilimal.kz/v1/main?source_id=5")
            raise HTTPException(status_code=401, detail="Invalid token")

        user_data = response.json()
        return (
            user_data.get("id"),
            user_data.get("role_id"),
            user_data.get("first_name") or "Unknown",
            user_data.get("middle_name", ""),
            user_data.get("last_name") or "Unknown",
            user_data.get("source", 1),
        )




@router.post("/login")
async def external_user_login(body: LoginRequest, session: AsyncSession = Depends(get_async_session)):
    """
    Эндпоинт для авторизации внешнего пользователя через API Bilimal.
    """
    try:
        async with session.begin():
            # ✅ Проверяем, есть ли пользователь в БД по логину
            existing_user_query = await session.execute(
                select(ExternalUserModel).where(ExternalUserModel.login == body.login)
            )
            existing_user = existing_user_query.scalars().first()

            if existing_user:
                logger.info(f"🔍 Пользователь {body.login} найден в БД. Проверяем пароль...")
                if not verify_password(body.password, existing_user.password) :
                    logger.warning(f"⛔ Неверный пароль для {body.login}. Проверяем через Bilimal API...")

                    # Проверяем через Bilimal, если пароль неверный
                    async with httpx.AsyncClient() as client:
                        payload = {"login": body.login, "password": body.password}
                        response = await client.post(BILIMAL_API_URL, json=payload)

                    if not (200 <= response.status_code < 300):
                        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

                    # ✅ Если Bilimal подтвердил — обновляем пароль в БД
                    logger.info(f"✅ Обновляем пароль в базе для {body.login}")
                    existing_user.set_password(body.password)  # Хешируем новый пароль
                    session.add(existing_user)

                # ✅ Генерируем JWT
                access_token = create_access_token(
                    data={"user_id": existing_user.external_id, "aud": JWT_AUDIENCE},
                )
                return {"message": "Авторизация успешна", "token": access_token}

        # ✅ Если пользователя нет в БД, запрашиваем у Bilimal API
        logger.info(f"🔍 Пользователь {body.login} не найден в БД. Авторизуем через Bilimal API...")
        async with httpx.AsyncClient() as client:
            payload = {"login": body.login, "password": body.password}
            response = await client.post(BILIMAL_API_URL, json=payload)

        if not (200 <= response.status_code < 300):
            raise HTTPException(status_code=response.status_code, detail="Ошибка аутентификации")

        data = response.json()
        token = data["token"]
        profile = data.get("profile")

        if not token or not profile:
            raise HTTPException(status_code=500, detail="Bilimal не вернул данные профиля.")

        user_id = profile.get("user_id")
        first_name = profile.get("first_name", "Unknown")
        last_name = profile.get("last_name", "Unknown")
        role_id = profile.get("role_id")
        source_id = profile.get("source", 1)

        if not user_id or not role_id:
            raise HTTPException(status_code=500, detail="Некорректный ответ от Bilimal API.")

        async with session.begin():
            # ✅ Запрашиваем роль пользователя
            role_query = await session.execute(
                select(RoleModel).where(RoleModel.id == role_id, RoleModel.source_id == source_id)
            )
            role = role_query.scalars().first()

            if not role:
                raise HTTPException(status_code=403, detail="Роль не найдена в базе")

            # ✅ Проверяем права роли
            try:
                role_permissions = json.loads(role.permissions) if isinstance(role.permissions, str) else role.permissions or {}
            except json.JSONDecodeError:
                raise HTTPException(status_code=500, detail="Ошибка парсинга прав доступа")

            can_login = role_permissions.get("can_login", False)

            if not can_login:
                logger.warning(f"🚫 Попытка входа с запрещённой ролью (role_id={role_id}, user_id={user_id})")
                raise HTTPException(status_code=403, detail="Доступ запрещен: у вашей роли нет разрешения на вход")

            # ✅ Сохраняем пользователя в БД
            new_user = ExternalUserModel(
                external_id=user_id,
                login=body.login,
                first_name=first_name,
                last_name=last_name,
                user_type=role_id,
                access_token=token,
                registered_at=datetime.utcnow(),
                generation_count=0,
            )
            new_user.set_password(body.password)  # ✅ Хешируем пароль
            session.add(new_user)

        # ✅ Генерируем свой JWT через `create_access_token`
        access_token = create_access_token(
            data={"user_id": user_id, "aud": JWT_AUDIENCE},
        )

        return {"message": "Авторизация успешна", "token": access_token}

    except HTTPException as http_err:
        await session.rollback()
        logger.error(f"Ошибка при логине: {http_err.detail}")
        raise http_err

    except Exception as e:
        await session.rollback()
        logger.error(f"❌ Неизвестная ошибка при логине: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка при входе")

@router.get("/decode_jwt")
async def decode_jwt(request: Request):
    """Принимает JWT-токен, расшифровывает и возвращает данные"""
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(status_code=400, detail="Missing or invalid Authorization header")

    token = token.split("Bearer ")[1]  # Убираем "Bearer "
    decoded_data = decode_jwt_token(token)
    return {"decoded_token": decoded_data}
