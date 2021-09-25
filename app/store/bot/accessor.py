from datetime import datetime

from app.base.base_accessor import BaseAccessor
from app.quiz.schemes import ThemeListSchema
from app.store.bot.models import User, UserModel, Game, GameModel, Score, ScoreModel


class BotAccessor(BaseAccessor):

    async def create_user(self, user_id: int) -> User:
        user = await UserModel.create(
            user_id=user_id,
        )
        return user.user_id

    async def get_user(self, user_id: int) -> User:
        user = await UserModel.query.where(UserModel.user_id == user_id).gino.first()
        return None if user is None else user.user_id

    async def create_game(self, chat_id: int, status: bool, theme: int, last_question: int) -> Game:
        game = await GameModel.create(
            chat_id=chat_id,
            status=status,
            start=datetime.now(),
            end=datetime.now(),
            theme=theme,
            last_question=last_question,
        )
        return game.id

    async def create_user_score(self, game_id: int, user_id: int, count: int) -> Score:
        score = await ScoreModel.create(
            game_id=game_id,
            user_id=user_id,
            count=count,
        )
        return score.to_dc()

    async def get_list_themes_for_response(self):
        themes = await self.app.store.quizzes.list_themes()
        data = ThemeListSchema().dump({"themes": themes})["themes"]
        themes = []
        for d in data:
            themes.append(d["title"])
        return themes

    def theme_response(self, theme):
        text = ""
        for i in theme:
            text += f"%0A {i} "
        return text

        # await self.app.store.vk_api.send_keyboard(
        #     Message(
        #         text="Клава",
        #         peer_id=update.object.peer_id,
        #     )
        # )
