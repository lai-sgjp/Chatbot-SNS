from abc import ABC, abstractmethod
from bot.models import Reply


class BaseAdapter(ABC):
    @abstractmethod
    async def start(self):
        ...

    @abstractmethod
    async def send(self, reply: Reply):
        ...
