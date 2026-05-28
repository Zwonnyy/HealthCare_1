from ai_worker.core import config

TORTOISE_APP_MODELS = [
    "app.models.users",
    "app.models.records",
    "app.models.guides",
    "app.models.health_logs",
    "app.models.messages",
]

TORTOISE_ORM = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.mysql",
            "dialect": "asyncmy",
            "credentials": {
                "host": config.DB_HOST,
                "port": config.DB_PORT,
                "user": config.DB_USER,
                "password": config.DB_PASSWORD,
                "database": config.DB_NAME,
                "connect_timeout": config.DB_CONNECT_TIMEOUT,
                "maxsize": config.DB_CONNECTION_POOL_MAXSIZE,
            },
        }
    },
    "apps": {
        "models": {
            "models": TORTOISE_APP_MODELS,
        }
    },
    "timezone": "Asia/Seoul",
}
