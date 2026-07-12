import hashlib
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from api.decoder import decrypt_config
from model.database import get_db, Config as ConfigModel, Site as SiteModel, Parse as ParseModel
from model.bean import VodConfig, ConfigImportRequest

router = APIRouter()


def compute_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


async def parse_config(data: dict) -> VodConfig:
    return VodConfig(**data)


@router.get("/")
async def list_configs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ConfigModel).order_by(ConfigModel.id.desc()))
    configs = result.scalars().all()
    return {
        "code": 0,
        "data": [
            {
                "id": c.id,
                "name": c.name,
                "url": c.url,
                "type": c.type,
                "hash": c.hash,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
                "is_active": c.is_active,
            }
            for c in configs
        ],
    }


@router.post("/import")
async def import_config(
    request: Request,
    url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    json_str: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    body = await request.body()
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            json_body = json.loads(body)
            url = url or json_body.get("url")
            json_str = json_str or json_body.get("content") or json_body.get("json_str")
        except Exception:
            pass
    raw_content = ""

    if url:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            raw_content = resp.text
    elif file:
        raw_content = (await file.read()).decode("utf-8")
    elif json_str:
        raw_content = json_str
    else:
        raise HTTPException(status_code=400, detail="Must provide url, file, or json")

    try:
        decrypted = decrypt_config(raw_content)
        data = json.loads(decrypted)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="JSON 格式错误，请检查配置内容")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"解密失败: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"配置解析失败: {str(e)}")

    cfg = await parse_config(data)
    cfg_hash = compute_hash(raw_content)

    existing = await db.execute(select(ConfigModel).where(ConfigModel.hash == cfg_hash))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Config already exists")

    name = data.get("name", "") or data.get("wall", "") or "Imported Config"
    config_type = "vod"
    if not cfg.sites and cfg.lives:
        config_type = "live"

    config_entry = ConfigModel(
        name=name,
        url=url or "",
        type=config_type,
        content=raw_content,
        hash=cfg_hash,
        is_active=1,
    )
    db.add(config_entry)
    await db.flush()

    for site in cfg.sites:
        site_entry = SiteModel(
            config_id=config_entry.id,
            key=site.key,
            name=site.name,
            type=site.type,
            api=site.api,
            ext=site.get_ext_str(),
            player_type=site.playerType,
            searchable=site.searchable,
            quick_search=site.quickSearch,
            filterable=site.filterable,
        )
        db.add(site_entry)

    for parse in cfg.parses:
        parse_entry = ParseModel(
            config_id=config_entry.id,
            name=parse.name,
            url=parse.url,
            type=parse.type,
            ext=json.dumps(parse.ext, ensure_ascii=False) if isinstance(parse.ext, dict) else str(parse.ext),
        )
        db.add(parse_entry)

    await db.commit()

    return {
        "code": 0,
        "site_count": len(cfg.sites),
        "live_count": len(cfg.lives),
        "parse_count": len(cfg.parses),
    }


@router.delete("/{config_id}")
async def delete_config(config_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ConfigModel).where(ConfigModel.id == config_id))
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")

    await db.delete(config)
    await db.commit()
    return {"code": 0}


@router.put("/{config_id}/activate")
async def activate_config(config_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ConfigModel).where(ConfigModel.id == config_id))
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")

    await db.execute(update(ConfigModel).values(is_active=0))
    config.is_active = 1
    await db.commit()
    return {"code": 0}


@router.get("/site/")
async def list_sites(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ConfigModel).where(ConfigModel.is_active == 1).limit(1)
    )
    active_config = result.scalar_one_or_none()
    if not active_config:
        return {"code": 0, "data": []}

    site_result = await db.execute(
        select(SiteModel).where(SiteModel.config_id == active_config.id)
    )
    sites = site_result.scalars().all()
    return {
        "code": 0,
        "data": [
            {
                "id": s.id,
                "key": s.key,
                "name": s.name,
                "type": s.type,
                "api": s.api,
                "ext": s.ext,
                "player_type": s.player_type,
                "searchable": s.searchable,
                "quick_search": s.quick_search,
                "filterable": s.filterable,
            }
            for s in sites
        ],
    }
