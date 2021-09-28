import typing
from datetime import datetime
from logging import getLogger
import random
import time
from app.store.bot.models import ScoreModel, GameModel
from app.store.vk_api.dataclasses import Update, Message, KeyboardMessage

if typing.TYPE_CHECKING:
    from app.web.app import Application


class BotManager:
    def __init__(self, app: "Application"):
        self.app = app
        self.bot = None
        self.logger = getLogger("handler")
        self.start = {}
        self.time = {}
        # self.session = {}


    async def start_game(self, update, theme, game_id):
        # Ставим флаг что игра уже начата
        self.start[game_id] = True
        await GameModel.update.where(GameModel.chat_id == update.object.peer_id). \
            where(GameModel.status == "start").gino.first({"theme": theme})

        # смотрим кто   есть в чате, и для каждого пользователя создаем запись в бд и счет
        members = await self.app.store.vk_api.get_members(chat_id=update.object.peer_id)
        for member in members:
            if member > 1:
                # self.game_score[member] = 0
                existing_user = await self.app.store.bot_accessor.get_user(member)
                # создаем пользователя если такого нет в бд
                if not existing_user:
                    user_id = await self.app.store.bot_accessor.create_user(member)
                    await self.app.store.bot_accessor.create_user_score(game_id=game_id,
                                                                        user_id=user_id,
                                                                        count=0,
                                                                        user_attempts=0
                                                                        )
                else:
                    await self.app.store.bot_accessor.create_user_score(game_id=game_id,
                                                                        user_id=existing_user,
                                                                        count=0,
                                                                        user_attempts=0
                                                                        )


    async def end_game(self, update, game_id):
        await GameModel.update.where(GameModel.chat_id == update.object.peer_id).where(GameModel.id == game_id)\
            .gino.first({"end": datetime.now() , "status": "finish"})
        participants = await self.app.store.bot_accessor.stat_game_response(game_id)
        await self.app.store.vk_api.delet_keyboard(
            Message(
                text=f"Конец игры! %0A Итоговый счет: {participants}",
                peer_id=update.object.peer_id,
            )
        )
        self.start[game_id] = False




    async def ask_question(self, update, theme, game_id):
        # self.flag_next_question.flag = False
        await GameModel.update.where(GameModel.chat_id == update.object.peer_id). \
            where(GameModel.status == "start").gino.first({"status": "ask"})
        # "end": datetime.now(),
        # Смотрим какие вопросы были использованы и какие вопросы
        used_questions = await self.app.store.bot_accessor.get_game_questions(game_id)
        theme_id = (await self.app.store.quizzes.get_theme_by_title(theme)).id
        all_theme_questions = []
        for question in (await self.app.store.quizzes.list_questions(theme_id)):
            all_theme_questions.append(question.title)
        unused_questions = list(set(all_theme_questions) - set(used_questions))
        if unused_questions:
            question_title = random.choice(unused_questions)
            used_questions = used_questions + [question_title]
            await GameModel.update.where(GameModel.id == game_id).gino.first({"used_questions": used_questions})
            question = await self.app.store.quizzes.get_question_by_title(question_title)
            # answer = self.app.store.bot_accessor.answer_response(question.answers)
            #
            # await self.app.store.vk_api.send_message(
            #     Message(
            #         text=f"Вопрос: {question.title} %0A Варианты ответов: {answer}",
            #         peer_id=update.object.peer_id,
            #     )
            # )
            keyboard_answer = self.app.store.bot_accessor.answer_response_keyboard(question.answers)
            await self.app.store.vk_api.send_keyboard(
                KeyboardMessage(
                    text=f"Вопрос: {question.title} %0A",
                    peer_id=update.object.peer_id,
                    keyboard_text=keyboard_answer,
                )
            )
            self.time[game_id] = time.time() + 30
        else:
            await self.app.store.vk_api.send_message(
                Message(
                    text="Вопросы кончились",
                    peer_id=update.object.peer_id,
                )
            )
            await self.end_game(update, game_id)


    async def handle_updates(self, updates: list[Update]):
        # self.session = self.session.fromkeys(self.session, False)
        for update in updates:
            # Берем статус последней игры сыгранной в этой бесед(если она есть)
            game = await self.app.store.bot_accessor.last_game(update.object.peer_id)
            # Если игр в беседе до этого не было
            if game:
                status = game.status
            else:
                status = "finish"

            if update.object.body == '\start' and status == 'finish':
                # ставим флаг о создании новой игры
                await self.app.store.bot_accessor.create_game(chat_id=update.object.peer_id,
                                                              status="start",
                                                              theme="No_theme",
                                                              used_questions=""
                                                              )
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
            elif status == 'start':
                self.start[game.id] = False
                themes = await self.app.store.bot_accessor.get_list_themes_for_response()
                for theme in themes:
                    if update.object.body == theme:
                        game_id = game.id
                        await self.start_game(update, theme, game_id)
                        # посылаем первую тему
                        await self.ask_question(update, theme, game_id)
                # Если не нашел тему то посылаем список тем заново
                if self.start[game.id] == False:
                    themes = await self.app.store.bot_accessor.get_list_themes_for_response()
                    text_themes = self.app.store.bot_accessor.theme_response(themes)
                    # высылаем список тем, что бы пользователь определился
                    await self.app.store.vk_api.send_message(
                        Message(
                            text=f"Тема не найдена( %0A Выберите тему: {text_themes}",
                            peer_id=update.object.peer_id,
                        )
                    )



            # Прерывание раунда
            elif update.object.body == '\end' and status == 'ask':
                await self.end_game(update, game.id)

            # Статистика раунда
            elif update.object.body == '\stat' and status == 'ask':
                participants = await self.app.store.bot_accessor.stat_game_response(game.id)
                await self.app.store.vk_api.send_message(
                    Message(
                        text=f"Статистика игры: %0A Счет: {participants}",
                        peer_id=update.object.peer_id,
                    )
                )
            # Посылание вопросов
            # elif status == 'ask':
            #     await self.ask_question(update)
            elif status == 'ask':
                game_id = game.id
                # Проверяем не выключился ли сервер на этом моменте, если выключился обнуляем попытки и задаем следующий вопрос
                user_attempts = (await self.app.store.bot_accessor.get_scores(game_id, update.object.user_id)).user_attempts
                if self.start == {}:
                    self.start[game.id] = True

                # Задаем вопрос повторно
                    last_question = (await self.app.store.bot_accessor.get_game_questions(game.id))[-1]
                    question = await self.app.store.quizzes.get_question_by_title(last_question)

                    # answer = self.app.store.bot_accessor.answer_response(question.answers)
                    # await self.app.store.vk_api.send_message(
                    #     Message(
                    #         text=f"Вопрос: {question.title} %0A Варианты ответов: {answer}",
                    #         peer_id=update.object.peer_id,
                    #     )
                    # )
                    keyboard_answer = self.app.store.bot_accessor.answer_response_keyboard(question.answers)
                    await self.app.store.vk_api.send_keyboard(
                        KeyboardMessage(
                            text=f"Вопрос: {question.title} %0A",
                            peer_id=update.object.peer_id,
                            keyboard_text=keyboard_answer,
                        )
                    )
                    self.time[game_id] = time.time() + 30


                elif user_attempts < 1:
                    await ScoreModel.update.where(ScoreModel.game_id == game_id). \
                        where(ScoreModel.user_id == update.object.user_id).gino.all({"user_attempts": 1})
                    last_question = (await self.app.store.bot_accessor.get_game_questions(game_id))[-1]
                    question = await self.app.store.quizzes.get_question_by_title(last_question)
                    right_answer = self.app.store.bot_accessor.get_answer(question.answers)
                    theme = game.theme
                    # второе сравнение для клавиатуры в беседе

                    if self.time[game_id] > time.time() and (update.object.body == right_answer or
                                                    update.object.body == f"[club206933962|@club206933962] {right_answer}"):
                        score = (await self.app.store.bot_accessor.get_scores(game_id, update.object.user_id)).count
                        score = score + 1
                        # Обнуляем попытки пользователей
                        await ScoreModel.update.where(ScoreModel.game_id == game_id).gino.all({"user_attempts": 0})
                        await ScoreModel.update.where(ScoreModel.game_id == game_id).\
                            where(ScoreModel.user_id == update.object.user_id).gino.all({"count": score})
                        # await self.app.store.vk_api.send_message(
                        #     Message(
                        #         text=f"Правильный ответ!",
                        #         peer_id=update.object.peer_id,
                        #     )
                        # )
                        await self.app.store.vk_api.delet_keyboard(
                            Message(
                                text=f"Правильный ответ!",
                                peer_id=update.object.peer_id,
                            )
                        )
                    # посылаем следующий вопрос
                        await self.ask_question(update, theme, game_id)
                    # elif not await self.app.store.bot_accessor.get_user_attempts(game_id):
                    #     keyboard_answer = self.app.store.bot_accessor.answer_response_keyboard(question.answers)
                    #     await self.app.store.vk_api.send_keyboard(
                    #         KeyboardMessage(
                    #             text=f"Вопрос: {question.title} %0A",
                    #             peer_id=update.object.peer_id,
                    #             keyboard_text=keyboard_answer
                    #         )
                    #     )
                    elif self.time[game_id] < time.time():

                        await self.app.store.vk_api.delet_keyboard(
                            Message(
                                text=f"Время на вопрос истекло ( %0A Правильный ответ: {right_answer}",
                                peer_id=update.object.peer_id,
                            )
                        )
                        await ScoreModel.update.where(ScoreModel.game_id == game_id).gino.all({"user_attempts": 0})

                        await self.ask_question(update, theme, game_id)

                    elif await self.app.store.bot_accessor.get_user_attempts(game_id):
                        await self.app.store.vk_api.delet_keyboard(
                            Message(
                                text=f"Никто не ответил правильно( %0A Правильный ответ: {right_answer}",
                                peer_id=update.object.peer_id,
                            )
                        )
                        await ScoreModel.update.where(ScoreModel.game_id == game_id).gino.all({"user_attempts": 0})

                        await self.ask_question(update, theme, game_id)


                else:
                    await self.app.store.vk_api.send_message(
                        Message(
                            text=f"Количество попыток у пользователя @id{update.object.user_id} закончилось",
                            peer_id=update.object.peer_id,
                        )
                    )


            else:
                await self.app.store.vk_api.send_message(
                    Message(
                        text="\start - начало игры %0A \stat - статистика по игре  %0A \end - окончание по игры",
                        peer_id=update.object.peer_id,
                    )
                )

            # self.session[game.chat_id] = True


