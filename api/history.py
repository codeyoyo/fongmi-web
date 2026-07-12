"""History & Keep API"""
import json
from datetime import datetime
from fastapi import APIRouter, Query

from model.database import async_session, History as HistoryModel, Keep as KeepModel
from sqlalchemy import select, delete, desc

router = APIRouter()


@router.get("/history")
async def list_history():
    async with async_session() as session:
        result = await session.execute(
            select(HistoryModel).order_by(desc(HistoryModel.created_at)).limit(100)
        )
        items = result.scalars().all()
    return [
        {"id": h.id, "site_key": h.site_key, "vod_id": h.vod_id, "name": h.name,
         "pic": h.pic, "episode": h.episode, "position": h.position, "duration": h.duration,
         "time": h.created_at.isoformat() if h.created_at else ""}
        for h in items
    ]


@router.post("/history")
async def add_history(body: dict):
    site_key = body.get("site_key", "")
    vod_id = body.get("vod_id", "")
    name = body.get("name", "")
    pic = body.get("pic", "")
    episode = body.get("episode", "")
    position = body.get("position", 0)
    duration = body.get("duration", 0)
    async with async_session() as session:
        result = await session.execute(
            select(HistoryModel).where(HistoryModel.site_key == site_key, HistoryModel.vod_id == vod_id)
        )
        existing = result.scalar_one_or_none()
        now = datetime.now()
        if existing:
            existing.name = name
            existing.pic = pic
            existing.episode = episode
            if position:
                existing.position = position
            if duration:
                existing.duration = duration
            existing.created_at = now
        else:
            session.add(HistoryModel(site_key=site_key, vod_id=vod_id, name=name,
                                     pic=pic, episode=episode, position=position,
                                     duration=duration, created_at=now))
        await session.commit()
    return {"code": 0}


@router.put("/history")
async def update_history(body: dict):
    site_key = body.get("site_key", "")
    vod_id = body.get("vod_id", "")
    position = body.get("position", 0)
    duration = body.get("duration", 0)
    async with async_session() as session:
        result = await session.execute(
            select(HistoryModel).where(HistoryModel.site_key == site_key, HistoryModel.vod_id == vod_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.position = position
            existing.duration = duration
            existing.updated_at = datetime.now()
            await session.commit()
    return {"code": 0}


@router.delete("/history/{history_id}")
async def delete_history(history_id: int):
    async with async_session() as session:
        await session.execute(delete(HistoryModel).where(HistoryModel.id == history_id))
        await session.commit()
    return {"code": 0}


@router.delete("/history")
async def clear_history():
    async with async_session() as session:
        await session.execute(delete(HistoryModel))
        await session.commit()
    return {"code": 0}


@router.get("/keep")
async def list_keep():
    async with async_session() as session:
        result = await session.execute(
            select(KeepModel).order_by(desc(KeepModel.created_at)).limit(100)
        )
        items = result.scalars().all()
    return [
        {"id": k.id, "site_key": k.site_key, "vod_id": k.vod_id, "name": k.name,
         "pic": k.pic, "type": k.type, "time": k.created_at.isoformat() if k.created_at else ""}
        for k in items
    ]


@router.post("/keep")
async def add_keep(body: dict):
    site_key = body.get("site_key", "")
    vod_id = body.get("vod_id", "")
    name = body.get("name", "")
    pic = body.get("pic", "")
    keep_type = body.get("type", "vod")
    async with async_session() as session:
        result = await session.execute(
            select(KeepModel).where(KeepModel.site_key == site_key, KeepModel.vod_id == vod_id)
        )
        if result.scalar_one_or_none():
            return {"code": 0, "msg": "already_keep"}
        session.add(KeepModel(site_key=site_key, vod_id=vod_id, name=name,
                              pic=pic, type=keep_type, created_at=datetime.now()))
        await session.commit()
    return {"code": 0}


@router.delete("/keep/{keep_id}")
async def delete_keep(keep_id: int):
    async with async_session() as session:
        await session.execute(delete(KeepModel).where(KeepModel.id == keep_id))
        await session.commit()
    return {"code": 0}


@router.get("/keep/check")
async def check_keep(site_key: str = Query(...), vod_id: str = Query(...)):
    async with async_session() as session:
        result = await session.execute(
            select(KeepModel).where(KeepModel.site_key == site_key, KeepModel.vod_id == vod_id)
        )
        exists = result.scalar_one_or_none() is not None
    return {"is_keep": exists}
