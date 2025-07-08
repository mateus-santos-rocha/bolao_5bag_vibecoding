from app.database import SessionLocal
from app.crud import get_user_by_name, create_user

db = SessionLocal()
user = get_user_by_name(db, 'admin')
if user:
    print('Usuário admin já existe. Atualizando para admin.')
    user.is_admin = True
    db.commit()
else:
    create_user(db, 'admin', True)
    print('Usuário admin criado.')
db.close()
