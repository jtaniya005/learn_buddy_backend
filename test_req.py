import os
os.environ["DATABASE_URL"] = "sqlite:///./sql_app_test2.db"

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app, raise_server_exceptions=False)

response = client.post(
    "/api/auth/register",
    json={
        "name": "taniya",
        "email": "user_with_student_id@example.com",
        "password": "1234567890",
        "student_class": 10,
        "avatar_index": 0,
        "weak_subjects": ["maths"],
        "daily_goal_minutes": 30
    }
)
print("STATUS:", response.status_code)
print("RESPONSE:", response.json())
