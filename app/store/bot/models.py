from dataclasses import dataclass
from datetime import datetime

from app.store.database.gino import db


@dataclass
class Game:
    id: int
    chat_id: int
    status: str
    start: datetime
    end: datetime
    theme_id: int
#    Лист из вопросов которые были использованы
#    (для того что бы можно было продолжить игру после падения
#    и что бы вопросы не повторялись)


class GameModel(db.Model):
    __tablename__ = "games"

    id = db.Column(db.Integer(), primary_key=True)
    chat_id = db.Column(db.Integer(), nullable=False, unique=True)
    status = db.Column(db.String(), nullable=False)
    start = db.Column(db.DateTime(), nullable=False)
    end = db.Column(db.DateTime(), nullable=False)
    theme_id = db.Column(db.ForeignKey("themes.id"), nullable=False) # ondelete="CASCADE"
    last_question = db.Column(db.Integer())

    def to_dc(self):
        return Game(
            id=self.id,
            chat_id=self.chat_id,
            status=self.status,
            start=self.start,
            end=self.end,
            theme_id=self.theme_id,
        )


@dataclass
class User:
    id: int
    name: str


class UserModel(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(), nullable=False)

    def to_dc(self):
        return User(
            id=self.id,
            name=self.name,
        )


@dataclass
class Score:
    game_id: int
    user_id: int
    count: int


class ScoreModel(db.Model):
    __tablename__ = "scores"

    id = db.Column(db.Integer(), primary_key=True)
    game_id = db.Column(db.ForeignKey("games.id"), nullable=False)
    user_id = db.Column(db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    count = db.Column(db.Integer(), nullable=False)

    def to_dc(self):
        return Score(
            game_id=self.game_id,
            user_id=self.user_id,
            count=self.count,
        )