import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://db.example.test/test_database",
)
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("FRONTEND_URL", "http://frontend.test")
os.environ.setdefault("BACKEND_ALLOWED_HOSTS", "testserver,localhost")
os.environ.setdefault("MLB_API_BASE_URL", "https://baseball.test/api/v1")
os.environ.setdefault("MLB_CURRENT_SEASON", "2026")
