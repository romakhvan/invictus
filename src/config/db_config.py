import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Определяем окружение (prod, stage, dev)
ENVIRONMENT = os.getenv("ENVIRONMENT", "prod").lower()


# MongoDB Configuration
def _get_mongo_uri(env: str) -> str:
    """Формирует MongoDB URI для указанного окружения."""
    env_upper = env.upper()
    
    user = os.getenv(f"MONGO_USER_{env_upper}")
    password = os.getenv(f"MONGO_PASSWORD_{env_upper}")
    hosts = os.getenv(f"MONGO_HOSTS_{env_upper}")
    replica_set = os.getenv(f"MONGO_REPLICA_SET_{env_upper}", "rs0")
    db_name = os.getenv(f"MONGO_DB_NAME_{env_upper}", "Cluster0")
    auth_source = os.getenv(f"MONGO_AUTH_SOURCE_{env_upper}", "")
    
    if not all([user, password, hosts]):
        raise ValueError(f"MongoDB credentials not found for environment: {env}")
    
    auth_source_param = f"&authSource={auth_source}" if auth_source else ""
    
    return (
        f"mongodb://{user}:{password}@{hosts}/"
        f"{db_name}?replicaSet={replica_set}{auth_source_param}"
    )


# Создаем URI для разных окружений
MONGO_URI_PROD = _get_mongo_uri("prod")
MONGO_URI_STAGE = _get_mongo_uri("stage")

# По умолчанию используется окружение из переменной ENVIRONMENT
MONGO_URI = MONGO_URI_PROD if ENVIRONMENT == "prod" else MONGO_URI_STAGE

DB_NAME = os.getenv(f"MONGO_DB_NAME_{ENVIRONMENT.upper()}", "Cluster0")


# PostgreSQL Configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "10.2.3.22")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DATABASE = os.getenv("POSTGRES_DATABASE", "master")

if not all([POSTGRES_USER, POSTGRES_PASSWORD]):
    raise ValueError("PostgreSQL credentials not found in environment variables")

# Connection URI для psycopg2 или SQLAlchemy
POSTGRES_URI = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
    f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DATABASE}"
)
