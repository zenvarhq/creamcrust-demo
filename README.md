# CreamCrust café design demo

An independent, unofficial website and interactive menu demonstration by ZENVAR. This is not CreamCrust’s official website and has not been approved by the business.

Photographs are licensed category illustrations, not CreamCrust products or premises. Menu prices, availability and business details come from public observations and remain unverified. See [asset credits and rights](ASSET_RIGHTS.md) and `content/assets-manifest.json`.

Serve this folder with `python -m http.server 8000`, then open http://localhost:8000. The six routes are `/`, `/story/`, `/gallery/`, `/visit/`, `/menu/` and `/studio/`. No server-side build or backend is required. GitHub Pages can serve the main branch root with `.nojekyll`.

Menu Studio saves only in the current browser. It does not update the repository, other visitors or a shared database. There is no checkout, customer-data collection or analytics. Search-engine indexing is discouraged with `noindex,nofollow`; this is not access control.

The public demonstration was authorized by the project founder on 25 October 2026. No business contact is authorized from 25 October through 23 November 2026. Telephone actions remain disabled. Public demo permission does not imply business approval or production readiness.

This repository contains the reviewed static publishing snapshot. Local development source remains in `CAFE/prototype`; the local `prepare_github_publish.py` script copies only approved website files. Internal research, backups and QA recordings are excluded.
