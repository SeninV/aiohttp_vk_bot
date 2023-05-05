import gino
from gino import Gino
from app.store.database.gino import db
from app.admin.models import *
from app.quiz.models import *
from sqlalchemy.engine.url import URL


class Database:
    db: Gino

    def __init__(self, app: "Application"):
        self.app = app
        self.db: Optional[Gino]

    async def connect(self, *_, **kw):
        self._engine = await gino.create_engine(
            URL(
                drivername="asyncpg",
                host=self.app.config.database.host,
                database=self.app.config.database.database,
                username=self.app.config.database.user,
                password=self.app.config.database.password,
                port=self.app.config.database.port,
            ),
            min_size=1,
            max_size=1,
        )
        self.db = db
        self.db.bind = self._engine

        # await self.db.set_bind(
        #     f'postgresql://{self.app.config.database.host}/{self.app.config.database.database}'
        # )
        await self.db.gino.create_all()

    async def disconnect(self, *_, **kw):
        self.app = None
        await db.pop_bind().close()
