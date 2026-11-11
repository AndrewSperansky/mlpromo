
# docker exec -it promo_ml_backend python scripts/create_user_me.py

from app.auth.jwt import get_password_hash
from app.db.session import SessionLocal
from app.models.user import User

db = SessionLocal()

new_user = User(
    username="a.shigaev",
    email="a.shigaev@agrohold.ru",
    hashed_password=get_password_hash("admin123"),
    full_name="Andrey Shigaev",
    role="admin",
    is_active=True
)

db.add(new_user)
db.commit()
print(f"User created with id: {new_user.id}")

db.close()