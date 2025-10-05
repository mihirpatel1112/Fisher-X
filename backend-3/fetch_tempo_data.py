import os, time, json, requests

API_URL = "https://cmr.earthdata.nasa.gov/search/granules.json"
COLLECTION_CONCEPT_ID = "C2930763263-LARC_CLOUD"   # 你的 collection
CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_SECONDS", "600"))

HEADERS = {"User-Agent":"nasa-clean-skies/0.1", "Client-Id":"nasa-clean-skies"}
STATE_FILE = "cmr_seen.json"
DATA_RELS = {"http://esipfed.org/ns/fedsearch/1.1/data#", "enclosure"}

def load_state():
    try:
        if os.path.exists(STATE_FILE):
            return set(json.load(open(STATE_FILE)))
    except Exception:
        pass
    return set()

def save_state(seen_ids):
    try:
        json.dump(sorted(seen_ids), open(STATE_FILE, "w"))
    except Exception as e:
        print(f"[WARN] save state failed: {e}")

def fetch_latest(n=10):
    """拿最新 n 条 granule（按开始时间倒序）"""
    params = {
        "collection_concept_id": COLLECTION_CONCEPT_ID,
        "sort_key": "-start_date",
        "page_size": n
    }
    r = requests.get(API_URL, params=params, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json().get("feed", {}).get("entry", []) or []

def extract_download_links(entry):
    links = entry.get("links", []) or []
    return [l["href"] for l in links if l.get("rel") in DATA_RELS]

def check_once(seen):
    entries = fetch_latest(10)
    if not entries:
        print("[INFO] 最新列表为空。")
        return seen, False

    found_new = False
    for e in entries:
        gid = e.get("id")
        if not gid or gid in seen:
            continue
        found_new = True
        seen.add(gid)

        title = e.get("title", "N/A")
        t0, t1 = e.get("time_start"), e.get("time_end")
        dls = extract_download_links(e)
        print("—— 发现新 granule ——")
        print("标题:", title)
        print("ID:", gid)
        print("时间范围:", t0, "→", t1)
        print("下载链接:", dls[0] if dls else "(未提供 data 链接)")

    if not found_new:
        print("[INFO] 没有发现新发布的数据。")
    return seen, found_new

def main():
    print(f"[RUN] 每 {CHECK_INTERVAL_SECONDS//60} 分钟检查一次（Ctrl+C 退出）")
    seen = load_state()
    # 首次初始化：把当前最新的若干条记为“已见”
    if not seen:
        entries = fetch_latest(10)
        for e in entries:
            if e.get("id"):
                seen.add(e["id"])
        save_state(seen)
        print(f"[INIT] 初始化完成，记录了 {len(seen)} 条当前最新的 granule。")

    while True:
        try:
            seen, changed = check_once(seen)
            if changed:
                save_state(seen)
        except requests.RequestException as e:
            print(f"[HTTP] 请求错误：{e}")
        except Exception as e:
            print(f"[ERR] 未知错误：{e}")
        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
