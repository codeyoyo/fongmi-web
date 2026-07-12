"""本地模型降级定义，当 model.bean 不可用时使用"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Site(BaseModel):
    key: str = ""
    name: str = ""
    type: int = 0
    api: str = ""
    playUrl: str = ""
    searchable: int = 1
    quickSearch: int = 1
    filterable: int = 1
    ext: str = ""
    jar: str = ""
    playerType: int = 0
    categories: list = []
    header: dict = {}
    style: dict = {}
    playerUrl: str = ""
    clickSelector: str = ""


class Parse(BaseModel):
    name: str = ""
    url: str = ""
    type: int = 0
    ext: dict = {}
    header: dict = {}


class Live(BaseModel):
    name: str = ""
    type: int = 0
    url: str = ""
    epg: str = ""
    logo: str = ""
    boot: bool = False
    pass_: bool = False

    class Config:
        fields = {"pass_": "pass"}


class Proxy(BaseModel):
    doh: str = ""
    url: str = ""
    ips: list = []


class VodConfig(BaseModel):
    sites: list = []
    parses: list = []
    lives: list = []
    doh: list = []
    rules: list = []
    flags: list[str] = []
    ads: list[str] = []
    wall: str = ""
    spider: str = ""
