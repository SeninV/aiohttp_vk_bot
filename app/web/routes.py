import typing

if typing.TYPE_CHECKING:
    from app.web.app import Application

def setup_routes(app: "Application"):
    from app.admin.routes import setup_routes as admin_setup_routes
    from app.quiz.routes import setup_routes as quiz_setup_routes

    admin_setup_routes(app)
    quiz_setup_routes(app)
