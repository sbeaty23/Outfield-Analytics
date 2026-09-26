import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://db.example.test/test_database",
)
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("FRONTEND_URL", "http://frontend.test")
