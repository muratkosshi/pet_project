import json
import traceback
from datetime import datetime, timedelta
from typing import Optional

import httpx
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials
from passlib.context import CryptContext
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqladmin.authentication import AuthenticationBackend
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.dependencies.db.database import get_async_session
from app.core.auth.auth_context import current_user, current_internal_user
from app.core.auth.security import verify_password
from app.core.config import BILIMAL_MAIN_URL
from app.models import RoleModel

from app.models.external_user_model import ExternalUserModel
from app.models.internal_user_model import InternalUserModel
from app.readconfig.myconfig import MyConfig
from fastapi.security import HTTPBearer

auth_scheme = HTTPBearer()
# Настройки
SECRET_KEY = "REMOVED_SECRET"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
JWT_AUDIENCE = "http://localhost:6565/"


config = MyConfig()

EXCLUDED_PATHS = ["/admin/login", "/admin/statics/"]


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_jwt_token(token: str) -> dict:
    """Функция для декодирования JWT токена с полной ошибкой"""
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return decoded
    except jwt.ExpiredSignatureError as e:
        error_details = traceback.format_exc()
        raise HTTPException(status_code=401, detail={"error": "Token has expired", "exception": str(e), "trace": error_details})
    except jwt.InvalidTokenError as e:
        error_details = traceback.format_exc()
        raise HTTPException(status_code=401, detail={"error": "Invalid token", "exception": str(e), "trace": error_details})
    except Exception as e:
        error_details = traceback.format_exc()
        raise HTTPException(status_code=500, detail={"error": "Unexpected error", "exception": str(e), "trace": error_details})



async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
    session: AsyncSession = Depends(get_async_session),
):
    """Проверка токена: сначала пробуем декодировать как JWT, если не удается — верифицируем через Bilimal."""
    token = credentials.credentials

    # 1️⃣ Попытка декодирования токена как JWT
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], audience=JWT_AUDIENCE)

        user_id = decoded.get("user_id")
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid JWT payload")
        query = select(ExternalUserModel).where(ExternalUserModel.external_id == user_id)
        result = await session.execute(query)
        user = result.scalars().first()
        profile_id = user.external_id
        role_id = user.user_type
        first_name = user.first_name
        last_name = user.last_name

        print("✅ JWT token verified successfully")  # Логирование

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        print("⚠️ Invalid JWT token. Falling back to Bilimal verification...")  # Логирование
        profile_id, role_id, first_name, middle_name, last_name = await verify_token_bilimal(token)


    # 3️⃣ Поиск пользователя в БД или создание нового
    query = select(ExternalUserModel).where(ExternalUserModel.external_id == profile_id)
    result = await session.execute(query)
    user = result.scalars().first()

    if not user:
        user = ExternalUserModel(
            external_id=profile_id,
            first_name=first_name,
            last_name=last_name,
            user_type=role_id,
            source=1,
            registered_at=datetime.utcnow(),
        )
        session.add(user)
        await session.commit()
        # 2️⃣ Проверка роли пользователя
    role_query = await session.execute(
        select(RoleModel).where(RoleModel.id == user.user_type, RoleModel.source_id == user.source)
    )
    role = role_query.scalars().first()

    if not role:
        raise HTTPException(status_code=403, detail=f"Role not found, {role_id}")

    # Разбираем permissions
    role_permissions = json.loads(role.permissions) if isinstance(role.permissions, str) else role.permissions or {}
    can_login = role_permissions.get("can_login", False)

    if not can_login:
        raise HTTPException(status_code=403, detail="Access forbidden: role does not have login permission")

    current_user.set(user)
    return user
async def fetch_user_profile(profile_id: int, jwt_token: str):
    """Получает данные профиля пользователя через API Bilimal."""
    url = f"https://api.bilimal.kz/v1/profile?source_id=5&x-lang=ru-RU&user_id={profile_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {jwt_token}",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:  # ⏳ Тайм-аут 10 секунд
            response = await client.get(url, headers=headers)

        if response.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Failed to fetch user profile from Bilimal: {response.text}")

        return response.json()

    except httpx.ReadTimeout:
        raise HTTPException(status_code=504, detail="Bilimal API is not responding (timeout exceeded)")

    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Network error: {str(e)}")



async def verify_token_bilimal(token: str):
    """Если токен не является JWT, верифицируем его через Bilimal API."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(BILIMAL_MAIN_URL, headers=headers)

        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid token")

        user_data = response.json()
        return (
            user_data.get("id"),
            user_data.get("role_id"),
            user_data.get("first_name"),
            user_data.get("middle_name", ""),
            user_data.get("last_name"),
        )


async def authenticate_user_login_password(session: AsyncSession, login: str, password: str) -> Optional[InternalUserModel]:
    query = select(InternalUserModel).where(InternalUserModel.username == login)
    result = await session.execute(query)
    user = result.scalars().first()

    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


# Получение текущего пользователя из токена
async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_async_session)
) -> InternalUserModel:
    """
    Получение текущего пользователя из токена.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
        )

    token = auth_header.split("Bearer ")[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    # Найти пользователя в базе данных
    query = text("SELECT * FROM internal_user WHERE id = :user_id")
    result = await session.execute(query, {"user_id": user_id})
    user = result.fetchone()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user

class AuthorizationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, secret_key: str):
        super().__init__(app)
        self.secret_key = secret_key

    async def dispatch(self, request: Request, call_next):
        if any(request.url.path.startswith(path) for path in EXCLUDED_PATHS):
            return await call_next(request)

        token = request.cookies.get("jwt")
        if not token:
            return RedirectResponse(url="/admin/login", status_code=302)

        async with request.state.db_session as session:
            try:
                user = await verify_admin_user(token, session)
                if not user:
                    raise HTTPException(status_code=401, detail="Unauthorized")
                request.state.user = user

            except:
                # Удаляем куки и перенаправляем
                response = RedirectResponse(url="/admin/login", status_code=302)
                response.delete_cookie(key="jwt")
                return response

        return await call_next(request)

class AdminAuthBackend(AuthenticationBackend):
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.middlewares = [Middleware(AuthorizationMiddleware, secret_key=secret_key)]

    async def login(self, request: Request) -> bool:
        form = await request.form()
        login, password = form.get("username"), form.get("password")

        if not login or not password:
            return False

        async with request.state.db_session as session:
            user = await authenticate_user_login_password(session, login, password)
            if not user:
                return False

            token = create_access_token({"sub": user.id})
            response = RedirectResponse(url="/admin", status_code=302)
            response.set_cookie(key="jwt", value=token, httponly=True)
            return response

    async def authenticate(self, request: Request) -> bool:
        token = request.cookies.get("jwt")
        if not token:
            raise HTTPException(status_code=401, detail="Unauthorized")

        async with request.state.db_session as session:
            user = await verify_admin_user(token, session)
            if user:
                request.state.user = user
                return True

        raise HTTPException(status_code=403, detail="Forbidden")

    async def logout(self, request: Request) -> bool:
        response = RedirectResponse(url="/admin/login", status_code=302)
        response.delete_cookie(key="jwt")
        return response


async def verify_admin_user(token: str, session: AsyncSession) -> InternalUserModel:
    payload = decode_jwt_token(token)

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    query = select(InternalUserModel).where(InternalUserModel.id == user_id)
    result = await session.execute(query)
    user = result.scalar_one_or_none()


    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    print(user)
    current_internal_user.set(user)
    return user
