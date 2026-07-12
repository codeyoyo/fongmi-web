"""Live TV API - M3U/TXT/JSON parsing with multi-line channel merging"""
import json
import re
import httpx
from fastapi import APIRouter, Query
from loguru import logger

from api.decoder import decrypt_config
from model.database import async_session, Config as ConfigModel
from sqlalchemy import select

router = APIRouter(prefix="/live", tags=["live"])

from spider.proxy_config import get_proxy_url

_PROXY_URL = get_proxy_url()


async def _get_config():
    async with async_session() as session:
        result = await session.execute(
            select(ConfigModel).where(ConfigModel.is_active == 1).limit(1)
        )
        return result.scalar_one_or_none()


async def _fetch_url(url: str) -> str:
    client_kwargs = dict(timeout=15.0, verify=False, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
    if _PROXY_URL:
        client_kwargs["proxy"] = _PROXY_URL
    async with httpx.AsyncClient(**client_kwargs) as client:
        resp = await client.get(url)
        return resp.text


@router.get("/groups")
async def live_groups():
    cfg = await _get_config()
    if not cfg:
        return []
    try:
        data = json.loads(decrypt_config(cfg.content))
        lives = data.get("lives", [])
        return [{"name": lv.get("name", f"Source {idx}"), "type": lv.get("type", 0),
                 "url": lv.get("url", ""), "epg": lv.get("epg", "")}
                for idx, lv in enumerate(lives)]
    except Exception as e:
        logger.error(f"live_groups error: {e}")
        return []


@router.get("/channels")
async def live_channels(source_idx: int = Query(default=0)):
    cfg = await _get_config()
    if not cfg:
        return []
    try:
        data = json.loads(decrypt_config(cfg.content))
        lives = data.get("lives", [])
        if source_idx >= len(lives):
            return []
        lv = lives[source_idx]
        url = lv.get("url", "")
        if not url:
            return []

        text = await _fetch_url(url)
        if "#EXTM3U" in text or "#EXTINF" in text:
            return _parse_m3u(text)
        else:
            return _parse_txt(text)
    except Exception as e:
        logger.error(f"live_channels error: {e}")
        return []


def _merge_channel(name: str, raw_url: str, groups: dict, group_name: str):
    """Merge a channel URL into the group, combining duplicates by name."""
    url = raw_url.strip().split("|")[0].strip()
    if not url or "://" not in url:
        return
    if group_name not in groups:
        groups[group_name] = {}
    channels = groups[group_name]
    if name in channels:
        existing_urls = channels[name]["urls"]
        if url not in existing_urls:
            existing_urls.append(url)
    else:
        channels[name] = {"name": name, "urls": [url], "current_index": 0}


def _parse_m3u(text: str) -> list:
    groups = {}
    current_group = "Default"
    ch_name = ""

    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("#EXTINF:"):
            gt = re.search(r'group-title="([^"]*)"', line)
            if gt:
                current_group = gt.group(1)
            m = re.search(r',(.+?)$', line)
            if m:
                ch_name = m.group(1).strip()
        elif line and not line.startswith("#") and "://" in line:
            _merge_channel(ch_name or "Channel", line, groups, current_group)
            ch_name = ""

    return [{"name": g, "channels": list(c.values())} for g, c in groups.items()]


def _parse_txt(text: str) -> list:
    groups = {}
    current_group = "Default"

    for line in text.split("\n"):
        line = line.strip()
        if "#genre#" in line:
            current_group = line.replace("#genre#", "").strip()
        elif "," in line and "://" in line:
            parts = line.split(",", 1)
            if len(parts) == 2:
                name = parts[0].strip()
                for url in parts[1].split("#"):
                    _merge_channel(name, url, groups, current_group)

    return [{"name": g, "channels": list(c.values())} for g, c in groups.items()]
