# MongoDB Configuration
MONGO_URI_PROD = (
    "mongodb://roman:Zq4Ln7Vc2Xj9Gt5P@"
    "10.2.3.41:27017,10.2.4.41:27017,10.2.5.41:27017/"
    "Cluster0?replicaSet=rs0"
)

MONGO_URI_STAGE = (
    "mongodb://mainAdmin:CJlur282BNHgw0j@"
    "10.3.3.41:27017,10.3.4.41:27017,10.3.5.41:27017/"
    "Cluster0?replicaSet=rs0&authSource=admin"
)

# По умолчанию используется PROD (для обратной совместимости)
MONGO_URI = MONGO_URI_PROD

DB_NAME = "Cluster0"


# PostgreSQL Configuration
POSTGRES_HOST = "10.2.3.22"
POSTGRES_PORT = 5432
POSTGRES_USER = "qa_eng"
POSTGRES_PASSWORD = "Qwedsa3221@#"  # TODO: указать пароль
POSTGRES_DATABASE = "master"

# Connection URI для psycopg2 или SQLAlchemy
POSTGRES_URI = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
    f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DATABASE}"
)
