# Euan / Running — setup and maintenance

Prepared 2 November 2026 for GitHub user **YEY24**. The intended repository is `YEY24/running`; `https://yey24.github.io/running/` is the expected address, not a claim that deployment has completed.

## What has been prepared

- An English, responsive running journal with cream and teal styling, light/dark themes, totals, a 12-week chart, activity heatmap, filterable log, calendar, and interactive GPS map.
- Your dashboard starts empty. Upstream example runs are not presented as yours.
- A daily GitHub Actions workflow that reads Intervals.icu and deploys to GitHub Pages.
- The public fields are running dates/times, distance, moving time, derived pace, elevation, activity ID, and GPS route. Titles are replaced with “Run”; heart rate, descriptions, wellness, and contact data are excluded.
- Intervals credentials are read from GitHub Secrets. No downloaded activities are committed back to source control. The chosen public data are, necessarily, downloadable in the deployed site assets.

## 1. Create the repository

Open https://github.com/new while signed in as YEY24. Create **running**, choose **Public**, and initialize it with a README. Send the resulting repository link in this chat so the prepared code can be uploaded. If the GitHub connection only permits selected repositories, add `running` to that selection.

The public repository choice supports GitHub Free Pages. Pages from a private repository requires an eligible paid plan and does not by itself make the published website private.

## 2. Connect Apple Watch data

Recommended path:

**Apple Watch → Apple Health → HealthFit → Intervals.icu → GitHub Actions → GitHub Pages**

In HealthFit, grant access to workouts and workout routes, open its connected-platform/export settings, connect Intervals.icu, and enable automatic workout export. Exact labels can vary by HealthFit release. Export a few existing runs first, then historical runs as needed. Open those activities in Intervals.icu and confirm their distances and route maps before enabling the website import.

If HealthFit already sends your runs directly to Intervals.icu, this connection is already complete. No Apple password or direct HealthKit access from the website is needed.

Prefer **direct HealthFit → Intervals.icu**, rather than Strava → Intervals.icu. The official Intervals API may return only stub records for Strava-sourced activities; such records cannot supply the website with full metrics and GPS. The exporter reports skipped stubs. This limitation cannot be fixed by adding another Intervals API key.

Alternative routes supported by the upstream project:

- **HealthFit → Strava → upstream Strava importer:** requires a Strava API application, client ID, client secret, and OAuth refresh token. This is an alternative integration, not enabled in the prepared workflow.
- **HealthFit FIT/GPX/TCX exports → upstream file importers:** useful for local imports/backfills. Raw exports contain private data and should stay outside the public repository. The upstream Python tools require their full dependencies. The prepared daily exporter uses only Python's standard library.

Avoid enabling multiple website importers for the same runs unless you intentionally handle duplicates.

## 3. Add the two repository secrets

In Intervals.icu, open Settings and find Developer Settings / API access. Obtain your athlete ID and create an API key. Keep the API key private.

In **YEY24/running → Settings → Secrets and variables → Actions → New repository secret**, add:

| Secret name | Value |
| --- | --- |
| `INTERVALS_ICU_ATHLETE_ID` | Your Intervals.icu athlete ID |
| `INTERVALS_ICU_API_KEY` | Your Intervals.icu API key |

Enter the values directly on GitHub. Do not paste them into chat, source files, workflow YAML, screenshots, or command arguments. The website only issues GET requests; an Intervals API key may have broader account permissions, so treat it accordingly.

No Strava credentials, Apple credentials, personal GitHub token, Mapbox account, or map token are required for this setup. Deployment uses GitHub's automatic short-lived workflow identity. The map uses the upstream dashboard's CARTO fallback and retains attribution; external map services receive ordinary browser map requests.

## 4. Enable GitHub Pages and run the first sync

1. Open **repository Settings → Pages**.
2. Under **Build and deployment → Source**, select **GitHub Actions**.
3. Open **Actions → Sync and publish running dashboard → Run workflow** on the default branch.
4. Confirm the **build** and **deploy** jobs succeed. The deployment job returns the actual Pages URL.
5. Open the URL, compare several activity dates/distances with Intervals.icu, and confirm that route selections match the chosen runs.

The workflow handles `/running/` automatically and also supports an `owner.github.io` repository at the root. It supports either `main` or `master`; scheduled runs use the default branch. Pushes rebuild and deploy. Pull requests run checks without Intervals secrets or deployment.

Before secrets are configured, a manual/push run can publish the honest empty dashboard. A scheduled run without secrets fails instead of reporting a successful sync. A failed import never reaches deployment, preserving the previous live version.

## 5. Scheduled synchronization

The saved schedule is **05:17 UTC every day**: **06:17 CET in winter**, **07:17 CEST in summer**. GitHub may delay scheduled runs; this is not an exact delivery guarantee. In a public repository, GitHub may disable scheduled workflows after 60 days without repository activity. Re-enable the workflow in Actions if needed.

