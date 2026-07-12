"""VOD API Routes"""
import json
from fastapi import APIRouter, Query, HTTPException
from loguru import logger

from spider.engine import home_content, category_content, detail_content, search_content, player_content
from model.database import async_session, Site as SiteModel, Config as ConfigModel, Parse as ParseModel
from model.bean import Site
from sqlalchemy import select

router = APIRouter(prefix="/vod", tags=["vod"])


async def _get_site(site_key: str):
    async with async_session() as session:
        result = await session.execute(select(SiteModel).where(SiteModel.key == site_key))
        db = result.scalar_one_or_none()
    if not db:
        raise HTTPException(404, "站点不存在")
    ext = db.ext or ""
    if isinstance(ext, dict):
        ext = json.dumps(ext, ensure_ascii=False)
    site = Site(
        key=db.key, name=db.name, type=db.type,
        api=db.api, ext=ext, jar="",
        searchable=1, quickSearch=1, filterable=1,
    )
    parses = []
    async with async_session() as session:
        config_result = await session.execute(
            select(ConfigModel).where(ConfigModel.is_active == 1).limit(1)
        )
        active_config = config_result.scalar_one_or_none()
        if active_config:
            parse_result = await session.execute(
                select(ParseModel).where(ParseModel.config_id == active_config.id)
            )
            db_parses = parse_result.scalars().all()
            parses = [
                {"name": p.name, "url": p.url, "type": p.type, "ext": p.ext}
                for p in db_parses
            ]
    return site, parses


@router.get("/home")
async def vod_home(site_key: str = Query(default=""), filter: bool = Query(default=True)):
    if not site_key:
        raise HTTPException(400, "site_key required")
    site, _ = await _get_site(site_key)
    try:
        return await home_content(site, filter)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"vod_home error: {e}")
        raise HTTPException(500, str(e))


@router.get("/category")
async def vod_category(
    site_key: str = Query(...), tid: str = Query(default=""),
    pg: str = Query(default="1"), filter: bool = Query(default=True),
    extend: str = Query(default=""),
):
    site, _ = await _get_site(site_key)
    ext = {}
    if extend:
        try:
            ext = json.loads(extend)
        except json.JSONDecodeError:
            raise HTTPException(400, "extend JSON error")
    try:
        return await category_content(site, tid, pg, filter, ext)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"vod_category error: {e}")
        raise HTTPException(500, str(e))


@router.get("/detail")
async def vod_detail(site_key: str = Query(...), ids: str = Query(...)):
    site, _ = await _get_site(site_key)
    id_list = [i.strip() for i in ids.split(",") if i.strip()]
    if not id_list:
        raise HTTPException(400, "ids required")
    try:
        return await detail_content(site, id_list)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"vod_detail error: {e}")
        raise HTTPException(500, str(e))


@router.get("/search")
async def vod_search(wd: str = Query(...)):
    """Aggregate search across ALL VOD sites"""
    from spider.search import search_all
    try:
        items = await search_all(wd)
        return items
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"vod_search error: {e}")
        raise HTTPException(500, str(e))


@router.get("/player")
async def vod_player(site_key: str = Query(...), flag: str = Query(default=""),
                     id: str = Query(...), vip: str = Query(default="")):
    site, parses = await _get_site(site_key)
    vip_flags = [v.strip() for v in vip.split(",") if v.strip()] if vip else []
    try:
        result = await player_content(site, flag, id, vip_flags, parses)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"vod_player error: {e}")
        raise HTTPException(500, str(e))
