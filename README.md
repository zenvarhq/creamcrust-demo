# CreamCrust café design demo

An independent, unofficial website and interactive menu demonstration by ZENVAR. This is not CreamCrust’s official website and has not been approved by the business.

Photographs are licensed category illustrations, not CreamCrust products or premises. Menu prices, availability and business details come from public observations and remain unverified. See [asset credits and rights](ASSET_RIGHTS.md) and `content/assets-manifest.json`.

Serve this folder with `python -m http.server 8000`, then open http://localhost:8000. The six routes are `/`, `/story/`, `/gallery/`, `/visit/`, `/menu/` and `/studio/`. No server-side build or backend is required. The GitHub Actions workflow publishes an allowlisted static artifact from `main` to GitHub Pages.

Menu Studio saves only in the current browser. It does not update the repository, other visitors or a shared database. There is no checkout, customer-data collection or analytics. Search-engine indexing is discouraged with `noindex,nofollow`; this is not access control.

The public demonstration was authorized by the project founder on 25 October 2026. No business contact is authorized from 25 October through 23 November 2026. Telephone actions remain disabled. Public demo permission does not imply business approval or production readiness.

The current `main` branch in this repository is the source of truth. Preview: https://zenvarhq.github.io/creamcrust-demo/. Older local archives are references only. Internal research and backups are excluded from deployment.

For reproducible Chromium checks, install `requirements-dev.txt`, run `python -m playwright install chromium`, then `python tests/browser_test.py --url http://localhost:8000 --output .qa/browser` and `python tests/owner_audit.py --url http://localhost:8000 --output .qa/visual --require-improvements`. Tests exit nonzero on failed checks. Menu Studio imports/exports JSON locally; reset affects catalogue overrides only. Site data, favourites and preferences are scoped to the browser profile and origin. No shared persistent CMS is implemented.
