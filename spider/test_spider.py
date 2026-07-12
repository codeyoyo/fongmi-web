"""测试用 Python 爬虫脚本，模拟 FongMi TV Spider 接口"""
import json
import sys


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "no payload"}))
        return
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        payload = json.load(f)
    method = payload["method"]
    args = payload["args"]

    if method == "homeContent":
        result = {
            "class": [
                {"type_id": "movie", "type_name": "电影"},
                {"type_id": "tv", "type_name": "电视剧"},
            ],
            "list": [
                {"vod_id": "1", "vod_name": "测试影片", "vod_pic": "http://example.com/p.jpg"},
            ],
        }
    elif method == "categoryContent":
        result = {
            "list": [
                {"vod_id": "1", "vod_name": "分类电影A", "vod_pic": ""},
                {"vod_id": "2", "vod_name": "分类电影B", "vod_pic": ""},
            ],
            "page": 1,
            "pagecount": 5,
            "total": 10,
        }
    elif method == "detailContent":
        result = {
            "list": [
                {
                    "vod_id": "1",
                    "vod_name": "详情测试",
                    "vod_play_from": "测试源",
                    "vod_play_url": "第1集$http://example.com/play1.m3u8#第2集$http://example.com/play2.m3u8",
                }
            ]
        }
    elif method == "searchContent":
        result = {
            "list": [
                {"vod_id": "1", "vod_name": f"搜索: {args[0]}", "vod_pic": ""},
            ]
        }
    elif method == "playerContent":
        result = {"url": f"http://example.com/play/{args[1]}.m3u8", "header": {}}
    else:
        result = {"error": f"unknown method: {method}"}

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
