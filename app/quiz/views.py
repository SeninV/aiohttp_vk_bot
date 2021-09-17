from aiohttp.web_exceptions import HTTPConflict, HTTPNotFound, HTTPBadRequest
from aiohttp_apispec import request_schema, response_schema, querystring_schema

from app.quiz.models import Answer
from app.quiz.schemes import (
    ThemeSchema,
    ThemeListSchema,
    QuestionSchema,
    ThemeIdSchema,
    ListQuestionSchema,
)
from app.web.app import View
from app.web.mixins import AuthRequiredMixin
from app.web.utils import json_response


class ThemeAddView(AuthRequiredMixin, View):
    @request_schema(ThemeSchema)
    @response_schema(ThemeSchema)
    async def post(self):
        title = self.data["title"]
        existing_theme = await self.store.quizzes.get_theme_by_title(title)
        if existing_theme:
            raise HTTPConflict
        theme = await self.store.quizzes.create_theme(title=title)
        return json_response(data=ThemeSchema().dump(theme))


class ThemeListView(AuthRequiredMixin, View):
    @response_schema(ThemeListSchema)
    async def get(self):
        themes = await self.store.quizzes.list_themes()
        return json_response(data=ThemeListSchema().dump({"themes": themes}))


class QuestionAddView(AuthRequiredMixin, View):
    @request_schema(QuestionSchema)
    @response_schema(QuestionSchema)
    async def post(self):
        title = self.data["title"]
        existing_question = await self.store.quizzes.get_question_by_title(title)
        if existing_question:
            raise HTTPConflict

        theme_id = self.data["theme_id"]
        theme = await self.store.quizzes.get_theme_by_id(id_=theme_id)
        if not theme:
            raise HTTPNotFound

        if len(self.data["answers"]) < 2:
            raise HTTPBadRequest

        parsed_answers = []
        correct = []
        for answer in self.data["answers"]:
            answer = Answer(title=answer["title"], is_correct=answer["is_correct"])
            if answer.is_correct and True in correct:
                raise HTTPBadRequest
            correct.append(answer.is_correct)
            parsed_answers.append(answer)

        if not any(correct):
            raise HTTPBadRequest

        question = await self.store.quizzes.create_question(
            title=title,
            theme_id=theme_id,
            answers=parsed_answers,
        )
        return json_response(data=QuestionSchema().dump(question))


class QuestionListView(AuthRequiredMixin, View):
    @querystring_schema(ThemeIdSchema)
    @response_schema(ListQuestionSchema)
    async def get(self):
        questions = await self.store.quizzes.list_questions(
            theme_id=self.data.get("theme_id")
        )
        return json_response(
            data=ListQuestionSchema().dump(
                {
                    "questions": questions,
                }
            )
        )
