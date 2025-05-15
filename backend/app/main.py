from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import alerts, auth, equipment, parameters, rules, settings, users
from app.core.config import settings as app_settings


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    print("PRINT:  Приложение FastAPI запускается...")
    yield
    print("PRINT:  Приложение FastAPI останавливается...")


# --- Описание приложения ---
description = """
    API мобильной системы мониторинга (MsM) помогает пользователям 
    следить за техническими параметрами технологического оборудования! 🚀

    Вы сможете:
        - Аутентифицироваться и управлять своим профилем;
        - Просматривать иерархию оборудования (цеха, линии, агрегаты, актуаторы);
        - Просматривать параметры для актуаторов и их значения;
        - Создавать и управлять правилами мониторинга для параметров;
        - Получать и просматривать тревоги, сработавшие по вашим правилам.
"""


# --- Создание экземпляра FastAPI ---
app = FastAPI(
    title="MsM – мобильная система мониторинга (API)",
    description=description,
    version="0.1.0",
    lifespan=lifespan,
    # openapi_url=f"{app_settings.API_V1_STR}/openapi.json"
    # docs_url="/docs",
    # redoc_url="/redoc"
)


# --- Настройка CORS (Cross-Origin Resource Sharing) ---
if app_settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,  # noqa
        allow_origins=[str(origin) for origin in app_settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,  # noqa
        allow_origins=["*"],  # TODO: Для production это небезопасно!
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# --- Подключение роутеров ---
api_prefix = ""  # Пока без общего префикса
    # api_prefix = "/api/v1"

app.include_router(auth.router, prefix=f"{api_prefix}", tags=["Authentication"])
app.include_router(users.router, prefix=f"{api_prefix}", tags=["Users"])
app.include_router(settings.router, prefix=f"{api_prefix}", tags=["User Settings"])
app.include_router(equipment.router, prefix=f"{api_prefix}", tags=["Equipment Hierarchy"])
app.include_router(parameters.router, prefix=f"{api_prefix}", tags=["Parameters & Data"])
app.include_router(rules.router, prefix=f"{api_prefix}", tags=["Monitoring Rules"])
app.include_router(alerts.router, prefix=f"{api_prefix}", tags=["Alerts"])


# Простой эндпоинт для проверки работоспособности API (опционально)
@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Добро пожаловать в API мобильной системы мониторинга (МsМ)!"}