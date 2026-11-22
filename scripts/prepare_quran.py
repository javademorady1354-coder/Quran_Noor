#!/usr/bin/env python3
"""Fetch a pinned, attributed Quran dataset and package only reader fields."""
import json
import pathlib
import urllib.request

COMMIT = "37b4aa3351c71bd7bfb14dc2dd577656bcafb41b"
URL = f"https://raw.githubusercontent.com/mjmirza/quran-dataset/{COMMIT}/data/quran.json"
OUT = pathlib.Path("app/src/main/assets/quran-data.js")

def main():
    request = urllib.request.Request(URL, headers={"User-Agent": "QuranNoorBuild/1.0"})
    with urllib.request.urlopen(request, timeout=90) as response:
        dataset = json.loads(response.read().decode("utf-8"))

    if len(dataset.get("surahs", [])) != 114:
        raise SystemExit("Dataset validation failed: expected 114 surahs")

    out_surahs = []
    ayah_count = 0
    pages = set()
    for surah in dataset["surahs"]:
        out_ayahs = []
        for ayah in surah["ayahs"]:
            page = int(ayah["page"])
            pages.add(page)
            ayah_count += 1
            out_ayahs.append({
                "n": int(ayah["number"]),
                "t": ayah["text"],  # copied verbatim; do not normalize Quran text
                "p": page,
                "j": int(ayah["juz"]),
                "h": int(ayah["hizb"]),
                "r": int(ayah["ruku"]),
                "s": ayah.get("sajda")
            })
        out_surahs.append({
            "n": int(surah["number"]),
            "a": surah["name_arabic"],
            "e": surah.get("name_english", ""),
            "tr": surah.get("name_transliteration", ""),
            "c": len(out_ayahs),
            "v": out_ayahs
        })

    if ayah_count != 6236 or pages != set(range(1, 605)):
        raise SystemExit(f"Dataset validation failed: {ayah_count} ayahs, {len(pages)} pages")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        "/* Tanzil Uthmani text, CC BY 3.0; source and notice in DATA_SOURCES.md */\n"
        "window.QURAN_DATA = " + json.dumps({"surahs": out_surahs}, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8"
    )
    print(f"Packaged {ayah_count} ayahs across 114 surahs and 604 Madinah pages.")

if __name__ == "__main__":
    main()
