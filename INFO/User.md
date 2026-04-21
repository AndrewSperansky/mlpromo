docker exec -it promo_ml_backend python -c "
from app.db.session import SessionLocal
from app.models.user import User
from app.auth.jwt import get_password_hash

db = SessionLocal()

# Проверим, есть ли уже пользователи
users = db.query(User).all()
print(f'Existing users: {len(users)}')

# Создадим админа (замени email и пароль на свои)
admin = User(
    username='a.shigaev',
    email='a.shigaev@agrohold.ru',
    hashed_password=get_password_hash('admin{2123'),
    full_name='Andrey Shigaev',
    role='admin',
    is_active=True,
    is_deleted=False
)

db.add(admin)
db.commit()
print(f'Admin created: {admin.username} (role={admin.role})')
db.close()
"