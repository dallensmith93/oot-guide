# Validation report

Research and validation date: **November 23, 2026**. Target: native Nintendo Switch 2 Ocarina of Time remake, **version 1.1.1**, the latest update listed on Nintendo's support page at research time.

## Delivered content and integrity checks

`python scripts/validate.py` regenerates the committed browser data and Markdown, then checks:

- Exactly 25 chronological episodes containing all 41 original route parts once, in order, and 370 unique objective IDs. Existing route links and saved objective IDs remain valid.
- Exactly 100 distinct Gold Skulltula records, 36 distinct Heart Piece records and eight boss Heart Containers.
- Correct running totals after every section; the final pre-boss audit reaches 100/36/8 and **20 hearts**.
- Thirteen songs including the player-composed Scarecrow Song; five bottles; ten dungeon maps and ten compasses.
- Presence of all six Great Fairy visits' rewards, including the initial magic meter and Din's Fire as separate inventory flags.
- Every objective belongs to one existing route section; all source references resolve to the local registry of 150 sources.
- All shared grotto reward references resolve without adding duplicate core reward IDs.
- 162 comparisons between named prerequisites and their scheduled acquisition sections, plus explicit child-crater, Silver Gauntlets and crater-bean ordering assertions.
- Local asset paths, root Netlify configuration publishing `site`, UTF-8 source data and absence of a ZIP.

These checks passed. The prerequisite assertions cover the named items in the script; they do not simulate every room, key expenditure, timer, enemy spawn or console save state. A numeric count does not prove every supplied location is correct.

`node --check site/app.js` and `node --check site/data.js` passed. There is no configured production build or package installation to run. `site/data.js`, Markdown exports and the full printable HTML are generated locally and committed for direct publishing.

## Browser and HTTP checks

The development-only `scripts/browser_test.py` uses Python Playwright with the installed Chrome browser, serving **the actual configured `site` directory** through a temporary local HTTP server. It does not test mock guide data.

The interaction suite checks:

- All ten main views and all 41 route sections render, including direct fragment links.
- HTML, JavaScript, stylesheet and full printable guide return HTTP 200.
- Shared checkboxes agree between route and tracker views and survive reload.
- Search, region, age, type, completion and hide-completed controls change results.
- Last-section resume, first-incomplete shortcut and previous/next navigation work.
- JSON export/import round-trips; malformed JSON, wrong schemas/game IDs, invalid ID arrays and oversize imports are rejected without replacing valid progress; unknown IDs are retained safely.
- Reset cancellation preserves progress and confirmed reset clears it.
- Phone and desktop widths have no horizontal overflow; mobile navigation opens and closes.
- Keyboard access, focus behavior and theme persistence work.
- Puzzle details expand for printing and restore their state afterward. Route and checklist PDFs are generated for inspection.
- No browser console errors or uncaught page errors occur during the exercised flows.

The suite passed all 18 reported check groups with no skipped groups, including all 25 episode pages, exact assigned objective coverage without duplicate checkboxes, and previous/next episode navigation. Browser output and visual artifacts are in ignored `test-results/`; they are QA artifacts, not runtime dependencies. Desktop and phone screenshots were visually inspected. PDF creation and print-state behavior were tested; PDF text extraction and printer hardware were not tested. Automated layout/focus checks are not a full assistive-technology audit.

## Content limitations and effect on the 100% claim

This is a substantial remake-specific route and working companion, **not a certified exhaustive completion reference**. No console playthrough or frame-by-frame gameplay audit was performed. The exact unresolved gaps are exposed in the website and affected records:

1. **All-chest manifest:** the route documents maps, compasses, required chests and source-described side-chest sweeps, but a complete independent count and identity list for every remake dungeon chest remains unverified. The sweep checkboxes cannot prove every chest was opened.
2. **All 84 Hall statue identities:** the route identifies commonly missed enemies, describes Hall access, lists the documented individual rematches and three named gauntlets, and explains their trophies. A verified individual list of all 84 enemy variants remains missing. The aggregate statue audit is a self-report, not an independently validated 84-entry bestiary.
3. **Fairy Thoughts:** fifteen source-listed locations are included. Another community map reports nineteen, so the Thought collection is not established as exhaustive. These checks do not inflate core progress.
4. **Grotto catalogue:** 36 optional records follow a declared counting convention. Other sources count 37 by including Dampé's grave. `grotto-17`, `grotto-25`, `grotto-29` and `grotto-36` retain explicit uncertainty; the Goron sign puzzle's exact sequence is not verified. One catalogue's prose and table also disagree about how many entries it has independently confirmed.
5. **Collectible source conflicts:** `gs-008`, `gs-023`, `gs-051`, `gs-071`, `gs-077`, `gs-084`, `gs-085`, `hp-009`, `hp-021` and `hp-033` have location, access, fee or threshold notes. Most have conservative collection guidance; `gs-084` retains a genuine Well-room conflict. A unique ID represents one token regardless of the alternative descriptions.
6. **Minigames and timed trades:** published remake descriptions conflict on the Lost Woods shooting setup, some fishing/archery thresholds and delivery timer values. The route uses conservative targets and direct travel, but those disputed details were not verified on a console.
7. **Controls:** Nintendo's material establishes manual jump, dash, camera and microphone functionality. A complete official web button chart was not located; physical-button names are attributed to remake control-card reporting and recorded gameplay, with the in-game Controls screen authoritative.
8. **Missables and saving:** the reported Malon/Epona song bug is explicitly labeled a player report, not a universal official missable. Exact post-credits save-state behavior remains unverified; the guide advises a pre-finale manual save and makes no unverified postgame-world or autosave shortcut promise.
9. **Connected extras:** the website does not replicate the full official ZELDA NOTES percentage formula, all Gossip Quests or all app medals. These require the optional connected service and are separated from base-game progress. Future 2027 amiibo masks are outside the launch base-game checklist. No unsupported DLC or additional difficulty mode is invented.

Because of these gaps, marking every website objective cannot establish that every possible base-game chest, statue, Thought, scarecrow event or optional dialogue has been independently documented. This limitation is distinct from the checked numeric collectible totals and the passing website tests.

## Deployment and practical estimate

The exact publish directory was tested locally over HTTP. Netlify configuration and Git-import instructions were checked against current official documentation. **No GitHub push, external repository change or live Netlify deployment was performed.** Hosting/account credentials were not used and no ZIP was created.

Budget **40–60 hours** for a normal player following the route with modest minigame retries and Hall practice, or **60–80 hours** for a first-time player. This is an editorial estimate, not a timed benchmark or expert speedrun prediction. Optional app master medals and extensive record chasing can add substantially more time.
