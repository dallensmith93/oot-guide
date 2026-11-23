# The Hero's Ledger

A responsive Ocarina of Time playthrough companion targeting the **native Nintendo Switch 2 remake**, released November 5, 2026. Research snapshot: **November 23, 2026**, targeting Nintendo's latest listed **version 1.1.1**.

The site presents a 25-episode chronological playthrough, with the 41 detailed route parts retained inside those episodes. It includes dungeon notes, shared collectible and inventory checklists, expected route totals, search/filter tools, local progress, JSON transfer, light/dark themes and print styling. Remake research conflicts are shown alongside affected records and in the validation report; this project's checklist is not an official game completion percentage.

Edit `content/episodes.json` to change episode titles and boundaries. Every route part must appear once, in order. The generator derives episode-ending totals; `guide/episodes.md` provides the episode guide. Existing route and objective IDs remain unchanged, preserving old deep links and saved checkmarks. Episodes are natural playthrough divisions, not promises of equal recording length.

## Local preview

With Python installed, run from this directory:

```sh
python -m http.server 8080 --directory site
```

Open **http://localhost:8080**. The exact same `site` directory is configured for Netlify. The production site requires no Python, npm, backend, keys, CDN or third-party service.

## GitHub and Netlify

Push this project's files to your GitHub repository, then import that repository into Netlify. Root `netlify.toml` selects **`site`** as the publish directory. Leave the build command empty. Future pushes to the connected branch deploy automatically. See [DEPLOY-NETLIFY.md](DEPLOY-NETLIFY.md) for the checked interface steps and troubleshooting. No repository or hosting account was modified during preparation. No ZIP is needed or supplied.

## Repository structure

```text
content/                 Curated source JSON: route, collectibles, extras, sources
site/index.html          Accessible static shell
site/styles.css          Responsive design, themes and print styles
site/app.js              Navigation, shared progress, search and import/export
site/data.js             Committed data derived from content JSON
guide/                   Markdown walkthrough and checklist exports
scripts/generate.py      Derives data.js and Markdown from the same records
scripts/validate.py      Data and deployment integrity checks
scripts/browser_test.py  Optional Playwright interaction checks
netlify.toml             Publish directory and response headers
validation-report.md     Actual checks and content limitations
```

## Editing and validation

Edit the relevant `content/*.json` file, then run:

```sh
python scripts/generate.py
python scripts/validate.py
```

Commit the updated source JSON, generated `site/data.js`, and Markdown exports together. Netlify publishes the committed output directly without a generation step. Do not edit the derived exports separately.

Section IDs and objective IDs are persistent identities. Moving an existing objective to another section does not change its ID. Never reuse an old ID for a different reward. Sources are linked by ID. `scripts/generate.py` maps collectible stage labels to numbered sections and derives category totals and hearts. Any exceptional placement is explicit in that script. Optional activities have `optional: true` and do not inflate core progress.

`python scripts/browser_test.py` requires the optional Python Playwright package plus a compatible installed browser; it is development-only and is not required for preview or hosting. See its source for browser executable selection. No production dependencies or lockfile are needed because there is no JavaScript build or package installation.

## Progress and privacy

Progress is stored in localStorage in this browser for this site address. There is no account or server synchronization and the website cannot read your Nintendo save. Export JSON before clearing data, changing browser or moving to another domain. Import it at the destination. A localhost preview and the Netlify URL have different storage.

Exports use schema version 1 and game ID `oot-switch2-remake`. Imports validate the format before replacement; invalid input leaves current progress unchanged. Unknown historical objective IDs are preserved for future compatibility but do not count toward current totals. Shared objectives use one ID across every view. Reset requires confirmation.

## Reading offline or printing

The Markdown exports in `guide/` contain the route, compact playthrough list, master collectibles and warnings/cleanup. In the website, use Print on the desired route or tracker view. Source links substantiate instructions; they are not runtime dependencies. All art and layout are original CSS and text.

## Completion scope

The source records contain 100 distinct Gold Skulltulas, 36 Pieces of Heart and eight boss Heart Containers. The route covers story, inventory and remake activities using the cited sources. It has not been tested by playing a console save. See the site's Sources view and [validation-report.md](validation-report.md) for unresolved location conflicts, incomplete exhaustive chest/statue/Thought evidence and the resulting limits on any claim of total completion.
