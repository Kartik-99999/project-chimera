# User browser sessions

Clean sessions — a fresh browser with no stored state — remain the
default for every Chimera run. Some sites refuse automation from
clean sessions (bot gates, challenges). For those, selected
workflows may run on a **persistent user profile**: a Chromium
profile directory whose cookies, storage, and challenge
clearances persist across runs.

## Creating a profile

```sh
python -m workbench.sessions login <name> --url https://site.example/
python -m workbench.sessions list
python -m workbench.sessions remove <name>
```

`login` opens the site in a **visible** browser window on a new
profile and waits. You log in — and clear any human challenge —
in that window, then press Enter here. Chimera never sees, asks
for, stores, or logs credentials; it only reuses the cookies your
own login left behind.

Profiles live outside the repository at `~/.chimera/profiles/`
(`CHIMERA_PROFILES_DIR` overrides this), created owner-only
(`0700`). A profile directory holds **live session cookies**:
treat it like credentials — never commit it, copy it to shared
machines, or paste its contents anywhere. `remove` deletes a
profile; also log out on the site itself to rotate server-side
sessions.

## Running with a profile

Only workflows that declare `sessions=("clean", "user")` accept
profiles; every other workflow rejects the `profile` parameter,
and Studio workflows always run clean. Pass the profile at
submit time (API `profile` field, or the Workspace form's
profile input on supporting workflows). A missing profile fails
fast with the login command — the run is never started.

```sh
# Example: Stack Overflow on your logged-in profile
curl -X POST localhost:PORT/api/workbench/executions \
  -H 'Content-Type: application/json' \
  -d '{"workflow_id":"stackoverflow-search","driver":"chimera",
       "params":{"query":"pytest fixture"},"profile":"me"}'
```

## What a profile run may do

The per-workflow **observer policy** is the action allowlist: each
workflow declares exactly which navigations, fills, and clicks
are permitted, and everything else is denied and recorded. Both
pilot workflows are read-only inside the session (navigate and
read only; empty fill/click targets). Amazon additionally
refuses cart, checkout, account, and login paths at three
layers: the driver's URL guard, the observer policy, and the
verifier's page expectations. A workflow that needs
state-changing actions must declare them explicitly in its
policy — silence means forbidden.

## Evidence labeling

Every execution record carries `session`: `clean`, or
`user:<profile>`. The run view and history show it, the API and
CSV export include it, and history supports filtering and
faceting by it (`session` is a filter column). User-state
evidence is therefore always separable from clean-session
evidence — never silently mixed. When a clean run meets a bot
gate, the verdict is `verified-failure` with a diagnosed
"bot gate detected" detail (never zero-results), and the error
points back at the login command above.
