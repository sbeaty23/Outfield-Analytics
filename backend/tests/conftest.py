import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://outfield:outfield@db/outfield_analytics",
)
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("FRONTEND_URL", "http://frontend.test")
