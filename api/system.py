"""System Settings API (proxy, etc.)"""
import json
import os
from fastapi import APIRouter

from spider.proxy_config import get_proxy, set_proxy

router = APIRouter()


@router.get("/system/config")
async def get_config():
    return {"code": 0, "data": {"proxy": get_proxy()}}


@router.post("/system/config")
async def update_config(body: dict):
    proxy = body.get("proxy", "")
    set_proxy(proxy)
    return {"code": 0}
