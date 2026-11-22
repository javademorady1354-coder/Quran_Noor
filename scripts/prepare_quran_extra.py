#!/usr/bin/env python3
"""Package only Persian QuranEnc resources explicitly present in its public catalogue."""
import concurrent.futures
import json
import pathlib
import time
import urllib.error
import urllib.request

BASE = "https://quranenc.com/api/v1"
OUT = pathlib.Path("app/src/main/assets/quran-extra-data.js")
HEADERS = {"User-Agent": "QuranNoor/1.2 (offline resource packaging)"}

def get_json(url):
    last_error = None
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=90) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            if attempt == 3:
                break
            time.sleep(2 ** attempt)
    raise RuntimeError(f"QuranEnc request failed: {url}: {last_error}")

def main():
    catalogue = get_json(f"{BASE}/translations/list/fa?localization=fa")
    entries = catalogue.get("translations", [])
    entries = [x for x in entries if x.get("language_iso_code") == "fa" and x.get("key")]
    if not entries:
        raise SystemExit("QuranEnc catalogue contains no Persian translations; refusing to package unverified text.")

    def fetch_sura(task):
        key, sura = task
        data = get_json(f"{BASE}/translation/sura/{key}/{sura}")
        rows = data.get("result")
        if not isinstance(rows, list) or not rows:
            raise RuntimeError(f"Unexpected QuranEnc response for {key}, sura {sura}")
        return key, sura, rows

    tasks = [(item["key"], sura) for item in entries for sura in range(1, 115)]
    collected = {item["key"]: {} for item in entries}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(fetch_sura, task) for task in tasks]
        for future in concurrent.futures.as_completed(futures):
            key, sura, rows = future.result()
            collected[key][str(sura)] = rows

    packed = {}
    for item in entries:
        key = item["key"]
        if len(collected[key]) != 114:
            raise SystemExit(f"Incomplete Persian resource: {key}")
        packed[key] = {
            "key": key,
            "title": item.get("title", key),
            "description": item.get("description", ""),
            "version": item.get("version", "unspecified"),
            "last_update": item.get("last_update"),
            "source": "QuranEnc.com",
            "surahs": collected[key],
        }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        "/* Persian translations listed by QuranEnc; source/version retained. */\\n"
        "window.QURAN_EXTRA_DATA = " + json.dumps({"translations": packed}, ensure_ascii=False, separators=(",", ":")) + ";\\n",
        encoding="utf-8"
    )
    print(f"Packaged {len(packed)} catalogue-listed Persian translations across 114 surahs.")
    for key, item in packed.items():
        print(f"{key}: {item['title']} (version {item['version']})")

if __name__ == "__main__":
    main()
