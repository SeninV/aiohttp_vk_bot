from datetime import datetime
from typing import List, Optional

from app.base.base_accessor import BaseAccessor
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
        # if user:
        #     return user.user_id
        return None if user is None else user.user_id

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
        # if game:
        #     return game.to_dc()
        return None if game is None else game.to_dc()

    async def last_game(self, chat_id: int) -> Optional[Game]:
        last_game = await GameModel.query.where(GameModel.chat_id == chat_id).order_by(GameModel.id.desc()).gino.first()
        return None if last_game is None else last_game.to_dc()


    async def get_game_questions(self, id_: int) -> Optional[List[str]]:
        questions = await self.get_game(id_)
        questions = questions.get_question
        # if questions:
        #     return questions
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

    def theme_response(self, theme) -> str:
        text = ""
        for i in theme:
            if i != "No_theme":
                text += f"%0A {i} "
        return text

    def answer_response(self, answer) -> str:
        text = ""
        for i, ans in enumerate(answer, 1):
            text += f"%0A {i}) {ans.title} "
        return text

    def get_answer(self, answer) -> str:
        for ans in answer:
            if ans.is_correct:
                return ans.title

    async def get_scores(self, game_id, user_id) -> Optional[Score]:
        score = await ScoreModel.query.where(ScoreModel.game_id == game_id).where(ScoreModel.user_id == user_id).gino.first()
        return None if score is None else score

    async def get_user_attempts(self, game_id) -> bool:
        user_attempts = await ScoreModel.query.where(ScoreModel.game_id == game_id).gino.all()
        all = 0
        count = 0
        for i, att in enumerate(user_attempts, 1):
            all += att.user_attempts
            count = i
        if all == count:
            return True
        else:
            return False


    async def stat_game_response(self, game_id) -> str:
        participants = await ScoreModel.query.where(ScoreModel.game_id == game_id).order_by(ScoreModel.count.desc()).gino.all()
        text = ""
        for i, par in enumerate(participants, 1):
            text += f"%0A {i}) @id{par.user_id} - {par.count}"
        return text

        # await self.app.store.vk_api.send_keyboard(
        #     Message(
        #         text="Клава",
        #         peer_id=update.object.peer_id,
        #     )
        # )
