"""Media Player Proxy - for CORS bypass & direct play info"""
import asyncio
import hashlib
import json
import os
import tempfile
import time
from pathlib import Path
from urllib.parse import urlparse, quote, unquote
from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse, Response
from spider.proxy_config import get_proxy_url

router = APIRouter(prefix="/player", tags=["player"])
_PROXY_URL = get_proxy_url()

import httpx

_SHARED_CLIENT: httpx.AsyncClient | None = None

# ---- cache ----
CACHE_DIR = Path(tempfile.gettempdir()) / "fongmi_cache"
CACHE_MAX_SIZE = 1024 * 1024 * 1024
CACHE_TTL = 7200
_LAST_CLEANUP = 0

# ---- in-memory hot cache ----
_MEM_CACHE: dict[str, tuple[float, bytes, str]] = {}
_MEM_CACHE_MAX = 50

def _mem_get(url: str) -> tuple[bytes, str] | None:
    key = _cache_key(url)
    if key in _MEM_CACHE:
        ts, data, ct = _MEM_CACHE[key]
        if time.time() - ts < CACHE_TTL:
            _MEM_CACHE[key] = (time.time(), data, ct)
            return data, ct
        del _MEM_CACHE[key]
    return None

def _mem_set(url: str, data: bytes, ct: str):
    key = _cache_key(url)
    _MEM_CACHE[key] = (time.time(), data, ct)
    if len(_MEM_CACHE) > _MEM_CACHE_MAX:
        oldest = min(_MEM_CACHE.keys(), key=lambda k: _MEM_CACHE[k][0])
        del _MEM_CACHE[oldest]

# ---- preloader ----
_PRELOAD_SEM = asyncio.Semaphore(12)
_PRELOAD_TASKS: dict[str, asyncio.Task] = {}
_PRELOAD_LIMIT = 50
_PRELOAD_BLOCK_COUNT = 5


def _cache_key(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()


def _cache_path(key: str) -> Path:
    return CACHE_DIR / key[:2] / key


def _cache_get(url: str) -> tuple[bytes, str] | None:
    hit = _mem_get(url)
    if hit:
        return hit
    key = _cache_key(url)
    path = _cache_path(key)
    meta = path.with_suffix(".meta")
    if not path.exists() or not meta.exists():
        return None
    if time.time() - path.stat().st_mtime > CACHE_TTL:
        path.unlink(missing_ok=True); meta.unlink(missing_ok=True)
        return None
    path.touch(); meta.touch()
    data, ct = path.read_bytes(), meta.read_text().strip()
    _mem_set(url, data, ct)
    return data, ct


def _cache_set(url: str, data: bytes, ct: str):
    _mem_set(url, data, ct)
    key = _cache_key(url)
    path = _cache_path(key)
    meta = path.with_suffix(".meta")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data); meta.write_text(ct)
    _maybe_cleanup()


def _maybe_cleanup():
    global _LAST_CLEANUP
    if time.time() - _LAST_CLEANUP < 300:
        return
    _LAST_CLEANUP = time.time()
    try:
        if not CACHE_DIR.exists():
            return
        entries, total = [], 0
        for f in CACHE_DIR.rglob("*"):
            if f.is_file() and f.suffix != ".meta":
                try:
                    sz = f.stat().st_size
                    entries.append((f.stat().st_atime, f))
                    total += sz
                except OSError:
                    pass
        if total <= CACHE_MAX_SIZE:
            return
        entries.sort(key=lambda x: x[0])
        for _, f in entries:
            if total <= CACHE_MAX_SIZE:
                break
            try:
                sz = f.stat().st_size
                f.with_suffix(".meta").unlink(missing_ok=True)
                f.unlink(missing_ok=True)
                total -= sz
            except OSError:
                pass
    except Exception:
        pass


def _client() -> httpx.AsyncClient:
    global _SHARED_CLIENT
    if _SHARED_CLIENT is None or _SHARED_CLIENT.is_closed:
        _SHARED_CLIENT = httpx.AsyncClient(
            follow_redirects=True, verify=False,
            proxy=_PROXY_URL if _PROXY_URL else None,
            timeout=120.0,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        )
    return _SHARED_CLIENT


# ========== m3u8 rewrite ==========

def _abs_url(url: str, base: str) -> str:
    """Resolve a (possibly relative) URL against a base URL."""
    if url.startswith("http"):
        return url
    parsed = urlparse(base)
    p = parsed.path.rsplit("/", 1)[0] + "/"
    if url.startswith("/"):
        return f"{parsed.scheme}://{parsed.netloc}{url}"
    return f"{parsed.scheme}://{parsed.netloc}{p}{url}"


def _rewrite_m3u8(content: str, playlist_url: str) -> str:
    """Rewrite all segment URIs in an m3u8 to proxy URLs."""
    out = []
    for line in content.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("<"):
            out.append(line)
            continue
        # Non-comment line = segment URI → rewrite to proxy URL
        abs_url = _abs_url(s, playlist_url)
        proxy_url = f"/api/player/proxy/{quote(abs_url, safe='')}"
        indent = line[:len(line) - len(line.lstrip())]
        out.append(f"{indent}{proxy_url}")
    return "\n".join(out)


