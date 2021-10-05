from typing import Optional

from app.base.base_accessor import BaseAccessor
from app.quiz.models import (
    Theme,
    Question,
    Answer,
    QuestionModel,
    AnswerModel,
    ThemeModel,
)
from typing import List


class QuizAccessor(BaseAccessor):
    async def create_theme(self, title: str) -> Theme:
        theme = await ThemeModel.create(title=title)

        return theme.to_dc()

    async def get_theme_by_title(self, title: str) -> Optional[Theme]:
        theme_title = await ThemeModel.query.where(
            ThemeModel.title == title
        ).gino.first()
        return None if theme_title is None else theme_title.to_dc()

    async def get_theme_by_id(self, id_: int) -> Optional[Theme]:
        theme_id = await ThemeModel.get(id_)
        return None if theme_id is None else theme_id.to_dc()

    async def list_themes(self) -> List[Theme]:
        theme_list = await ThemeModel.query.gino.all()
        return [o.to_dc() for o in theme_list]

    async def create_answers(self, question_id, answers: List[Answer]):
        await AnswerModel.insert().gino.all(
            [
                {
                    "title": a.title,
                    "is_correct": a.is_correct,
                    "question_id": question_id,
                }
                for a in answers
            ]
        )

    async def create_question(
        self, title: str, theme_id: int, answers: List[Answer]
    ) -> Question:
        a = await QuestionModel.create(title=title, theme_id=theme_id)
        question = a.to_dc()
        await self.create_answers(question.id, answers)
        question.answers = answers

        return question

    def _get_question_join(self):
        return QuestionModel.outerjoin(
            AnswerModel,
            QuestionModel.id == AnswerModel.question_id,
        ).select()

    def _get_questions_load(self, query):
        return query.gino.load(
            QuestionModel.distinct(QuestionModel.id).load(add_answer=AnswerModel.load())
        ).all()

    async def get_question_by_title(self, title: str) -> Optional[Question]:
        query = self._get_question_join().where(QuestionModel.title == title)
        questions = await self._get_questions_load(query)

        return None if not questions else questions[0].to_dc()

    async def list_questions(self, theme_id: Optional[int] = None) -> List[Question]:
        question_list = await self._get_questions_load(self._get_question_join())
        if theme_id:
            theme_questions = []
            for question in question_list:
                if question.theme_id == int(theme_id):
                    theme_questions.append(question)
            return [o.to_dc() for o in theme_questions]
        else:
            return [o.to_dc() for o in question_list]
