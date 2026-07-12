"""引擎使用示例"""
import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from spider.engine import SpiderEngine
from spider.js_runtime import SpiderJSRuntime

JS_SPIDER_CODE = """
function homeContent(filter) {
    return JSON.stringify({
        class: [
            { type_id: "movie", type_name: "电影" },
            { type_id: "tv", type_name: "电视剧" }
        ],
        list: [
            { vod_id: "100", vod_name: "示例电影", vod_pic: "https://example.com/poster.jpg" }
        ]
    });
}

function categoryContent(tid, pg, filter, extend) {
    return JSON.stringify({
        list: [
            { vod_id: "101", vod_name: "动作片-" + tid, vod_pic: "", vod_remarks: "HD" },
            { vod_id: "102", vod_name: "喜剧片-" + tid, vod_pic: "", vod_remarks: "1080P" }
        ],
        page: parseInt(pg),
        pagecount: 10,
        total: 20
    });
}

function detailContent(ids) {
    return JSON.stringify({
        list: [{
            vod_id: ids[0],
            vod_name: "示例详情",
            vod_pic: "https://example.com/poster.jpg",
            vod_year: "2024",
            vod_area: "中国大陆",
            vod_remarks: "正片",
            vod_actor: "演员A, 演员B",
            vod_director: "导演C",
            vod_content: "这是影片简介描述。",
            vod_play_from: "zyk",
            vod_play_url: "第1集$https://example.com/play1.m3u8#第2集$https://example.com/play2.m3u8"
        }]
    });
}

function searchContent(key, quick) {
    return JSON.stringify({
        list: [
            { vod_id: "200", vod_name: "搜索结果: " + key, vod_pic: "", vod_remarks: "首播" }
        ]
    });
}

function playerContent(flag, id, vipFlags) {
    return JSON.stringify({
        url: id,
        header: { "User-Agent": "Mozilla/5.0" }
    });
}
""".strip()


async def demo_js():
    print("=" * 60)
    print("Demo 1: QuickJS 引擎 - 执行 JS 爬虫")
    print("=" * 60)

    rt = SpiderJSRuntime()
    rt.load_spider(JS_SPIDER_CODE)

    print("\n[homeContent]")
    result = rt.call("homeContent", True)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    print("\n[categoryContent]")
    result = rt.call("categoryContent", "movie", "1", True, {})
    print(json.dumps(result, ensure_ascii=False, indent=2))

    print("\n[detailContent]")
    result = rt.call("detailContent", ["100"])
    print(json.dumps(result, ensure_ascii=False, indent=2))

    print("\n[searchContent]")
    result = rt.call("searchContent", "测试", False)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    print("\n[playerContent]")
    result = rt.call("playerContent", "zyk", "https://example.com/play1.m3u8", [])
    print(json.dumps(result, ensure_ascii=False, indent=2))

    rt.destroy()
    print("\nJS  demo completed")


async def demo_py():
    print("=" * 60)
    print("Demo 2: Python 爬虫 - subprocess 隔离执行")
    print("=" * 60)

    from spider.py_runtime import SpiderPyRuntime
    rt = SpiderPyRuntime()
    script = os.path.join(os.path.dirname(__file__), "test_spider.py")

    print("\n[homeContent]")
    result = await rt.call("homeContent", script, True)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    print("\n[categoryContent]")
    result = await rt.call("categoryContent", script, "tv", "1", True, {})
    print(json.dumps(result, ensure_ascii=False, indent=2))

    print("\n[searchContent]")
    result = await rt.call("searchContent", script, "动作片", False)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    print("\nPython demo completed")


async def demo_engine():
    print("=" * 60)
    print("Demo 3: SpiderEngine 统一入口")
    print("=" * 60)

    from model.bean import Site
    engine = SpiderEngine.get_instance()

    site = Site(
        key="test_js",
        name="测试站点",
        type=3,
        api="",
        ext="",
    )
    print(f"\n站点: {site.name} (type={site.type})")
    print(f"缓存大小: {len(engine._cache)}")

    spider = await engine.get_spider(site)
    print(f"获取 Spider 实例成功")

    result = engine.clear_cache()
    print(f"清空缓存后大小: {len(engine._cache)}")

    print("\nEngine demo completed")


if __name__ == "__main__":
    asyncio.run(demo_js())
    print()
    asyncio.run(demo_py())
    print()
    asyncio.run(demo_engine())
