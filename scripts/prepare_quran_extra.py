#!/usr/bin/env python3
"""Package Persian QuranEnc resources for offline use, preserving source text verbatim."""
import concurrent.futures
import json
import pathlib
import urllib.request
import urllib.error

BASE = "https://quranenc.com/api/v1"
OUT = pathlib.Path("app/src/main/assets/quran-extra-data.js")
HEADERS = {"User-Agent": "QuranNoor/1.1 (offline resource packaging)"}

def get_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))

def norm(value):
    return str(value or "").replace("ي", "ی").replace("ى", "ی").replace("ك", "ک").replace("ة", "ه")

def choose(items, predicate, label):
    matches = [x for x in items if predicate(norm(x.get("title", "")), norm(x.get("key", "")))]
    if len(matches) != 1:
        names = [x.get("title", x.get("key", "?")) for x in matches]
        raise SystemExit(f"Expected exactly one {label}; found {len(matches)}: {names}")
    return matches[0]

def main():
    payload = get_json(f"{BASE}/translations/list/fa?localization=fa")
    items = payload.get("translations", [])
    persian = [x for x in items if x.get("language_iso_code") == "fa"]
    if not persian:
        raise SystemExit("QuranEnc returned no Persian resources")

    translation = choose(
        persian,
        lambda title, key: ("رواد" in title and "ترجمه" in title) or "persian_rwwad" in key,
        "Persian translation (Ruwad)"
    )
    brief_tafsir = choose(
        persian,
        lambda title, key: "مختصر" in title and "تفسیر" in title,
        "Persian brief tafsir"
    )
    saadi_tafsir = choose(
        persian,
        lambda title, key: "سعد" in title and "تفسیر" in title,
        "Persian Tafsir al-Saadi"
    )

    resources = [
        ("translation", translation),
        ("brief_tafsir", brief_tafsir),
        ("saadi_tafsir", saadi_tafsir),
    ]

    def fetch_sura(pair):
        resource_id, item, sura = pair
        key = item["key"]
        data = get_json(f"{BASE}/translation/sura/{key}/{sura}")
        rows = data.get("result")
        if not isinstance(rows, list) or not rows:
            raise RuntimeError(f"No rows for {key}, sura {sura}")
        return resource_id, sura, rows

    tasks = [(rid, item, sura) for rid, item in resources for sura in range(1, 115)]
    collected = {rid: {} for rid, _ in resources}
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(fetch_sura, task) for task in tasks]
        for future in concurrent.futures.as_completed(futures):
            rid, sura, rows = future.result()
            collected[rid][str(sura)] = rows

    packed = {}
    for rid, item in resources:
        if len(collected[rid]) != 114:
            raise SystemExit(f"Incomplete resource {item['key']}")
        packed[rid] = {
            "key": item["key"],
            "title": item.get("title", ""),
            "description": item.get("description", ""),
            "version": item.get("version", ""),
            "last_update": item.get("last_update"),
            "source": "QuranEnc.com",
            "surahs": collected[rid],
        }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        "/* QuranEnc Persian resources. Reproduced unchanged under QuranEnc Terms and Policies. */\n"
        "window.QURAN_EXTRA_DATA = " + json.dumps(packed, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8"
    )
    print("Packaged QuranEnc Persian translation and two tafsir resources for all 114 surahs.")
    for rid, item in resources:
        print(f"{rid}: {item.get('title')} (version {item.get('version')})")

if __name__ == "__main__":
    main()
