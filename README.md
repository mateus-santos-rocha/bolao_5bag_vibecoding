# Bolão 5BAG

Site/app para gerenciar bolão de partidas de LOL entre amigos, com ranking, apostas, e administração de partidas.

## Como rodar

1. Instale as dependências:
   ```
pip install -r requirements.txt
   ```
2. Configure os parâmetros de conexão no `database_connection_parameters.json` e a senha em `database_password.txt`.
3. Execute o app:
   ```
uvicorn app.main:app --reload
   ```

## Estrutura
- `app/`: código principal
- `static/`: arquivos estáticos
- `templates/`: templates HTML

## Funcionalidades
- Cadastro de usuários (sem senha, exceto admin)
- Gerenciamento de partidas e apostas
- Ranking
- Aprovação de apostas fora do prazo
- Pontuação parametrizável
