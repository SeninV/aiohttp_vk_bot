import typing


if typing.TYPE_CHECKING:
    from app.web.app import Application


def setup_routes(app: "Application"):
    from app.admin.views import AdminLoginView
    from app.admin.views import AdminCurrentView
    from app.admin.views import AdminGameStat
    from app.admin.views import AdminGames

    app.router.add_view("/admin.login", AdminLoginView)
    app.router.add_view("/admin.current", AdminCurrentView)
    app.router.add_view("/admin.fetch_games", AdminGames)
    app.router.add_view("/admin.fetch_game_stats", AdminGameStat)
