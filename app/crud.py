from sqlalchemy.orm import Session
from . import models
from datetime import datetime

def get_user_by_name(db: Session, name: str):
    return db.query(models.User).filter(models.User.name == name).first()

def get_all_users(db: Session):
    return db.query(models.User).all()

def create_user(db: Session, name: str, is_admin: bool = False):
    # Não permite usuário duplicado
    if db.query(models.User).filter(models.User.name == name).first():
        return None
    user = models.User(name=name, is_admin=is_admin)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def update_user(db: Session, user_id: int, new_name: str, is_admin: bool = False):
    user = db.query(models.User).get(user_id)
    if not user:
        return None
    # Não permite duplicidade
    if db.query(models.User).filter(models.User.name == new_name, models.User.id != user_id).first():
        return None
    user.name = new_name
    user.is_admin = is_admin
    db.commit()
    db.refresh(user)
    return user

def delete_user(db: Session, user_id: int):
    user = db.query(models.User).get(user_id)
    if user:
        db.delete(user)
        db.commit()
        return True
    return False

def get_matches(db: Session):
    return db.query(models.Match).all()

def create_match(db: Session, team1, team2, scheduled_time, match_type):
    match = models.Match(team1=team1, team2=team2, scheduled_time=scheduled_time, match_type=match_type)
    db.add(match)
    db.commit()
    db.refresh(match)
    return match

def set_match_result(db: Session, match_id, result):
    match = db.query(models.Match).get(match_id)
    if match:
        match.result = result
        db.commit()
    return match

def place_bet(db: Session, user_id, match_id, prediction, approved=True):
    bet = models.Bet(user_id=user_id, match_id=match_id, prediction=prediction, timestamp=datetime.now(), approved=approved)
    db.add(bet)
    db.commit()
    db.refresh(bet)
    return bet

def create_bet_request(db: Session, user_id, match_id, prediction):
    req = models.BetRequest(user_id=user_id, match_id=match_id, prediction=prediction, timestamp=datetime.now())
    db.add(req)
    db.commit()
    db.refresh(req)
    return req

def approve_bet_request(db: Session, req_id, approve: bool):
    req = db.query(models.BetRequest).get(req_id)
    if req:
        req.approved = approve
        db.commit()
    return req

def get_ranking(db: Session, points_func):
    users = db.query(models.User).all()
    matches = db.query(models.Match).all()
    bets = db.query(models.Bet).filter(models.Bet.approved == True).all()
    ranking = {}
    for user in users:
        score = 0
        for bet in filter(lambda b: b.user_id == user.id, bets):
            match = next((m for m in matches if m.id == bet.match_id and m.result), None)
            if match:
                score += points_func(match.match_type.value, bet.prediction, match.result)
        ranking[user.name] = score
    return sorted(ranking.items(), key=lambda x: x[1], reverse=True)

def get_teams(db: Session):
    return db.query(models.Team).all()

def create_team(db: Session, name: str):
    team = models.Team(name=name)
    db.add(team)
    db.commit()
    db.refresh(team)
    return team

def get_all_bets(db: Session):
    return db.query(models.Bet).all()

def update_bet(db: Session, user_id, match_id, prediction):
    bet = db.query(models.Bet).filter_by(user_id=user_id, match_id=match_id).first()
    if bet:
        bet.prediction = prediction
        bet.timestamp = datetime.now()
        db.commit()
        db.refresh(bet)
    return bet