Each run fetches a full snapshot from the configured start date. This reflects activity edits and deletions, unlike an append-only history. Routes are fetched afresh to avoid retaining a removed route. No raw workout cache is restored. Large histories can take several minutes. The job allows 45 minutes, retries transient failures, and limits route-request frequency.

Optional repository **Variables** (not secrets):

| Variable | Default | Purpose |
| --- | --- | --- |
| `PUBLISH_ROUTES` | `true` | Set to `false` and run the workflow to remove GPS from the next deployment. |
| `SYNC_START_DATE` | `2000-01-01` | Restrict imported history; use ISO date format. |

Publishing no accessible runs is treated as an error, protecting a working history from an accidental empty response. If you intentionally remove every run, publish the clean empty source without credentials or explicitly adapt that guard. Previously downloaded copies and third-party caches cannot be recalled by redeployment.

## Architecture and customization

Based on `yihong0618/running_page`, inspected at commit `3bec7208d38f62562585514133f016f4814c6815` on 2 November 2026. The source retains the upstream MIT license.

| Location | Role |
| --- | --- |
| `src/main.tsx`, `src/App.tsx` | React entry, theme/locale providers, registered theme |
| `config.yml` | Public locale, theme preset and appearance configuration |
| `src/core/` | Shared types, activity loader, format helpers, theme and localization |
| `src/themes/euan/` | Your custom page and styling |
| `src/components/` | Reused heatmap, log, calendar, and route-map components |
| `src/static/activities.json` | Empty in source; generated during a sync/build |
| `scripts/sync_intervals.py` | Read-only API → sanitized running_page-compatible JSON |
| `.github/workflows/run_data_sync.yml` | One ordered sync/build/deploy workflow |
| `run_page/` | Retained upstream Python importers and analysis tools |

The upstream front end is React + TypeScript + Vite + Tailwind; Python imports produce a shared activity JSON dataset. The legacy importer also uses SQLite and original FIT/GPX/TCX files. Your exporter reads summary metrics and GPS streams directly, avoids raw-file downloads and geocoding, and supplies the same frontend data shape. That includes treadmill runs with metrics but no route.

The current upstream README describes some older behavior: its Intervals `--all` flag actually includes all sports (not “all history”), and the implementation defaults to a start date in 2015. The prepared exporter instead includes Run, TrailRun and VirtualRun only, with a documented start date. Current Vite dependencies also need newer Node than the README's broad “Node >=20”; use **Node 24** and **pnpm 8.9.0** for the supplied lockfile.

Change branding and wording in `src/themes/euan/index.tsx`, colors and spacing in `src/themes/euan/style.css`, and favicon in `public/images/euan.svg`. The active theme is English; changing the locale alone does not translate its custom headings. No unconfirmed race target or mileage goal has been published. The upstream Dashboard/Classic theme sources are retained but unregistered, so their sample SVG statistics and unrelated widgets are not bundled in your live site. Register them explicitly if you choose to use them later.

## Local preview

After Node 24 and pnpm 8.9.0 are available:

```sh
cd /path/to/euan-running
pnpm install --frozen-lockfile
pnpm dev
```

Open the printed local URL. A local preview starts empty. To test real imports locally, supply credentials through a secure environment/hidden input workflow; never commit the generated personal JSON. Prefer the GitHub Secrets path above for unattended sync.

```sh
python3 -m unittest discover -s scripts -p 'test_*.py'
pnpm typecheck
PATH_PREFIX=/running pnpm build
```

`pnpm typecheck` checks the deployed app and its dependencies. The separate upstream Classic theme has pre-existing TypeScript alias/type errors under its whole-repository configuration and is outside this check. Existing legacy formatting/lint scripts are retained but not required by the personal workflow.

## Troubleshooting

- **No repository is visible to the connector:** check which GitHub account is connected and whether the GitHub app has access to `running`.
- **HTTP 401:** replace the Intervals API key in GitHub Secrets; verify the athlete ID belongs to the key.
- **HTTP 403/404 or stub warnings:** check direct HealthFit uploads; Strava-only data can be unavailable through the API.
- **Metrics but no GPS:** check the original activity's route in HealthFit and Intervals.icu. A treadmill activity may correctly have no GPS.
- **Pages returns 404:** confirm Source is GitHub Actions, workflow deployment succeeded, and the URL includes `/running/`.
- **No recent update:** inspect the latest Actions run. The page displays the last successful import time, not a made-up “live” status.
- **Map cannot load:** use the displayed retry/error state; external map availability and WebGL support can affect it independently of the running metrics.

## Sources

- Project README and architecture: https://github.com/yihong0618/running_page and `docs/theme-system.md`.
- HealthFit's supported destinations: https://apps.apple.com/us/app/healthfit/id1202650514.
- Intervals API schema, including Strava stubs and `ActivityStream` data/data2: https://intervals.icu/api/v1/docs.
- GitHub Pages workflow requirements: https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages.
- Scheduled workflow behavior: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule.
