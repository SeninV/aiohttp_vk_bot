from marshmallow import Schema, fields


class AdminSchema(Schema):
    id = fields.Int(required=False)
    email = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)


class UserSchema(Schema):
    user_id = fields.Int(required=True)
    count = fields.Int(required=True)


class GameSchema(Schema):
    id = fields.Int(required=False)
    chat_id = fields.Int(required=True)
    start = fields.Str(required=True)
    end = fields.Str(required=True)
    theme = fields.Str(required=True)
    winner = fields.Nested(UserSchema, many=False)
    duration = fields.Str(required=True)


class ListGameSchema(Schema):
    total = fields.Int(required=True)
    games = fields.Nested(GameSchema, many=True)


class UserWinSchema(Schema):
    user_id = fields.Int(required=True)
    win_count = fields.Int(required=True)


class ListStatGameSchema(Schema):
    game_avg_per_day = fields.Float(required=True)
    winner = fields.Nested(UserWinSchema, many=False)
    duration_total = fields.Int(required=True)
    games_total = fields.Int(required=True)
    duration_avg = fields.Int(required=True)


class GamesLimitOffsetShema(Schema):
    limit = fields.Int()
    offset = fields.Int()
