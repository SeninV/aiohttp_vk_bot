import json
import random
import typing
from typing import Optional

from aiohttp import TCPConnector
from aiohttp.client import ClientSession

from app.base.base_accessor import BaseAccessor
from app.store.vk_api.dataclasses import Update, Message, UpdateObject
from app.store.vk_api.poller import Poller

if typing.TYPE_CHECKING:
    from app.web.app import Application

API_PATH = "https://api.vk.com/method/"


class VkApiAccessor(BaseAccessor):
    def __init__(self, app: "Application", *args, **kwargs):
        super().__init__(app, *args, **kwargs)
        self.session: Optional[ClientSession] = None
        self.key: Optional[str] = None
        self.server: Optional[str] = None
        self.poller: Optional[Poller] = None
        self.ts: Optional[int] = None

    async def connect(self, app: "Application"):
        self.session = ClientSession(connector=TCPConnector(verify_ssl=False))
        try:
            await self._get_long_poll_service()
        except Exception as e:
            self.logger.error("Exception", exc_info=e)
        # await self.send_message(
        #     message=Message(
        #         text="Включаюсь",
        #         peer_id=88628474,
        #     )
        # )
        self.poller = Poller(app.store)
        self.logger.info("start polling")
        await self.poller.start()

    async def disconnect(self, app: "Application"):
        if self.session:
            # await self.send_message(
            #     message=Message(
            #         text="Выключаюсь",
            #         peer_id=88628474,
            #     )
            # )
            await self.session.close()
        if self.poller:
            await self.poller.stop()

    @staticmethod
    def _build_query(host: str, method: str, params: dict) -> str:
        url = host + method + "?"
        if "v" not in params:
            params["v"] = "5.131"
        url += "&".join([f"{k}={v}" for k, v in params.items()])
        return url

    async def _get_long_poll_service(self):
        async with self.session.get(
            self._build_query(
                host=API_PATH,
                method="groups.getLongPollServer",
                params={
                    "group_id": self.app.config.bot.group_id,
                    "access_token": self.app.config.bot.token,
                },
            )
        ) as resp:
            data = (await resp.json())["response"]
            self.logger.info(data)
            self.key = data["key"]
            self.server = data["server"]
            self.ts = data["ts"]
            self.logger.info(self.server)

    async def poll(self):
        async with self.session.get(
            self._build_query(
                host=self.server,
                method="",
                params={
                    "act": "a_check",
                    "key": self.key,
                    "ts": self.ts,
                    "wait": 30,
                },
            )
        ) as resp:
            data = await resp.json()
            self.logger.info(data)
            self.ts = data["ts"]
            raw_updates = data.get("updates", [])
            updates = []
            for update in raw_updates:
                updates.append(
                    Update(
                        type=update["type"],
                        object=UpdateObject(
                            id=update["object"]["message"]["id"],
                            user_id=update["object"]["message"]["from_id"],
                            body=update["object"]["message"]["text"],
                            peer_id=update["object"]["message"]["peer_id"]
                        ),
                    )
                )
        return updates

    async def send_message(self, message: Message) -> None:
        async with self.session.get(
            self._build_query(
                API_PATH,
                "messages.send",
                params={
                    "random_id": random.randint(1, 2 ** 32),
                    "peer_id": message.peer_id,
                    "message": message.text,
                    "access_token": self.app.config.bot.token,
                },
            )
        ) as resp:
            data = await resp.json()
            self.logger.info(data)

    async def get_members(self, chat_id: int):
        async with self.session.get(
            self._build_query(
                API_PATH,
                "messages.getConversationMembers",
                params={
                    "random_id": random.randint(1, 2 ** 32),
                    "peer_id": chat_id,
                    "access_token": self.app.config.bot.token,
                },
        )
        ) as resp:
            data = await resp.json()
            # self.logger.info(data)
            members = []
            for i in data["response"]["items"]:
                members.append(i["member_id"])
        return members

            # data["response"]["items"]
    # Клавиатура для вк
    def get_but(self, text: str):
        return{
            "action": {
                "type": "text",
                "payload": "{\"button\": \"1\"}",
                "label": f"{text}"
            },
            "color": "negative"
        }
    def get_keyboard(self):
        keyboard = {
            "one_time": True,
            "buttons": [[
                self.get_but('asd'), self.get_but('q')
            ]]
        }
        keyboard = json.dumps(keyboard, ensure_ascii=False).encode('utf-8')
        keyboard = str(keyboard.decode('utf-8'))
        return keyboard


    async def send_keyboard(self, message: Message) -> None:
        async with self.session.get(
                self._build_query(
                    API_PATH,
                    "messages.send",
                    params={
                        "random_id": random.randint(1, 2 ** 32),
                        "peer_id": message.peer_id,
                        "message": message.text,
                        "access_token": self.app.config.bot.token,
                        "keyboard": self.get_keyboard()
                    },
                )
        ) as resp:
            data = await resp.json()
            self.logger.info(data)
