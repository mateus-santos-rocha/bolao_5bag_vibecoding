from fastapi import FastAPI, Request, Form, Depends, HTTPException, Response, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from . import models, crud, points
from .models import MatchType
from .config import POINTS
from datetime import datetime, timedelta
from fastapi.staticfiles import StaticFiles
import json
from hashlib import sha256
from sqlalchemy import text

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

ADMIN_SESSION_COOKIE = "admin_session"
ADMIN_SESSION_DURATION = timedelta(hours=6)
ADMIN_DEFAULT_PASSWORD = "02925160"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    ranking = crud.get_ranking(db, points.calculate_points)
    matches = crud.get_matches(db)
    # Formata a data/hora das partidas para o padrão brasileiro
    for match in matches:
        match.scheduled_time_fmt = match.scheduled_time.strftime('%d/%m/%Y %H:%M:%S') if match.scheduled_time else ''
    return templates.TemplateResponse("home.html", {"request": request, "ranking": ranking, "matches": matches})

@app.get("/apostar", response_class=HTMLResponse)
def select_user(request: Request, db: Session = Depends(get_db)):
    users = crud.get_all_users(db)
    users = [u for u in users if not u.is_admin]
    return templates.TemplateResponse("select_user.html", {"request": request, "users": users})

@app.get("/matches", response_class=HTMLResponse)
def matches(request: Request, db: Session = Depends(get_db), user_name: str = None):
    if not user_name:
        return RedirectResponse("/apostar", status_code=303)
    matches_db = crud.get_matches(db)
    users = crud.get_all_users(db)
    bets = crud.get_all_bets(db)
    # Serializa matches para JSON seguro
    matches = []
    for m in matches_db:
        matches.append({
            'id': m.id,
            'team1': m.team1,
            'team2': m.team2,
            'match_type': m.match_type.value if hasattr(m.match_type, 'value') else str(m.match_type),
            'scheduled_time_fmt': m.scheduled_time.strftime('%d/%m/%Y %H:%M:%S') if m.scheduled_time else '',
        })
    # Serializa apostas incluindo o nome do usuário
    bets_serialized = []
    user_id_map = {u.id: u.name for u in users}
    # Filtra apostas apenas do usuário selecionado
    user = next((u for u in users if u.name == user_name), None)
    user_bets = [b for b in bets if user and b.user_id == user.id]
    for b in user_bets:
        bets_serialized.append({
            'user_id': b.user_id,
            'user_name': user_id_map.get(b.user_id, ''),
            'match_id': b.match_id,
            'prediction': b.prediction,
            'timestamp': b.timestamp.strftime('%d/%m/%Y %H:%M:%S') if b.timestamp else '',
        })
    return templates.TemplateResponse("matches.html", {"request": request, "matches": matches, "users": users, "bets": bets_serialized, "selected_user": user_name})

@app.get("/editar", response_class=HTMLResponse)
def select_user_edit(request: Request, db: Session = Depends(get_db)):
    users = crud.get_all_users(db)
    return templates.TemplateResponse("select_user_edit.html", {"request": request, "users": users})

@app.get("/edit-bet", response_class=HTMLResponse)
def edit_bet(request: Request, db: Session = Depends(get_db), user_name: str = None):
    if not user_name:
        return RedirectResponse("/editar", status_code=303)
    users = crud.get_all_users(db)
    matches_db = crud.get_matches(db)
    bets = crud.get_all_bets(db)
    # Filtra apenas apostas feitas pelo usuário selecionado
    user = next((u for u in users if u.name == user_name), None)
    if not user:
        return RedirectResponse("/editar", status_code=303)
    user_bets = [b for b in bets if b.user_id == user.id]
    # Só mostrar partidas que o usuário já apostou
    match_ids_with_bet = {b.match_id for b in user_bets}
    now = datetime.now()
    matches = [
        {
            'id': m.id,
            'team1': m.team1,
            'team2': m.team2,
            'match_type': m.match_type.value if hasattr(m.match_type, 'value') else str(m.match_type),
            'scheduled_time_fmt': m.scheduled_time.strftime('%d/%m/%Y %H:%M:%S') if m.scheduled_time else '',
            'scheduled_time': m.scheduled_time.isoformat() if m.scheduled_time else '',
        }
        for m in matches_db if m.id in match_ids_with_bet and (not m.scheduled_time or m.scheduled_time > now)
    ]
    bets_serialized = []
    for b in user_bets:
        bets_serialized.append({
            'id': b.id,
            'user_id': b.user_id,
            'match_id': b.match_id,
            'prediction': b.prediction,
            'timestamp': b.timestamp.isoformat() if b.timestamp else '',
            'approved': b.approved,
        })
    return templates.TemplateResponse("edit_bet.html", {"request": request, "users": users, "matches": matches, "bets": bets_serialized, "selected_user": user_name})

