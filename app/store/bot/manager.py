import typing
from logging import getLogger

from aiohttp.web_exceptions import HTTPConflict

from app.quiz.schemes import ThemeListSchema
from app.store.bot.models import StartGame
from app.store.vk_api.dataclasses import Update, Message

if typing.TYPE_CHECKING:
    from app.web.app import Application


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.bot = None
        self.logger = getLogger("handler")
        self.flag_new_game = StartGame(start_game=False)
        self.flag_start_game = StartGame(start_game=False)


    async def start_game(self, update, theme):
        # Ставим флаг что игра уже начата
        self.flag_start_game.start_game = True
        # создаем игру в бд
        game_id = await self.app.store.bot_accessor.create_game(chat_id=update.object.peer_id,
                                                      status="Start",
                                                      theme=theme,
                                                      last_question=0
                                                      )
        # смотрим кто есть в чате, и для каждого пользователя создаем запись в бд и счет
        members = await self.app.store.vk_api.get_members(chat_id=update.object.peer_id)
        for member in members:
            if member > 1:
                existing_user = await self.app.store.bot_accessor.get_user(member)
                # создаем пользователя если такого нет в бд
                if not existing_user:
                    user_id = await self.app.store.bot_accessor.create_user(member)
                    await self.app.store.bot_accessor.create_user_score(game_id=game_id,
                                                                        user_id=user_id,
                                                                        count=1,
                                                                        )
                else:
                    await self.app.store.bot_accessor.create_user_score(game_id=game_id,
                                                                        user_id=existing_user,
                                                                        count=1,
                                                                        )

    async def handle_updates(self, updates: list[Update]):
        for update in updates:
            a = 1
            # Если игрок пишет начать игру
            if update.object.body == 'a' and self.flag_new_game.start_game != True:
                # ставим флаг о создании новой игры
                self.flag_new_game.start_game = True
                # получаем список тем в удобном формате
                themes = await self.app.store.bot_accessor.get_list_themes_for_response()
                text_themes = self.app.store.bot_accessor.theme_response(themes)
                # высылаем список тем, что бы пользователь определился
                await self.app.store.vk_api.send_message(
                    Message(
                        text=f"Выберите тему: {text_themes}",
                        peer_id=update.object.peer_id,
                    )
                )

            # Если игрок уже начал игру и выбрал тему
            elif self.flag_new_game.start_game == True and self.flag_start_game.start_game == False:
                themes = await self.app.store.bot_accessor.get_list_themes_for_response()
                for theme in themes:
                    if update.object.body == theme:
                        await self.start_game(update, theme)

            elif self.flag_start_game == True:

                pass

            else:
                await self.app.store.vk_api.send_message(
                    Message(
                        text="s!",
                        peer_id=update.object.peer_id,
                    )
                )
