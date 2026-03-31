from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Get database connection string from environment variables
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_NAME = os.getenv('DB_NAME', 'everyday_card')

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create engine with connection pool configuration to handle MySQL timeouts
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,          # 使用前检测连接是否有效,自动重连
    pool_recycle=3600,           # 1小时后回收连接,避免MySQL wait_timeout
    pool_size=5,                 # 连接池大小
    max_overflow=10,             # 最大溢出连接数
    echo=False,                  # 不打印SQL日志
    connect_args={
        'connect_timeout': 10,
        'read_timeout': 10,
        'write_timeout': 10
    }
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 