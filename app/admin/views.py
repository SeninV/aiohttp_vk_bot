
from aiohttp_apispec import request_schema, response_schema
from aiohttp_session import new_session

from app.admin.schemes import AdminSchema, ListGameSchema, GameSchema, ListStatGameSchema, UserSchema
from app.web.app import View
from aiohttp.web import HTTPForbidden, HTTPUnauthorized

from app.web.mixins import AuthRequiredMixin
from app.web.utils import json_response


class AdminLoginView(View):
    @request_schema(AdminSchema)
    @response_schema(AdminSchema)
    async def post(self):
        email, password = self.data["email"], self.data["password"]
        admin = await self.store.admins.get_by_email(email)
        if not admin or not admin.check_password(password):
            raise HTTPForbidden
        admin_data = AdminSchema().dump(admin)
        response = json_response(data=admin_data)
        session = await new_session(request=self.request)
        session["admin"] = admin_data
        return response


class AdminCurrentView(View):
    @response_schema(AdminSchema)
    async def get(self):
        if self.request.admin:
            return json_response(data=AdminSchema().dump(self.request.admin))
        raise HTTPUnauthorized


class AdminGames(AuthRequiredMixin, View):
    @response_schema(ListGameSchema)
    async def get(self):
        limit = self.request.query.get("limit")
        offset = self.request.query.get("offset")

        games = await self.store.bot_accessor.list_games(limit=limit, offset=offset)
        for a in games:
            a.duration = (a.end - a.start)

        return json_response(data=ListGameSchema().dump(
            {
                "total": len(games),
                "games": games,
            }
        ))


class AdminGameStat(AuthRequiredMixin, View):
    async def get(self):

        games = await self.store.bot_accessor.list_game_stats()

        games_total = 0
        duration_total = 0
        day = games[0].end.day
        all_days = 1
        count = {}

        for game in games:
            count[game.winner] = 1
            games_total += 1
            duration_total = duration_total + (game.end - game.start).total_seconds()
            if day != game.end.day:
                all_days += 1
        for game in games:
            count[game.winner] += 1
        a = max(count , key=count.get)
        winner = UserSchema().dump(
            {
                "user_id": a,
                "win_count": count[a]
            }
        )
        game_avg_per_day = games_total/all_days
        duration_avg = duration_total/games_total


        return json_response(data=ListStatGameSchema().dump(
            {
                "game_avg_per_day": game_avg_per_day,
                "winner": winner,
                "duration_total": duration_total,
                "games_total": games_total,
                "duration_avg": duration_avg,
            }
        ))
