#!/usr/bin/env python3
"""iPhone Duo 256GB スターホワイト の店頭受け取り在庫を監視し、Discordに通知する。"""
import json
import os
import random
import sys
import time
import urllib.parse
import urllib.request

PART = "MK244J/A"
TARGETS = ["心斎橋", "梅田", "京都"]
LOCATIONS = ["542-0086", "600-8008"]
INTERVAL = 7 * 60

WEBHOOK = os.environ.get("DISCORD_WEBHOOK", "")
UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"
)


def fetch_stores(location):
    qs = urllib.parse.urlencode(
        {
            "pl": "true",
            "mts.0": "regular",
            "mts.1": "compact",
            "parts.0": PART,
            "location": location,
        }
    )
    url = f"https://www.apple.com/jp/shop/fulfillment-messages?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.load(r)
    return data["body"]["content"]["pickupMessage"]["stores"]


def check():
    found = {}
    for loc in LOCATIONS:
        for s in fetch_stores(loc):
            name = s.get("storeName", "")
            if not any(t in name for t in TARGETS):
                continue
            info = s.get("partsAvailability", {}).get(PART, {})
            found[name] = info.get("pickupDisplay") == "available"
    missing = [t for t in TARGETS if not any(t in n for n in found)]
    if missing:
        print(f"[warn] 取得結果に含まれない店舗: {missing}")
    return [n for n, ok in found.items() if ok]


def notify(msg):
    if not WEBHOOK:
        print("[error] DISCORD_WEBHOOK が未設定です")
        return
    body = json.dumps({"content": msg}).encode()
    req = urllib.request.Request(
        WEBHOOK,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "stock-monitor"},
    )
    urllib.request.urlopen(req, timeout=20).read()


def message(stores):
    return (
        "📱 **iPhone Duo 256GB スターホワイト** 在庫あり!\n"
        + "\n".join(f"・{s}" for s in stores)
        + "\nhttps://www.apple.com/jp/shop/buy-iphone/iphone-duo"
    )


def main():
    if "--test" in sys.argv:
        notify("✅ 監視システムのテスト通知です")
        return
    if "--once" in sys.argv:
        stores = check()
        print("在庫あり:", stores or "なし")
        if stores:
            notify(message(stores))
        return

    notified = set()
    while True:
        try:
            stores = set(check())
            new = stores - notified
            if new:
                notify(message(sorted(stores)))
            notified = stores
            print(time.strftime("%H:%M:%S"), "在庫あり:", sorted(stores) or "なし")
        except Exception as e:
            print("[error]", e)
        time.sleep(INTERVAL + random.randint(-60, 60))


if __name__ == "__main__":
    main()
