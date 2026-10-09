"""
Download OSM PBF extracts from Geofabrik for France's neighboring countries/regions.

Uses the same date (220101) as the existing france-220101.osm.pbf to ensure
temporal consistency. Downloads only border-relevant subregions for large
countries (Germany, Spain, Italy) and full extracts for small neighbors
(Belgium, Luxembourg, Switzerland, Monaco, Andorra).

Output: data/osm/<name>-220101.osm.pbf
"""

import os
import sys
import urllib.request

BASE_URL = "https://download.geofabrik.de/europe"
DATE_SUFFIX = "220101"
OUTPUT_DIR = os.path.join(
    os.path.dirname(__file__), os.pardir, "data", "osm"
)

# (display_name, url_path relative to BASE_URL)
DOWNLOADS = [
    # Full countries (small neighbors)
    ("belgium", f"belgium-{DATE_SUFFIX}.osm.pbf"),
    ("luxembourg", f"luxembourg-{DATE_SUFFIX}.osm.pbf"),
    ("switzerland", f"switzerland-{DATE_SUFFIX}.osm.pbf"),
    ("monaco", f"monaco-{DATE_SUFFIX}.osm.pbf"),
    ("andorra", f"andorra-{DATE_SUFFIX}.osm.pbf"),
    # Germany – border subregions only
    ("germany-baden-wuerttemberg", f"germany/baden-wuerttemberg-{DATE_SUFFIX}.osm.pbf"),
    ("germany-rheinland-pfalz", f"germany/rheinland-pfalz-{DATE_SUFFIX}.osm.pbf"),
    ("germany-saarland", f"germany/saarland-{DATE_SUFFIX}.osm.pbf"),
    # Spain – border subregions only
    ("spain-aragon", f"spain/aragon-{DATE_SUFFIX}.osm.pbf"),
    ("spain-cataluna", f"spain/cataluna-{DATE_SUFFIX}.osm.pbf"),
    ("spain-navarra", f"spain/navarra-{DATE_SUFFIX}.osm.pbf"),
    ("spain-pais-vasco", f"spain/pais-vasco-{DATE_SUFFIX}.osm.pbf"),
    # Italy – border subregion only
    ("italy-nord-ovest", f"italy/nord-ovest-{DATE_SUFFIX}.osm.pbf"),
]


def download_file(url, dest_path):
    """Download a file with progress reporting."""
    print(f"  Downloading {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as response:
        total = response.headers.get("Content-Length")
        total = int(total) if total else None
        downloaded = 0
        block_size = 1024 * 1024  # 1 MB

        with open(dest_path, "wb") as f:
            while True:
                chunk = response.read(block_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = downloaded * 100 / total
                    mb = downloaded / (1024 * 1024)
                    total_mb = total / (1024 * 1024)
                    print(f"\r  {mb:.0f}/{total_mb:.0f} MB ({pct:.0f}%)", end="", flush=True)

        if total:
            print()  # newline after progress


def main():
    out_dir = os.path.normpath(OUTPUT_DIR)
    os.makedirs(out_dir, exist_ok=True)
    print(f"Output directory: {out_dir}")
    print(f"Files to download: {len(DOWNLOADS)}\n")

    failed = []
    skipped = []
    downloaded = []

    for name, url_path in DOWNLOADS:
        filename = f"{name}-{DATE_SUFFIX}.osm.pbf"
        dest = os.path.join(out_dir, filename)
        url = f"{BASE_URL}/{url_path}"

        if os.path.exists(dest):
            size_mb = os.path.getsize(dest) / (1024 * 1024)
            print(f"[SKIP] {filename} already exists ({size_mb:.1f} MB)")
            skipped.append(name)
            continue

        print(f"[GET]  {filename}")
        try:
            download_file(url, dest)
            size_mb = os.path.getsize(dest) / (1024 * 1024)
            print(f"  -> Saved ({size_mb:.1f} MB)")
            downloaded.append(name)
        except Exception as e:
            print(f"  -> FAILED: {e}")
            # Remove partial file
            if os.path.exists(dest):
                os.remove(dest)
            failed.append((name, str(e)))

    print(f"\n{'='*60}")
    print(f"Downloaded: {len(downloaded)}")
    print(f"Skipped (already exist): {len(skipped)}")
    print(f"Failed: {len(failed)}")
    if failed:
        for name, err in failed:
            print(f"  - {name}: {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
