"""Media Player Proxy - for CORS bypass & direct play info"""
import os
from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse
from spider.proxy_config import get_proxy_url

router = APIRouter(prefix="/api/player", tags=["player"])

_PROXY_URL = get_proxy_url()


@router.get("/live_url")
async def live_url(source_idx: int = Query(...), channel_idx: int = Query(default=0)):
    return {"code": "use_direct", "msg": "Use the URL from /api/live/channels directly"}


@router.api_route("/proxy/{path:path}", methods=["GET", "HEAD", "OPTIONS"])
async def media_proxy(path: str, request: Request):
    """Stream proxy - bypass CORS, support Range requests for video seeking"""
    from urllib.parse import unquote
    real_url = unquote(path)
    if not real_url.startswith(("http://", "https://")):
        return StreamingResponse(iter([b""]), status_code=400)

    range_header = request.headers.get("range", "")
    referer = request.headers.get("referer", "")
    user_agent = request.headers.get("user-agent", "Mozilla/5.0")
    headers = {"User-Agent": user_agent}
    if referer:
        headers["Referer"] = referer
    if range_header:
        headers["Range"] = range_header

    async def stream():
        import httpx
        async with httpx.AsyncClient(
            follow_redirects=True, verify=False,
            proxy=_PROXY_URL,
            timeout=60.0,
        ) as client:
            async with client.stream("GET", real_url, headers=headers) as resp:
                async for chunk in resp.aiter_bytes(65536):
                    yield chunk

    media_type = "application/octet-stream"
    if ".m3u8" in real_url:
        media_type = "application/vnd.apple.mpegurl"
    elif ".ts" in real_url:
        media_type = "video/mp2t"
    elif ".mp4" in real_url:
        media_type = "video/mp4"
    elif ".flv" in real_url:
        media_type = "video/x-flv"

    return StreamingResponse(
        stream(),
        media_type=media_type,
        headers={
            "Accept-Ranges": "bytes",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
        },
    )
