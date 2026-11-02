# EMC² and Île-de-France EGT inventory

## Status

The expected source directories are not present in this checkout:

- `data/raw/emc2/` — absent
- `data/raw/egt/` — absent

The current `data/raw/` directory listing contains neither directory nor
any EMC²/EGT-named folder. The raw-data root is ignored by Git
(`.gitignore`, line 1), so source files should remain local and must not
be committed.

## Inventory and blockers

| Survey | Files / formats | Tables / dictionaries | Households | Persons | Persons with a described day | Trips |
|---|---|---|---:|---:|---:|---:|
| EMC² | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable |
| Île-de-France EGT | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable |

Interview dates, described-day periods, sector-by-period counts, survey
design, weights, zoning, commune codes, and the requested variable
availability/codings cannot be verified without the source files and
their documentation. No survey-to-step-11 mapping is proposed in the
absence of those materials.

To unblock the inventory, place the local source files and
documentation under `data/raw/emc2/` and `data/raw/egt/`, or provide
their actual locations. No downloads or changes to `data/raw/` were
made.
