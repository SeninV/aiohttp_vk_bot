from datetime import datetime
from typing import List, Optional

from sqlalchemy.sql.functions import count
from gino.loader import ColumnLoader

from app.base.base_accessor import BaseAccessor
from app.quiz.models import Answer
from app.quiz.schemes import ThemeListSchema
from app.store.bot.models import User, UserModel, Game, GameModel, Score, ScoreModel


class BotAccessor(BaseAccessor):

    async def create_user(self, user_id: int) -> int:
        user = await UserModel.create(
            user_id=user_id,
        )
        return user.user_id

    async def get_user(self, user_id: int) -> Optional[int]:
        user = await UserModel.query.where(UserModel.user_id == user_id).gino.first()
        if user:
            return user.user_id

    async def create_game(self, chat_id: int, status: bool, theme: int, used_questions: list[str]) -> Game:
        game = await GameModel.create(
            chat_id=chat_id,
            status=status,
            start=datetime.now(),
            end=datetime.now(),
            theme=theme,
            used_questions=used_questions,
        )
        return game.to_dc()

    async def get_game(self, id_: int) -> Optional[Game]:
        game = await GameModel.query.where(GameModel.id == id_).gino.first()
        return None if game is None else game.to_dc()


    def _get_winner_join(self):
        return GameModel.outerjoin(
            ScoreModel,
            GameModel.id == ScoreModel.game_id,
        ).select()


    def _get_winner_load(self, query):
        return query.gino.load(
            GameModel.load(winner=ScoreModel)
        ).all()

    async def list_games(self, limit: Optional[str] = None, offset: Optional[str] = None) -> Optional[List[Game]]:
        query = self._get_winner_join().where(GameModel.winner == ScoreModel.user_id).order_by(GameModel.id.asc()).limit(limit).offset(offset)
        game_list = await self._get_winner_load(query)
        if game_list:
            return game_list

    async def list_game_stats(self) -> Optional[List[Game]]:
        game_list = await GameModel.query.gino.all()
        if game_list:
            return game_list


    async def last_game(self, chat_id: int) -> Optional[Game]:
        last_game = await GameModel.query.where(GameModel.chat_id == chat_id).order_by(GameModel.id.desc()).gino.first()
        if last_game:
            return last_game.to_dc()


    async def get_game_questions(self, id_: int) -> Optional[List[str]]:
        questions = await self.get_game(id_)
        questions = questions.used_questions
        return None if questions is None else questions

    async def create_user_score(self, game_id: int, user_id: int, count: int, user_attempts:int) -> Score:
        score = await ScoreModel.create(
            game_id=game_id,
            user_id=user_id,
            count=count,
            user_attempts=user_attempts

        )
        return score.to_dc()

    async def get_list_themes_for_response(self) -> List[str]:
        themes = await self.app.store.quizzes.list_themes()
        data = ThemeListSchema().dump({"themes": themes})["themes"]
        themes = []
        for d in data:
            themes.append(d["title"])
        return themes

    def theme_response(self, theme: List[str]) -> str:
        text = ""
        for i, th in enumerate(theme):
            if th != "No_theme":
                text += f"%0A ************ %0A {th}"
        return text

    def answer_response(self, answer: List[Answer]) -> str:
        text = ""
        for i, ans in enumerate(answer, 1):
            text += f"%0A {i}) {ans.title} "
        return text

    def answer_response_keyboard(self, answer: List[Answer]) -> List[str]:
        text = []
        for ans in answer:
            text += [ans.title]
        return text


    def get_answer(self, answer: List[Answer]) -> str:
        for ans in answer:
            if ans.is_correct:
                return ans.title

    async def get_scores(self, game_id: int, user_id: int) -> Optional[Score]:
        score = await ScoreModel.query.where(ScoreModel.game_id == game_id).where(ScoreModel.user_id == user_id).gino.first()
        if score:
            return score


    async def get_user_attempts(self, game_id: int) -> bool:
        user_attempts = await ScoreModel.query.where(ScoreModel.game_id == game_id).gino.all()
        all = 0
        count = 0
        for i, att in enumerate(user_attempts, 1):
            all += att.user_attempts
            count = i
        return all == count



    async def stat_game_response(self, game_id: int) -> str:
        participants = await ScoreModel.query.where(ScoreModel.game_id == game_id).order_by(ScoreModel.count.desc()).gino.all()
        text = ""
        for i, par in enumerate(participants, 1):
            text += f"%0A {i}) @id{par.user_id} - {par.count}"
        return text


