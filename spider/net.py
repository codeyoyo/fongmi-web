"""异步 HTTP 客户端，替代原 OkHttp 网络层"""
import httpx
from loguru import logger


def _build_client(proxy_url: str = "") -> httpx.AsyncClient:
    kwargs = dict(follow_redirects=True, timeout=30.0, verify=False)
    if proxy_url:
        kwargs["proxy"] = proxy_url
    return httpx.AsyncClient(**kwargs)


class NetClient:
    def __init__(self):
        self._proxy = ""
        self.client = _build_client()

    async def get(self, url, headers=None, params=None) -> str:
        resp = await self.client.get(url, headers=headers, params=params)
        resp.raise_for_status()
        return resp.text

    async def post(self, url, data=None, headers=None) -> str:
        resp = await self.client.post(url, data=data, headers=headers)
        resp.raise_for_status()
        return resp.text

    async def get_bytes(self, url, headers=None) -> bytes:
        resp = await self.client.get(url, headers=headers)
        resp.raise_for_status()
        return resp.content

    def set_proxy(self, proxy_url: str):
        self._proxy = proxy_url
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(1) as pool:
                    pool.submit(asyncio.run, self.client.aclose()).result(timeout=5)
            else:
                loop.run_until_complete(self.client.aclose())
        except Exception:
            pass
        self.client = _build_client(proxy_url)
        logger.info(f"Proxy set to {proxy_url}")

    async def close(self):
        await self.client.aclose()