@app.post("/edit-bet")
def edit_bet_post(request: Request, user_name: str = Form(...), match_id: int = Form(...), prediction: str = Form(...), db: Session = Depends(get_db)):
    users = crud.get_all_users(db)
    matches_db = crud.get_matches(db)
    bets = crud.get_all_bets(db)
    user = crud.get_user_by_name(db, user_name)
    if not user:
        return templates.TemplateResponse("edit_bet.html", {"request": request, "users": users, "matches": matches_db, "bets": bets, "selected_user": user_name, "error": "Usuário não encontrado."})
    match = db.query(models.Match).get(match_id)
    if not match:
        return templates.TemplateResponse("edit_bet.html", {"request": request, "users": users, "matches": matches_db, "bets": bets, "selected_user": user_name, "error": "Partida não encontrada."})
    try:
        t1, t2 = map(int, prediction.split('-'))
        tipo = match.match_type.value if hasattr(match.match_type, 'value') else str(match.match_type)
        if tipo == 'MD1':
            if not ((t1 == 1 and t2 == 0) or (t1 == 0 and t2 == 1)):
                raise Exception("Placar válido para MD1: 1-0 ou 0-1")
        elif tipo == 'MD3':
            validos = [(2,0), (2,1), (0,2), (1,2)]
            if (t1, t2) not in validos:
                raise Exception("Placar válido para MD3: 2-0, 2-1, 0-2, 1-2")
        elif tipo == 'MD5':
            validos = [(3,0), (3,1), (3,2), (0,3), (1,3), (2,3)]
            if (t1, t2) not in validos:
                raise Exception("Placar válido para MD5: 3-0, 3-1, 3-2, 0-3, 1-3, 2-3")
        else:
            raise Exception("Tipo de série inválido")
        # Só pode editar antes do início da partida
        if datetime.now() > match.scheduled_time:
            return RedirectResponse(f"/edit-bet?user_name={user_name}", status_code=303)
        crud.update_bet(db, user.id, match_id, prediction)
        return RedirectResponse(f"/edit-bet?user_name={user_name}", status_code=303)
    except Exception as e:
        # Renderiza a tela de edição com erro
        user_bets = [b for b in bets if b.user_id == user.id]
        match_ids_with_bet = {b.match_id for b in user_bets}
        matches = [
            {
                'id': m.id,
                'team1': m.team1,
                'team2': m.team2,
                'match_type': m.match_type.value if hasattr(m.match_type, 'value') else str(m.match_type),
                'scheduled_time_fmt': m.scheduled_time.strftime('%d/%m/%Y %H:%M:%S') if m.scheduled_time else '',
                'scheduled_time': m.scheduled_time.isoformat() if m.scheduled_time else '',
            }
            for m in matches_db if m.id in match_ids_with_bet
        ]
        bets_serialized = []
        for b in user_bets:
            bets_serialized.append({
                'id': b.id,
                'user_id': b.user_id,
                'match_id': b.match_id,
                'prediction': b.prediction,
                'timestamp': b.timestamp.isoformat() if b.timestamp else '',
                'approved': b.approved,
            })
        return templates.TemplateResponse("edit_bet.html", {"request": request, "users": users, "matches": matches, "bets": bets_serialized, "selected_user": user_name, "error": str(e)})

