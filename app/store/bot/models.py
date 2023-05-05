from dataclasses import dataclass
from datetime import datetime
from typing import List

from app.quiz.models import Question, QuestionModel
from app.store.database.gino import db


@dataclass
class Game:
    id: int
    chat_id: int
    status: str
    start: datetime
    end: datetime
    theme: str
    used_questions: List[str]


class GameModel(db.Model):
    __tablename__ = "games"

    id = db.Column(db.Integer(), primary_key=True)
    chat_id = db.Column(db.Integer(), nullable=False)
    status = db.Column(db.String(), nullable=False)
    start = db.Column(db.DateTime(), nullable=False)
    end = db.Column(db.DateTime(), nullable=False)
    theme = db.Column(
        db.ForeignKey("themes.title"), nullable=False
    )  # ondelete="CASCADE"
    used_questions = db.Column(db.ARRAY(db.String()))

    def to_dc(self):
        return Game(
            id=self.id,
            chat_id=self.chat_id,
            status=self.status,
            start=self.start,
            end=self.end,
            theme=self.theme,
            used_questions=self.used_questions,
        )


@dataclass
class User:
    id: int
    user_id: int


class UserModel(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), nullable=False, unique=True)

    def to_dc(self):
        return User(
            id=self.id,
            user_id=self.user_id,
        )


@dataclass
class Score:
    game_id: int
    user_id: int
    count: int
    user_attempts: int


class ScoreModel(db.Model):
    __tablename__ = "scores"

    id = db.Column(db.Integer(), primary_key=True)
    game_id = db.Column(db.ForeignKey("games.id"), nullable=False)
    user_id = db.Column(
        db.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    count = db.Column(db.Integer(), nullable=False)
    user_attempts = db.Column(db.Integer(), nullable=False)

    def to_dc(self):
        return Score(
            game_id=self.game_id,
            user_id=self.user_id,
            count=self.count,
            user_attempts=self.user_attempts,
        )
