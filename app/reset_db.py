from app.database import engine
from sqlalchemy import text

# Lista das tabelas na ordem correta para evitar problemas de FK
TABLES = ['bet_requests', 'bets', 'matches', 'users']

def drop_tables():
    with engine.connect() as conn:
        for table in TABLES:
            conn.execute(text(f'DROP TABLE IF EXISTS {table} CASCADE;'))
        conn.commit()

if __name__ == '__main__':
    drop_tables()
    print('Tabelas apagadas com sucesso.')
