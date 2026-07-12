"""Image Proxy - bypass CORS for thumbnails"""
from fastapi import APIRouter, Query
from fastapi.responses import Response

router = APIRouter(prefix="/img", tags=["img"])

# Direct image extensions
_IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".ico"}


@router.get("/proxy")
async def image_proxy(url: str = Query(...)):
    """Proxy image requests to bypass CORS"""
    import httpx
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.google.com/",
    }
    
    try:
        async with httpx.AsyncClient(
            timeout=10.0, verify=False, follow_redirects=True, headers=headers
        ) as client:
            resp = await client.get(url)
            
            content_type = resp.headers.get("content-type", "image/jpeg")
            if not content_type.startswith("image/"):
                content_type = "image/jpeg"
            
            return Response(
                content=resp.content,
                media_type=content_type,
                headers={
                    "Cache-Control": "public, max-age=86400",
                    "Access-Control-Allow-Origin": "*",
                }
            )
    except Exception:
        # Return 1x1 transparent pixel on error
        pixel = bytes.fromhex("47494839326131000600000000000000")
        return Response(content=pixel, media_type="image/gif")
