"""Proxy configuration - loads from data/config.json"""
import json
import os

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "config.json")


def get_proxy() -> str:
    """Get proxy URL from config file, fallback to env vars"""
    try:
        with open(_CONFIG_PATH, "r") as f:
            cfg = json.load(f)
        proxy = cfg.get("proxy", "")
        if proxy:
            return proxy
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY") or ""


def set_proxy(proxy: str):
    """Save proxy URL to config file"""
    try:
        with open(_CONFIG_PATH, "r") as f:
            cfg = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        cfg = {}
    cfg["proxy"] = proxy
    os.makedirs(os.path.dirname(_CONFIG_PATH), exist_ok=True)
    with open(_CONFIG_PATH, "w") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def get_proxy_url() -> str:
    """Get proxy URL string"""
    return get_proxy()


def get_proxy_dict():
    """Get proxy dict for backwards compat"""
    proxy = get_proxy()
    if proxy:
        return {"https://": proxy, "http://": proxy}
    return None
