"""Spider Engine - dispatches to correct runtime based on site type"""
import hashlib
import threading
from collections import OrderedDict
from loguru import logger

try:
    from model.bean import Site
except ImportError:
    from spider.models import Site


class _LRUCache:
    def __init__(self, maxsize=50):
        self._store = OrderedDict()
        self._max = maxsize

    def get(self, key):
        if key in self._store:
            self._store.move_to_end(key)
            return self._store[key]
        return None

    def put(self, key, value):
        if key in self._store:
            self._store.move_to_end(key)
        else:
            if len(self._store) >= self._max:
                self._store.popitem(last=False)
        self._store[key] = value

    def clear(self):
        self._store.clear()


class _SpiderInstance:
    def __init__(self, spider_type, api, ext, jar):
        self.spider_type = spider_type
        self.api = api
        self.ext = ext
        self.jar = jar
        self._runtime = None
        self._lock = threading.Lock()

    def _ensure_runtime(self):
        if self._runtime is not None:
            return
        with self._lock:
            if self._runtime is not None:
                return
            if self.spider_type == 1:
                from spider.http_spider import HttpSpider
                self._runtime = HttpSpider(self.api, self.ext or "")
            elif self.spider_type == 3:
                from spider.js_runtime import SpiderJSRuntime
                rt = SpiderJSRuntime()
                rt.load_spider(self._read_api())
                self._runtime = rt
            else:
                logger.warning(f"Unsupported type: {self.spider_type}")

    def _read_api(self):
        import os
        if os.path.isfile(self.api):
            with open(self.api, "r", encoding="utf-8") as f:
                return f.read()
        return self.api

    def call(self, method, *args):
        self._ensure_runtime()
        if self._runtime is None:
            return {}
        return self._runtime.call(method, *args)


class SpiderEngine:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._cache = _LRUCache()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def _key(self, site):
        return hashlib.md5(f"{site.key}|{site.api}|{site.ext}|{site.jar}".encode()).hexdigest()

    def get_spider(self, site):
        k = self._key(site)
        spider = self._cache.get(k)
        if spider:
            return spider
        spider = _SpiderInstance(site.type, site.api, site.ext, site.jar)
        self._cache.put(k, spider)
        return spider


engine = SpiderEngine.get_instance()


async def home_content(site, filter=True):
    spider = engine.get_spider(site)
    import asyncio
    return await asyncio.to_thread(spider.call, "homeContent", filter)


async def category_content(site, tid, pg, filter, extend):
    spider = engine.get_spider(site)
    import asyncio
    return await asyncio.to_thread(spider.call, "categoryContent", tid, pg, filter, extend)


async def detail_content(site, ids):
    spider = engine.get_spider(site)
    import asyncio
    return await asyncio.to_thread(spider.call, "detailContent", ids)


async def search_content(site, key, quick=False, pg=""):
    spider = engine.get_spider(site)
    import asyncio
    return await asyncio.to_thread(spider.call, "searchContent", key)


async def player_content(site, flag, id, vip_flags):
    spider = engine.get_spider(site)
    import asyncio
    return await asyncio.to_thread(spider.call, "playerContent", flag, id)


async def live_content(site, url=""):
    spider = engine.get_spider(site)
    import asyncio
    return await asyncio.to_thread(spider.call, "liveContent", url)
