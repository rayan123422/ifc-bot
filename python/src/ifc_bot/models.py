from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
import datetime

Base = declarative_base()

class League(Base):
    __tablename__ = 'league'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Club(Base):
    __tablename__ = 'club'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    logo = Column(String)
    role_id = Column(String)
    budget = Column(Integer, default=0)
    roster_limit = Column(Integer, default=25)
    manager_id = Column(String)  # discord id

    players = relationship('Player', back_populates='club')

class Player(Base):
    __tablename__ = 'player'
    id = Column(Integer, primary_key=True)
    discord_id = Column(String, unique=True, index=True)
    roblox = Column(String)
    country = Column(String)
    position = Column(String)
    overall = Column(Integer, default=0)
    club_id = Column(Integer, ForeignKey('club.id'))
    market_value = Column(Integer, default=30000)
    valuation_tier = Column(Integer, default=30000)

    club = relationship('Club', back_populates='players')

class Offer(Base):
    __tablename__ = 'offer'
    id = Column(Integer, primary_key=True)
    type = Column(String, default='FREE')
    from_club_id = Column(Integer, ForeignKey('club.id'))
    to_player_id = Column(Integer, ForeignKey('player.id'))
    amount = Column(Integer, default=0)
    message = Column(Text)
    status = Column(String, default='PENDING')
    player_accepted = Column(Boolean, default=False)
    club_approved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Contract(Base):
    __tablename__ = 'contract'
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('player.id'))
    club_id = Column(Integer, ForeignKey('club.id'))
    start_date = Column(DateTime, default=datetime.datetime.utcnow)
    end_date = Column(DateTime)
    salary = Column(Integer)
    status = Column(String, default='ACTIVE')

class Transfer(Base):
    __tablename__ = 'transfer'
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('player.id'))
    from_club_id = Column(Integer, ForeignKey('club.id'))
    to_club_id = Column(Integer, ForeignKey('club.id'))
    fee = Column(Integer)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Loan(Base):
    __tablename__ = 'loan'
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('player.id'))
    owner_club_id = Column(Integer, ForeignKey('club.id'))
    loan_club_id = Column(Integer, ForeignKey('club.id'))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    fee = Column(Integer)
    salary_split = Column(String)
    recallable = Column(Boolean, default=False)
    status = Column(String, default='PENDING')

class LfpPost(Base):
    __tablename__ = 'lfp_post'
    id = Column(Integer, primary_key=True)
    club_id = Column(Integer, ForeignKey('club.id'))
    manager_id = Column(String)
    position = Column(String)
    players_needed = Column(Integer)
    min_overall = Column(Integer)
    description = Column(Text)
    status = Column(String, default='ACTIVE')

class LfpInterest(Base):
    __tablename__ = 'lfp_interest'
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('lfp_post.id'))
    player_id = Column(Integer, ForeignKey('player.id'))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class BudgetTransaction(Base):
    __tablename__ = 'budget_transaction'
    id = Column(Integer, primary_key=True)
    club_id = Column(Integer, ForeignKey('club.id'))
    type = Column(String)
    amount = Column(Integer)
    details = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class PlayerStats(Base):
    __tablename__ = 'player_stats'
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('player.id'))
    match_id = Column(Integer)
    goals = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    rating = Column(Integer)

class PlayerValueHistory(Base):
    __tablename__ = 'player_value_history'
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('player.id'))
    old_value = Column(Integer)
    new_value = Column(Integer)
    staff_id = Column(String)
    reason = Column(Text)
    changed_at = Column(DateTime, default=datetime.datetime.utcnow)

class Setting(Base):
    __tablename__ = 'setting'
    key = Column(String, primary_key=True)
    value = Column(String)

class AuditLog(Base):
    __tablename__ = 'audit_log'
    id = Column(Integer, primary_key=True)
    actor_id = Column(String)
    action = Column(String)
    details = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
