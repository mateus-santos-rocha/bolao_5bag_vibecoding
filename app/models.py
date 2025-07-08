from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Enum
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()

class Team(Base):
    __tablename__ = 'teams'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    is_admin = Column(Boolean, default=False)

class MatchType(enum.Enum):
    MD1 = 'MD1'
    MD3 = 'MD3'
    MD5 = 'MD5'

class Match(Base):
    __tablename__ = 'matches'
    id = Column(Integer, primary_key=True)
    team1 = Column(String, nullable=False)
    team2 = Column(String, nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    match_type = Column(Enum(MatchType), nullable=False)
    result = Column(String)  # Ex: '2-1', '1-0', etc

class Bet(Base):
    __tablename__ = 'bets'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    match_id = Column(Integer, ForeignKey('matches.id'))
    prediction = Column(String)  # Ex: '2-1', '1-0', etc
    timestamp = Column(DateTime)
    approved = Column(Boolean, default=True)  # Se for aposta fora do prazo
    user = relationship('User')
    match = relationship('Match')

class BetRequest(Base):
    __tablename__ = 'bet_requests'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    match_id = Column(Integer, ForeignKey('matches.id'))
    prediction = Column(String)
    timestamp = Column(DateTime)
    approved = Column(Boolean, default=None)  # None=pending, True/False=decidido
    user = relationship('User')
    match = relationship('Match')