def _extract_segment_urls(content: str, playlist_url: str) -> list[str]:
    """Extract absolute segment URLs from m3u8 for preloading."""
    urls = []
    for line in content.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("<"):
            continue
        urls.append(_abs_url(s, playlist_url))
    return urls


# ========== background preloader ==========

async def _preload_one(client: httpx.AsyncClient, url: str):
    if _cache_get(url) is not None:
        return
    try:
        async with _PRELOAD_SEM:
            resp = await client.get(url, timeout=30.0)
        if resp.status_code == 200:
            ct = "video/mp2t"
            if ".mp4" in url:
                ct = "video/mp4"
            _cache_set(url, resp.content, ct)
    except Exception:
        pass


async def _preload_worker(playlist_url: str, segments: list[str]):
    client = _client()
    targets = [u for u in segments[:_PRELOAD_LIMIT] if ".m3u8" not in u]
    await asyncio.gather(*[_preload_one(client, u) for u in targets])


def _start_preload(playlist_url: str, segments: list[str]):
    if playlist_url in _PRELOAD_TASKS and not _PRELOAD_TASKS[playlist_url].done():
        return
    t = asyncio.create_task(_preload_worker(playlist_url, segments))
    _PRELOAD_TASKS[playlist_url] = t
    t.add_done_callback(lambda _: _PRELOAD_TASKS.pop(playlist_url, None))


async def _preload_and_block(segments: list[str]):
    targets = [u for u in segments if ".m3u8" not in u and _cache_get(u) is None][:_PRELOAD_BLOCK_COUNT]
    if not targets:
        return
    client = _client()
    sem = asyncio.Semaphore(8)
    async def _dl(u: str):
        async with sem:
            try:
                resp = await client.get(u, timeout=30.0)
                if resp.status_code == 200:
                    ct = "video/mp4" if ".mp4" in u else "video/mp2t"
                    _cache_set(u, resp.content, ct)
            except Exception:
                pass
    await asyncio.gather(*[_dl(u) for u in targets])


# ========== routes ==========

@router.get("/live_url")
async def live_url(source_idx: int = Query(...), channel_idx: int = Query(default=0)):
    return {"code": "use_direct", "msg": "Use the URL from /api/live/channels directly"}


@router.get("/proxy/info")
async def proxy_info():
    total_size = total_files = 0
    if CACHE_DIR.exists():
        for f in CACHE_DIR.rglob("*"):
            if f.is_file() and f.suffix != ".meta":
                total_files += 1
                total_size += f.stat().st_size
    active = sum(1 for t in _PRELOAD_TASKS.values() if not t.done())
    return {
        "cache_size_mb": round(total_size / 1024 / 1024, 1),
        "cache_files": total_files,
        "max_size_mb": int(CACHE_MAX_SIZE / 1024 / 1024),
        "active_preloads": active,
    }


@router.api_route("/proxy/{path:path}", methods=["GET", "HEAD", "OPTIONS"])
async def media_proxy(path: str, request: Request, extra_headers: str = Query(default="")):
    real_url = unquote(path)
    if not real_url.startswith(("http://", "https://")):
        return Response(b"", status_code=400)

    range_hdr = request.headers.get("range", "")
    headers = {"User-Agent": request.headers.get("user-agent", "Mozilla/5.0")}
    if ref := request.headers.get("referer"):
        headers["Referer"] = ref
    if range_hdr:
        headers["Range"] = range_hdr
    if extra_headers:
        try:
            custom = json.loads(extra_headers)
            if isinstance(custom, dict):
                headers.update(custom)
        except json.JSONDecodeError:
            pass

    is_m3u8 = ".m3u8" in real_url
    cacheable = range_hdr == "" and any(e in real_url for e in [".ts", ".m4s", ".m4f"])

    # ---- cache hit ----
    if cacheable:
        hit = _cache_get(real_url)
        if hit:
            return Response(hit[0], headers={
                "Content-Type": hit[1],
                "Access-Control-Allow-Origin": "*",
                "Accept-Ranges": "bytes",
                "X-Cache": "HIT",
            })

    # ---- stream ----
    async def stream():
        client = _client()
        async with client.stream("GET", real_url, headers=headers) as resp:
            if is_m3u8:
                raw = await resp.aread()
                text = raw.decode("utf-8", errors="replace")
                segs = _extract_segment_urls(text, real_url)
                if segs:
                    await _preload_and_block(segs)
                    _start_preload(real_url, segs)
                rewritten = _rewrite_m3u8(text, real_url)
                yield rewritten.encode("utf-8")
            elif cacheable:
                buf = b""
                async for chunk in resp.aiter_bytes(262144):
                    buf += chunk
                    yield chunk
                if buf:
                    _cache_set(real_url, buf, "video/mp2t")
            else:
                async for chunk in resp.aiter_bytes(262144):
                    yield chunk

    mt = "application/vnd.apple.mpegurl" if is_m3u8 else \
         "video/mp2t" if ".ts" in real_url else \
         "video/mp4" if ".mp4" in real_url else \
         "video/x-flv" if ".flv" in real_url else \
         "application/octet-stream"

    return StreamingResponse(stream(), media_type=mt, headers={
        "Accept-Ranges": "bytes",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "*",
        "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
    })
