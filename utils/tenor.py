import random
from typing import Optional

import aiohttp

from config import TENOR_API_KEY


class TenorObject:
    _BASE_URL = "https://tenor.googleapis.com/v2/search"
    _API_KEY = TENOR_API_KEY
    _LIMIT = 4

    async def search_async(self, query: str) -> Optional[str]:
        if not self._API_KEY:
            return None
        async with aiohttp.ClientSession() as session:
            async with session.get(self._BASE_URL, params={"key": self._API_KEY, "q": query, "limit": self._LIMIT}) as resp:
                data = await resp.json()
                return random.choice(data["results"])["url"] if data["results"] else None