@app.post("/bet")
def bet(user_name: str = Form(...), match_id: int = Form(...), prediction: str = Form(...), db: Session = Depends(get_db)):
    users = crud.get_all_users(db)
    matches_db = crud.get_matches(db)
    bets = crud.get_all_bets(db)
    user = crud.get_user_by_name(db, user_name)
    if not user:
        return templates.TemplateResponse("matches.html", {"request": {}, "matches": matches_db, "users": users, "bets": bets, "selected_user": user_name, "error": "Usuário não encontrado."})
    match = db.query(models.Match).get(match_id)
    if not match:
        return templates.TemplateResponse("matches.html", {"request": {}, "matches": matches_db, "users": users, "bets": bets, "selected_user": user_name, "error": "Partida não encontrada."})
    try:
        t1, t2 = map(int, prediction.split('-'))
        tipo = match.match_type.value if hasattr(match.match_type, 'value') else str(match.match_type)
        if tipo == 'MD1':
            if not ((t1 == 1 and t2 == 0) or (t1 == 0 and t2 == 1)):
                raise Exception("Placar válido para MD1: 1-0 ou 0-1")
        elif tipo == 'MD3':
            validos = [(2,0), (2,1), (0,2), (1,2)]
            if (t1, t2) not in validos:
                raise Exception("Placar válido para MD3: 2-0, 2-1, 0-2, 1-2")
        elif tipo == 'MD5':
            validos = [(3,0), (3,1), (3,2), (0,3), (1,3), (2,3)]
            if (t1, t2) not in validos:
                raise Exception("Placar válido para MD5: 3-0, 3-1, 3-2, 0-3, 1-3, 2-3")
        else:
            raise Exception("Tipo de série inválido")
        if datetime.now() > match.scheduled_time:
            crud.create_bet_request(db, user.id, match_id, prediction)
            return RedirectResponse(f"/matches?user_name={user_name}", status_code=303)
        # Verifica se já existe aposta para este usuário e partida
        existing_bet = db.query(models.Bet).filter_by(user_id=user.id, match_id=match_id).first()
        if existing_bet:
            crud.update_bet(db, user.id, match_id, prediction)
        else:
            crud.place_bet(db, user.id, match_id, prediction)
        return RedirectResponse(f"/matches?user_name={user_name}", status_code=303)
    except Exception as e:
        # Renderiza a tela de apostas com erro
        matches = []
        for m in matches_db:
            matches.append({
                'id': m.id,
                'team1': m.team1,
                'team2': m.team2,
                'match_type': m.match_type.value if hasattr(m.match_type, 'value') else str(m.match_type),
                'scheduled_time_fmt': m.scheduled_time.strftime('%d/%m/%Y %H:%M:%S') if m.scheduled_time else '',
            })
        bets_serialized = []
        user_id_map = {u.id: u.name for u in users}
        for b in bets:
            bets_serialized.append({
                'user_id': b.user_id,
                'user_name': user_id_map.get(b.user_id, ''),
                'match_id': b.match_id,
                'prediction': b.prediction,
                'timestamp': b.timestamp.strftime('%d/%m/%Y %H:%M:%S') if b.timestamp else '',
            })
        return templates.TemplateResponse("matches.html", {"request": {}, "matches": matches, "users": users, "bets": bets_serialized, "selected_user": user_name, "error": str(e)})

@app.get("/admin", response_class=HTMLResponse)
def admin(request: Request, db: Session = Depends(get_db)):
    matches = crud.get_matches(db)
    users = crud.get_all_users(db)
    teams = crud.get_teams(db)
    # Formata a data/hora das partidas para o padrão brasileiro
    for match in matches:
        match.scheduled_time_fmt = match.scheduled_time.strftime('%d/%m/%Y %H:%M:%S') if match.scheduled_time else ''
    return templates.TemplateResponse("admin.html", {"request": request, "matches": matches, "points": POINTS, "users": users, "teams": teams})

@app.post("/admin/match")
def admin_create_match(request: Request, team1: str = Form(...), team2: str = Form(...), scheduled_time: str = Form(...), match_type: str = Form(...), db: Session = Depends(get_db)):
    try:
        dt = datetime.strptime(scheduled_time, "%d/%m/%Y %H:%M:%S")
    except ValueError:
        matches = crud.get_matches(db)
        users = crud.get_all_users(db)
        teams = crud.get_teams(db)
        for match in matches:
            match.scheduled_time_fmt = match.scheduled_time.strftime('%d/%m/%Y %H:%M:%S') if match.scheduled_time else ''
        return templates.TemplateResponse("admin.html", {"request": request, "matches": matches, "points": POINTS, "users": users, "teams": teams, "error": "Data/hora inválida. Use o formato dd/mm/aaaa HH:MM:SS"})
    crud.create_match(db, team1, team2, dt, MatchType(match_type))
    return RedirectResponse("/admin", status_code=303)

@app.post("/admin/result")
def admin_set_result(match_id: int = Form(...), result: str = Form(...), db: Session = Depends(get_db)):
    crud.set_match_result(db, match_id, result)
    return RedirectResponse("/admin", status_code=303)

@app.post("/admin/points")
def admin_set_points(md1: int = Form(...), md3_winner: int = Form(...), md3_score: int = Form(...), md5_winner: int = Form(...), md5_score: int = Form(...)):
    POINTS['MD1'] = md1
    POINTS['MD3_WINNER'] = md3_winner
    POINTS['MD3_SCORE'] = md3_score
    POINTS['MD5_WINNER'] = md5_winner
    POINTS['MD5_SCORE'] = md5_score
    return RedirectResponse("/admin", status_code=303)

