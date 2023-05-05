from dataclasses import dataclass
from hashlib import sha256
from typing import Optional

from app.store.database.gino import db


@dataclass
class Admin:
    id: int
    email: str
    password: Optional[str] = None

    def check_password(self, password: str) -> bool:
        return self.password == sha256(password.encode()).hexdigest()


class AdminModel(db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer(), primary_key=True)
    email = db.Column(db.String(), nullable=False)
    password = db.Column(db.String(), nullable=False)

    def to_dc(self):
        return Admin(id=self.id, email=self.email, password=self.password)
