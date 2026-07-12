"""Aggregate search - all sites in parallel, merged results"""
import json
import asyncio
import ssl
import urllib.request
from loguru import logger
from sqlalchemy import select


_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE


async def search_all(keyword: str) -> list:
    """Search all VOD sites in parallel, return merged items with pictures"""
    from model.database import async_session, Site as SiteModel

    async with async_session() as session:
        result = await session.execute(
            select(SiteModel).where(SiteModel.searchable == 1)
        )
        site_rows = result.scalars().all()

    tasks = [_search_one_row(s.key, s.name, s.api, s.type, s.ext, keyword) for s in site_rows]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    merged = []
    for r in results:
        if isinstance(r, list):
            merged.extend(r)
        elif isinstance(r, Exception):
            logger.debug(f"Search failed: {r}")

    seen = set()
    unique = []
    for item in merged:
        name = item.get("vod_name", "")
        site_key = item.get("_site_key", "")
        key = f"{site_key}:{name}"
        if name and key not in seen:
            seen.add(key)
            unique.append(item)

    return unique


async def _search_one_row(site_key, site_name, api_url, site_type, site_ext, keyword):
    """Search a single site by type"""
    if not api_url:
        return []

    if site_type == 1:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _sync_search, site_key, site_name, api_url, keyword)
    elif site_type == 3:
        from spider.engine import search_content
        from model.bean import Site
        site = Site(
            key=site_key, name=site_name, type=site_type,
            api=api_url, ext=site_ext or "", jar="",
        )
        try:
            result = await search_content(site, keyword)
            items = result.get("list", [])
            for item in items:
                item["_site_key"] = site_key
                item["_site_name"] = site_name
            return items
        except Exception as e:
            logger.debug(f"Search {site_key} error: {e}")
            return []
    else:
        return []


def _sync_search(site_key, site_name, api_url, keyword):
    """Synchronous search using urllib"""
    base = api_url.split("?")[0].rstrip("/") if "?" in api_url else api_url.rstrip("/")
    vod_path = "api.php/provide/vod/"
    if vod_path not in base:
        base = base + "/" + vod_path

    import urllib.parse
    params = urllib.parse.urlencode({"wd": keyword, "pg": "1"})
    url = f"{base}?{params}"

    req = urllib.request.Request(url, headers={"User-Agent": "okhttp/3.10.0"})
    try:
        with urllib.request.urlopen(req, timeout=10, context=_SSL_CTX) as resp:
            text = resp.read().decode("utf-8", errors="replace").strip()
            if not text or "暂不支持" in text or len(text) < 10:
                return []
            data = json.loads(text)
            items = data.get("list", [])

            filtered = []
            for item in items:
                vid = str(item.get("vod_id", ""))
                name = item.get("vod_name", "")
                parts = vid.split("_")
                if len(parts) == 3 and all(p.isdigit() for p in parts):
                    continue
                if name.startswith("\u2708") or "\u5173\u6ce8" in name:
                    continue
                item["_site_key"] = site_key
                item["_site_name"] = site_name
                filtered.append(item)

            if filtered:
                has_pic = any(i.get("vod_pic") for i in filtered)
                if not has_pic:
                    _fetch_pics_sync(base, filtered)

            return filtered
    except Exception as e:
        logger.debug(f"Search {site_key} error: {e}")
        return []


def _fetch_pics_sync(base, items):
    """Fetch pictures for items"""
    try:
        ids = [str(i["vod_id"]) for i in items if i.get("vod_id")]
        if not ids:
            return
        clean_base = base.split("?")[0].rstrip("/") if "?" in base else base.rstrip("/")
        vod_path = "api.php/provide/vod/"
        if vod_path not in clean_base:
            clean_base = clean_base + "/" + vod_path
        import urllib.parse
        params = urllib.parse.urlencode({"ac": "detail", "ids": ",".join(ids)})
        url = f"{clean_base}?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": "okhttp/3.10.0"})
        with urllib.request.urlopen(req, timeout=15, context=_SSL_CTX) as resp:
            text = resp.read().decode("utf-8", errors="replace").strip()
            detail = json.loads(text)
            pic_map = {}
            for d in detail.get("list", []):
                vid = str(d.get("vod_id", ""))
                pic = d.get("vod_pic", "")
                if vid and pic:
                    pic_map[vid] = pic
            for item in items:
                vid = str(item.get("vod_id", ""))
                if not item.get("vod_pic") and vid in pic_map:
                    item["vod_pic"] = pic_map[vid]
    except Exception as e:
        logger.debug(f"Fetch pics error: {e}")