@app.post("/admin/user")
def admin_add_user(user_name: str = Form(...), is_admin: str = Form(None), db: Session = Depends(get_db)):
    is_admin_bool = bool(is_admin)
    if user_name:
        user = crud.create_user(db, user_name, is_admin_bool)
        if not user:
            return RedirectResponse("/admin?error=duplicated", status_code=303)
    return RedirectResponse("/admin", status_code=303)

@app.post("/admin/user/edit")
def admin_edit_user(user_id: int = Form(...), new_name: str = Form(...), is_admin: str = Form(None), db: Session = Depends(get_db)):
    is_admin_bool = bool(is_admin)
    user = crud.update_user(db, user_id, new_name, is_admin_bool)
    if not user:
        return RedirectResponse("/admin?error=duplicated", status_code=303)
    return RedirectResponse("/admin", status_code=303)

@app.post("/admin/user/delete")
def admin_delete_user(user_id: int = Form(...), db: Session = Depends(get_db)):
    crud.delete_user(db, user_id)
    return RedirectResponse("/admin", status_code=303)

@app.post("/admin/team")
def admin_add_team(team_name: str = Form(...), db: Session = Depends(get_db)):
    if team_name:
        team = crud.create_team(db, team_name)
        if not team:
            return RedirectResponse("/admin?error=duplicated_team", status_code=303)
    return RedirectResponse("/admin", status_code=303)

@app.post("/admin/team/edit")
def admin_edit_team(team_id: int = Form(...), new_name: str = Form(...), db: Session = Depends(get_db)):
    team = db.query(models.Team).get(team_id)
    if not team:
        return RedirectResponse("/admin?error=team_not_found", status_code=303)
    # Verifica duplicidade
    if db.query(models.Team).filter(models.Team.name == new_name, models.Team.id != team_id).first():
        return RedirectResponse("/admin?error=duplicated_team", status_code=303)
    team.name = new_name
    db.commit()
    db.refresh(team)
    return RedirectResponse("/admin", status_code=303)

@app.post("/admin/team/delete")
def admin_delete_team(team_id: int = Form(...), db: Session = Depends(get_db)):
    team = db.query(models.Team).get(team_id)
    if team:
        db.delete(team)
        db.commit()
    return RedirectResponse("/admin", status_code=303)

@app.get("/admin/login", response_class=HTMLResponse)
def admin_login_get(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request})

@app.post("/admin/login")
def admin_login_post(request: Request, user_name: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = crud.get_user_by_name(db, user_name)
    if not user or not user.is_admin:
        return templates.TemplateResponse("admin_login.html", {"request": request, "error": "Usuário não encontrado ou não é admin."})
    # Senha: se for admin padrão, aceita senha fixa
    if user_name == "admin" and password == ADMIN_DEFAULT_PASSWORD:
        import secrets
        session_token = secrets.token_hex(32)
        response = RedirectResponse("/admin", status_code=303)
        response.set_cookie(ADMIN_SESSION_COOKIE, session_token, max_age=int(ADMIN_SESSION_DURATION.total_seconds()), httponly=True, samesite="lax")
        app.state.admin_session = {"token": session_token, "user": user_name, "expires": datetime.now() + ADMIN_SESSION_DURATION}
        return response
    # Senha normal: hash( user_name + valor do arquivo database_password.txt )
    try:
        with open("database_password.txt") as f:
            secret = f.read().strip()
    except Exception:
        secret = "admin"
    expected = sha256((user_name+secret).encode()).hexdigest()
    if password != expected:
        return templates.TemplateResponse("admin_login.html", {"request": request, "error": "Senha incorreta."})
    # Login OK
    import secrets
    session_token = secrets.token_hex(32)
    response = RedirectResponse("/admin", status_code=303)
    response.set_cookie(ADMIN_SESSION_COOKIE, session_token, max_age=int(ADMIN_SESSION_DURATION.total_seconds()), httponly=True, samesite="lax")
    app.state.admin_session = {"token": session_token, "user": user_name, "expires": datetime.now() + ADMIN_SESSION_DURATION}
    return response

def is_admin_authenticated(request: Request):
    token = request.cookies.get(ADMIN_SESSION_COOKIE)
    session = getattr(app.state, "admin_session", None)
    if not session or not token or session["token"] != token or session["expires"] < datetime.now():
        return False
    return True

from fastapi.routing import APIRoute

# Protege todas as rotas /admin exceto /admin/login
@app.middleware("http")
async def admin_protect_middleware(request: Request, call_next):
    if request.url.path.startswith("/admin") and not request.url.path.startswith("/admin/login"):
        if not is_admin_authenticated(request):
            return RedirectResponse("/admin/login")
    response = await call_next(request)
    return response

@app.get("/debug/tabelas")
def debug_list_tables(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"))
    tables = [row[0] for row in result]
    return {"tables": tables}
