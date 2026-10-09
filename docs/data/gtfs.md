# GTFS archive and offline inventory

- **Source:** producer URLs in [the manifest](../../config/sources.yaml);
  dataset history from the configured transport.data.gouv.fr API.
- **Vintage:** the configured acquisition snapshot. Service dates can differ.
- **Local path:** `data/raw/gtfs/{vintage}/{dataset_id}/{resource_id}.zip`.
- **Format:** original ZIP, not unpacked or changed in place.
- **CRS:** GTFS stop coordinates are WGS84 longitude/latitude in degrees.
  The inventory bounding box is `(west, south, east, north)` in degrees,
  not a processing geometry; converted processing tables use EPSG:3035.
- **Reference:** [GTFS Schedule reference](https://gtfs.org/documentation/schedule/reference/),
  revised 27 April 2026. This check is acquisition triage for sections 5.1/5.6,
  not a full GTFS specification validator.

## Fields read by the offline check

| File | Fields | Meaning |
|---|---|---|
| `agency.txt` | `agency_name` | Distinct agency names |
| `stops.txt` | `stop_lon`, `stop_lat` | Stop extent, in WGS84 degrees; blank coordinates allowed |
| `trips.txt` | `service_id` | Services used by trips; row count gives trip count |
| `calendar.txt` | `service_id`, `monday` through `sunday`, `start_date`, `end_date` | Regular service, date strings `YYYYMMDD`, weekday flags `0`/`1` |
| `calendar_dates.txt` | `service_id`, `date`, `exception_type` | Service additions (`1`) and removals (`2`), date strings `YYYYMMDD` |

The checker also counts rows in `stops.txt`. It checks ZIP integrity (including
CRCs) and the presence of `agency.txt`, `stops.txt`, `routes.txt`, `trips.txt`,
`stop_times.txt`, and at least one of `calendar.txt` or `calendar_dates.txt`.
It reports the presence of `locations.geojson` and `booking_rules.txt` as
flex/on-demand indicators; their contents are not validated.

## Archive history

Dataset detail responses contain a top-level `history` array. Each item has
`resource_id` and a `payload` containing `permanent_url` and
`download_datetime` (an ISO timestamp with timezone). Select the newest
permanent URL for the requested resource only. The latest archive must be
less than the configured 60 days old and pass the local GTFS check before it
is published. Do not search older archives or sibling URLs.

The manifest retains the primary URL and records `archive_url`,
`archive_date`, and `archive_resource_id` separately. A successful archive
has a recorded local SHA-256, but is not independently checksum-verified.

## Inventory and quirks

`--check-gtfs` has no network access and does not modify the manifest or raw
files. It updates [the inventory](../../config/gtfs_inventory.csv), retaining
every configured resource, including missing files and excluded resources.
`gtfs_present_files` and `gtfs_missing_files` record table presence; other
`gtfs_*` fields record ZIP/GTFS status, service bounds, expiry, counts, agencies,
bounding box, check date and explicit errors. Lists and the bounding box
are JSON cells.

Effective first/last service dates use only service ids referenced by trips,
weekday flags, additions and removals, not `feed_info` publication dates.
Expiry means last effective service date precedes the check date. A date
equal to the check date is not expired. Feeds with no effective service
dates are flagged rather than assigned invented dates.

ZIP members can be under a subfolder; ambiguous duplicate table names are
flagged. CSV metadata tables are streamed to temporary scratch space and
read with DuckDB, not pandas. `stop_times.txt` is CRC-checked but not loaded
into memory. Parse errors are reported without terminating the whole check.
A `.proto` or an HTML page renamed `.zip` is not accepted as a GTFS ZIP.

A failed resource can be marked `excluded_reason: broken resource, dataset
covered by {resource_id}` only after checking a downloaded GTFS sibling of
the same dataset. This does not delete either resource. An expired sibling
remains structurally valid but is separately flagged by the offline check.
Exclusions are rechecked on acquisition reruns; losing the covering local
feed makes the resource eligible for retry rather than silently losing coverage.
