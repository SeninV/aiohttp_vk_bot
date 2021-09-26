import typing
from logging import getLogger
import random

from aiohttp.web_exceptions import HTTPConflict

from app.quiz.schemes import ThemeListSchema
from app.store.bot.models import StartGame, ScoreModel, GameModel
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
        self.flag_next_question = StartGame(start_game=True)
        self.game_id = None
        self.theme_id = None
        self.all_theme_questions = None
        self.right_answer = None # что бы каждый раз не обращаться к бд за правильным ответом для сравнения
        self.game_score = None
        self.user_attempts = None


    async def start_game(self, update, theme):
        # Ставим флаг что игра уже начата
        self.flag_start_game.start_game = True
        # создаем игру в бд
        game_id = await self.app.store.bot_accessor.create_game(chat_id=update.object.peer_id,
                                                                status="Start",
                                                                theme=theme,
                                                                used_questions=""
                                                                )
        self.game_id = game_id
        self.theme_id = (await self.app.store.quizzes.get_theme_by_title(theme)).id
        # Создаем список вопросов, для данной темы
        self.all_theme_questions = []
        for question in (await self.app.store.quizzes.list_questions(theme_id=self.theme_id)):
            self.all_theme_questions.append(question.title)
        # смотрим кто есть в чате, и для каждого пользователя создаем запись в бд и счет
        members = await self.app.store.vk_api.get_members(chat_id=update.object.peer_id)
        for member in members:
            if member > 1:
                self.game_score = {f"{member}": 0}
                self.user_attempts = {f"{member}": 0}
                existing_user = await self.app.store.bot_accessor.get_user(member)
                # создаем пользователя если такого нет в бд
                if not existing_user:
                    user_id = await self.app.store.bot_accessor.create_user(member)
                    await self.app.store.bot_accessor.create_user_score(game_id=self.game_id,
                                                                        user_id=user_id,
                                                                        count=0,
                                                                        )
                else:
                    await self.app.store.bot_accessor.create_user_score(game_id=game_id,
                                                                        user_id=existing_user,
                                                                        count=0,
                                                                        )


    async def end_game(self, update):

        pass

    async def ask_question(self, update):
        self.flag_next_question.start_game = False
        used_questions = await self.app.store.bot_accessor.get_game_questions(id_=self.game_id)
        unused_questions = list(set(self.all_theme_questions) - set(used_questions))
        if unused_questions:
            question_title = random.choice(unused_questions)
            used_questions = used_questions + [question_title]
            await GameModel.update.where(GameModel.id == self.game_id).gino.first({"used_questions": used_questions})
            question = await self.app.store.quizzes.get_question_by_title(question_title)
            self.right_answer = self.app.store.bot_accessor.get_answer(question.answers)
            answer = self.app.store.bot_accessor.answer_response(question.answers)
            await self.app.store.vk_api.send_message(
                Message(
                    text=f"Вопрос: {question.title} %0A Варианты ответов: {answer}",
                    peer_id=update.object.peer_id,
                )
            )
        else:
            await self.app.store.vk_api.send_message(
                Message(
                    text="Вопросы кончились",
                    peer_id=update.object.peer_id,
                )
            )
            await self.end_game(update)


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
                        # посылаем первую тему
                        await self.ask_question(update)



            # Посылание вопросов
            elif self.flag_start_game.start_game == True and self.flag_next_question.start_game == True:
                await self.ask_question(update)

            elif self.flag_start_game.start_game == True and self.flag_next_question.start_game == False:
                if self.user_attempts[f"{update.object.user_id}"] < 5:
                    self.user_attempts[f"{update.object.user_id}"] += 1
                    if update.object.body == self.right_answer:
                        self.flag_next_question.start_game = True
                        self.game_score[f"{update.object.user_id}"] += 1
                        score = self.game_score[f"{update.object.user_id}"]
                        # Обнуляем попытки пользователей
                        self.user_attempts = self.user_attempts.fromkeys(self.user_attempts, 0)
                        await ScoreModel.update.where(ScoreModel.game_id == self.game_id).gino.all(
                            {"count": score})
                        await self.app.store.vk_api.send_message(
                            Message(
                                text=f"Правильный ответ!",
                                peer_id=update.object.peer_id,
                            )
                        )
                    # посылаем следующий вопрос
                        await self.ask_question(update)

                else:
                    await self.app.store.vk_api.send_message(
                        Message(
                            text=f"Количество попыток у пользователя {update.object.user_id} закончилось",
                            peer_id=update.object.peer_id,
                        )
                    )


                pass


            else:





                # e = await self.app.store.bot_accessor.get_game(id_=34)
                # print(e)
                # print(await GameModel.query.where(GameModel.id == 34).gino.first())

                # await ScoreModel.update.where(ScoreModel.game_id == 17).gino.all({"game_id":17, "user_id":88628474 , "count": 22})


                # await self.app.store.vk_api.send_message(
                #     Message(
                #         text="s!",
                #         peer_id=update.object.peer_id,
                #     )
                # )
                pass