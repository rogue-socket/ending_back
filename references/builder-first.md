# Builder-first path

The 10-loop spec. Loaded only when `progress.json → learner.orientation = builder_first`.

**Premise.** Build a working backend service in Loop 1. Break it on purpose in every subsequent loop. Foundations get filled in *as the service breaks*, not before. The learner ends Loop 10 with a service that has been through the same failure modes as a real production system, in miniature.

**Mandate from project setup:** these are *real, runnable, fun* code projects — not placeholders. The learner should leave each loop with code that actually works, that they can show off, and that they understand because they wrote it.

---

## How the loops fit together

Each loop builds on the previous one. The same service grows across all 10 loops:

```
Loop 1: bare CRUD (in-memory)              ← starts here
Loop 2: persistence + concurrency break    ← Postgres + the in-memory race
Loop 3: migrations + schema evolution      ← change the schema while running
Loop 4: auth                               ← sessions or JWT
Loop 5: async work via a queue             ← background jobs, at-least-once
Loop 6: caching + stampede                 ← Redis, hot key
Loop 7: containerize + deploy              ← Docker, deploy to a real cloud
Loop 8: real-time + scale out              ← WebSockets, two instances
Loop 9: observability + planted bug        ← OTel, metrics, traces, debug from telemetry
Loop 10: load test + capacity + postmortem ← break it under load, write the RCA
```

The product is a "links" service — users save URLs with titles, optionally share lists, get notifications, see live updates. It's small enough to fit in 10 loops and rich enough to surface every interesting backend problem. The learner names it whatever they want; the code is theirs.

---

## Per-loop structure

Every loop has the same five files in `~/backend-dev/projects/loop-N-<slug>/`:

| File | Purpose |
|---|---|
| `README.md` | What this loop adds, how to run it |
| `BREAK.md` | The intentional failure mode this loop teaches — what to break, how to break it, what to observe |
| `WIN.md` | The success criteria — what "loop done" looks like |
| `NOTES.md` | The learner's own notes, edited as they go |
| `quickpass.json` | 3 quiz questions for `/loop quickpass` — pass = mark loop done without running it |

Plus the loop's source code, in the learner's chosen language.

`quickpass.json` shape:
```json
{
  "loop": 1,
  "questions": [
    {
      "q": "An HTTP handler reads from a shared Go map without a mutex while another goroutine writes. What's the failure mode and what does Go's race detector show?",
      "a_outline": "Concurrent map read+write is a data race in Go; the runtime panics ('fatal error: concurrent map read and map write') or silently corrupts. `go test -race` flags it as 'WARNING: DATA RACE'. Fix: sync.Mutex or sync.Map.",
      "weight": 1
    },
    { "q": "...", "a_outline": "...", "weight": 1 },
    { "q": "...", "a_outline": "...", "weight": 1 }
  ],
  "pass_threshold": 2
}
```

Pass = 2 of 3 → loop marked `done` in `progress.json → loops.entries[]`. Miss → run the loop.

---

## /loop slash commands

| Command | Behavior |
|---|---|
| `/loop list` | Print all 10 loops with current status from `progress.json` |
| `/loop [N]` | Jump to loop N. If prereqs are missing, warn the learner; honor override |
| `/loop skip` | Mark current loop `skipped` after a 30-second summary of what they're skipping |
| `/loop quickpass` | Run the loop's `quickpass.json`. Pass → mark `done`. Miss → run the loop |
| `/loop reset N` | Wipe loop N's project dir and start fresh (asks for confirmation) |

---

## The 10 loops

### Loop 1 — Bare CRUD

**Tier mapping:** T0 (HTTP), T1 (REST design), T3 (concurrency, peripherally)
**Time:** 90-120 min
**Theme:** *feel HTTP without framework magic.*

**Build.** A single resource (`/links`) supporting all five verbs (GET list, GET one, POST, PATCH, DELETE) backed by an in-memory map. No framework, no DB, no auth. Just `net/http` (Go), FastAPI's bare routing (Python), or equivalent in their language. JSON encode/decode by hand. Status codes by hand.

**WIN criteria:**
- All five endpoints work as specified
- 404 on unknown resource, 400 on malformed body, 405 on wrong verb, 415 on wrong content type
- Has at least 3 tests (happy path, 404, 400)
- The whole thing fits in <200 lines

**Testing starts here, not later.** Before calling Loop 1 complete, write the happy-path test
and both error-path tests. A learner who asks whether to test now should hear: *yes — these
three tests are part of learning the HTTP contract, not polish for a later loop.*

**BREAK.** Run two concurrent POSTs to the in-memory map. In Go, `go test -race` catches it; in Python with the GIL, the failure is more subtle (lost writes, not a panic). Show the race. Fix with a mutex. *Don't* skip ahead to "use a real DB" — that's Loop 2's job.

**What the learner internalizes:**
- HTTP requests and responses are just bytes; frameworks are conveniences, not magic
- Concurrent access to shared state is a problem the moment you have two requests in flight
- Tests are fast and cheap; write them now

**Foundations to fill in mid-loop (per `learner.level`):**
- *Foundations:* the request/response cycle, methods vs status codes, JSON content types
- *Working:* none usually — they know this; if they don't, that's the surface gap to flag
- *Senior:* probably already knows; quick pass

---

### Loop 2 — Persistence + the concurrency break

**Tier mapping:** T2 (Postgres, indexes, transactions), T3 (concurrency)
**Time:** 120-150 min
**Theme:** *the in-memory map was a lie.*

**Build.** Replace the in-memory map with Postgres. Add `docker-compose.yml` running Postgres 16. Connection pool. Schema with appropriate types (`id BIGSERIAL`, `url TEXT NOT NULL`, `created_at TIMESTAMPTZ DEFAULT now()`). Index on whatever the most common query touches. Migrate the in-memory tests to integration tests against a real DB.

**WIN criteria:**
- Data survives a service restart
- Connection pool sized sensibly (~10 connections for a single-process dev service); explain the number
- A single non-trivial query (filter + sort + paginate); query plan reviewed via `EXPLAIN ANALYZE`
- Integration tests run against a real (containerized) Postgres

**BREAK 1 — connection pool exhaustion.** Set the pool to 2. Run 10 concurrent slow queries. New requests time out at the pool, not at the DB. Observe.

**BREAK 2 — N+1.** Add a `tags` resource related to links. Implement a list endpoint that loads links and their tags naively (one query per link). Watch the query log explode. Fix with a JOIN or batch fetch.

**What the learner internalizes:**
- Connection pools are an explicit capacity decision, not a default
- The DB is a shared resource with limits; the application sees those limits as latency
- N+1 is structurally easy to write and ruinously easy to ship

---

### Loop 3 — Migrations + schema evolution

**Tier mapping:** T2.5 (migrations)
**Time:** 90-120 min
**Theme:** *the schema you wrote in Loop 2 was wrong; fix it without downtime.*

**Build.** Use `golang-migrate`, `alembic`, or `flyway` (whichever fits the language). Add a NOT NULL column to the populated `links` table. Do it the wrong way first (`ALTER TABLE ... ADD COLUMN ... NOT NULL DEFAULT ...` on a populated table = ACCESS EXCLUSIVE lock). Watch parallel writes block. Then do it the expand/contract way: nullable column → backfill in batches → add constraint → done.

**WIN criteria:**
- Migration committed, reversible (or with a documented forward-fix if not)
- Zero downtime measured by a parallel-running insert script
- Old code path (the one that didn't know about the new column) coexists with the new for at least one deploy

**BREAK.** Try to add an index without `CONCURRENTLY` on a populated table. Watch the lock. Cancel. Add `CONCURRENTLY` and try again.

**What the learner internalizes:**
- DDL takes locks; "free, instant" DDL is a Postgres marketing illusion. Read the manual on lock levels per statement
- Online migrations are a discipline (expand → backfill → contract), not a feature
- The hardest part of a migration is "the old code is still running"

---

### Loop 4 — Auth

**Tier mapping:** T1.7-1.9 (sessions, JWT, OAuth), T8 (security)
**Time:** 120-180 min
**Theme:** *shipping anything to "real users" means knowing who they are.*

**Build.** Pick one of:
- **Sessions** — server-side session store in Postgres or Redis, secure cookies (HttpOnly, Secure, SameSite=Lax), session rotation on login
- **JWT** — short-lived access tokens + refresh token rotation, RS256 signing, JWKS endpoint
- **OAuth** — authorization code + PKCE flow against a real provider (Auth0 dev tier, Keycloak self-hosted)

Foundations / Working learners: pick sessions (the simpler, safer default for first-party web). Senior learners: pick whatever matches their stated project.

Endpoints: `POST /auth/signup`, `POST /auth/login`, `GET /auth/me`, `POST /auth/logout`. Plus password hashing — bcrypt or argon2id, never plain.

**WIN criteria:**
- All endpoints work, with appropriate status codes
- Cookie / token flags correct (verify with browser devtools or curl)
- Logout actually invalidates (server-side for sessions, refresh-token revocation list for JWT)
- Test cases: wrong password, expired token, replay attack, CSRF attempt on a state-changing route

**BREAK 1 — algorithm confusion (JWT only).** Sign with HS256, accept RS256 in verification — attacker uses the public key as the HMAC secret. Reproduce in a test. Fix by pinning the algorithm.
**BREAK 2 — CSRF.** State-changing route without SameSite cookie or CSRF token; show the exploit page (locally). Fix with SameSite=Lax + double-submit token.
**BREAK 3 — token logging.** Find tokens in your own access logs. Fix log scrubbing.

**What the learner internalizes:**
- Auth correctness is binary; "almost right" gets you on the front page of TechCrunch
- Cookie flags and CORS are not optional knobs
- Logging tokens is an own-goal that happens by accident in every codebase

---

### Loop 5 — Async work via a queue

**Tier mapping:** T3.6-3.9 (queues, delivery semantics, retries, DLQs)
**Time:** 120-180 min
**Theme:** *some things shouldn't happen on the request path.*

**Build.** Add a "send notification email" feature that runs out-of-band. Use Redis Streams (simple, single-binary), RabbitMQ, or SQS (LocalStack for local dev). Producer enqueues; worker process consumes. At-least-once semantics. Idempotent consumer (dedup via processed-IDs set with TTL).

**WIN criteria:**
- Worker is a separate process / container
- Acknowledgment happens *after* the work, not before
- Crash mid-processing → message redelivered → no duplicate side effect (idempotent)
- Dead-letter queue for poison messages (max 5 redelivery attempts → DLQ + alert)
- Queue depth + DLQ depth metrics exposed

**BREAK 1 — ack-before-work.** Worker acks immediately, then crashes mid-send. Email never sent. Reproduce. Fix by acking after success.
**BREAK 2 — non-idempotent consumer.** Worker processes the same message twice (because the broker doesn't actually guarantee exactly-once even when it claims to). Two emails sent. Fix with idempotency.
**BREAK 3 — poison message.** Send a message that always crashes the worker. Watch it loop forever (or block the queue, depending on the broker). Add max-redelivery + DLQ.

**What the learner internalizes:**
- Exactly-once delivery is a marketing term; at-least-once + idempotent consumer is the engineering reality
- Acknowledgment timing is part of the contract
- DLQs without alarms are a graveyard

---

### Loop 6 — Caching + stampede

**Tier mapping:** T4 (entire)
**Time:** 90 min
**Theme:** *speed and cost; cache invalidation is hard for a reason.*

**Build.** Add a Redis cache to a hot read endpoint (e.g., "popular links of the day"). Cache-aside pattern. Reasonable TTL (60s).

**WIN criteria:**
- Cache hit ratio measurable via metrics
- Invalidation on write (or version-bump key strategy if invalidation is hard)
- Single-flight / request coalescing for the hot key
- Negative caching for not-found cases (so a missing key doesn't pound the DB)

**BREAK 1 — the stampede.** Disable single-flight. Set TTL to 10s. Run 1000 concurrent requests. At expiry, the DB gets hammered. Reproduce. Add single-flight; observe the recovery.
**BREAK 2 — staleness.** Update an item directly in the DB without bumping the cache. Old data served. Fix invalidation.
**BREAK 3 — Vary header on a CDN edge.** (Stretch) If they're using a CDN: misconfigure `Vary: Cookie` and watch hit rate collapse.

**What the learner internalizes:**
- A naive cache is an outage waiting for the right traffic spike
- Single-flight is one of those mechanisms that looks unnecessary until it isn't
- The cache is *another* source of truth; treat the consistency story explicitly

---

### Loop 7 — Containerize + deploy

**Tier mapping:** T9 (entire — 12-Factor, containers, CI/CD), T5.8 (graceful shutdown)
**Time:** 120-180 min
**Theme:** *runs on my laptop is not a deploy strategy.*

**Build.** Multi-stage Dockerfile producing a minimal image (<50MB for Go, <200MB for Python slim). Non-root user. `docker-compose.yml` for the full stack (app + Postgres + Redis + worker). Then deploy to a real cloud — easy mode: Fly.io, Render, or Railway (free tiers, no AWS billing surprises). Hard mode: AWS ECS or EC2 with Terraform.

**WIN criteria:**
- Image scanned with Trivy; no critical CVEs
- 12-Factor audit (use the planted-violations exercise from `exercise-bank.md`): all 12 factors satisfied
- Graceful shutdown handling SIGTERM (drain inflight, close pools, exit clean within 30s)
- Health endpoints for liveness and readiness; verify behavior under DB hiccup
- Service is reachable on the public internet

**BREAK 1 — secret in image.** Bake an env var into the Dockerfile, scan the image, find it. Fix.
**BREAK 2 — config in code.** Hardcode the DB URL. Realize you can't deploy to staging. Fix per 12-Factor III.
**BREAK 3 — kill -9.** Send SIGKILL during a request; lose the request. Send SIGTERM with proper handling; drain cleanly.

**What the learner internalizes:**
- Building a small image is a security feature, not just an aesthetic preference
- The 12-Factor App is operational law, not philosophy
- Graceful shutdown is the difference between a clean deploy and a 0.5% error spike every time

---

### Loop 8 — Real-time + scale out

**Tier mapping:** T0.6 (WebSockets), T1.12 (real-time API patterns), T3.6 (pub/sub), Path: Real-time
**Time:** 180 min — the biggest loop, plan for two sittings
**Theme:** *the live cursor is the easy part; making it survive a second instance is the hard part.*

**Build.** Add WebSocket support to the service. Live-update the "popular links" list when someone adds a link. Or — more fun — a simple chat room per "list" that users sharing a list can use.

**WIN criteria (single-instance):**
- Two browser tabs see each other's updates in real time
- Reconnection logic handles disconnects gracefully
- Auth on the WebSocket upgrade (cookie or token)
- Backpressure handled (slow client doesn't OOM the server)

**BREAK — the second instance.** Run two app instances behind a load balancer. Open one tab connected to instance A and another connected to instance B. Updates don't cross instances.

**WIN criteria (multi-instance):**
- Add Redis pub/sub bridging the instances
- Sticky sessions configured at the LB (so reconnects land on the same instance)
- Replay protocol on reconnect (Last-Event-ID or sequence numbers) so clients don't lose messages during a flap

**What the learner internalizes:**
- Single-instance WebSocket servers are toys; the moment you horizontal-scale, you need a pub/sub layer
- Sticky sessions are a load-balancer feature with operational consequences
- "Reconnect with replay" is its own protocol that has to be designed, not assumed

---

### Loop 9 — Observability + planted bug

**Tier mapping:** T6 (entire), T7 (peripheral)
**Time:** 120-150 min
**Theme:** *find the bug from telemetry alone.*

**Build.** Instrument the service end-to-end with OpenTelemetry (traces + metrics) and structured logs (JSON, correlation IDs propagated across services). Run Jaeger or Tempo locally for trace visualization. Run Prometheus + Grafana for metrics. Define one SLO with multi-window burn-rate alerts.

**WIN criteria:**
- Every HTTP handler emits a span; every DB call emits a child span with the query as an attribute (sanitized)
- Logs and traces share correlation IDs (you can grep logs from a trace ID)
- One SLO with one alert; alert fires at the correct thresholds
- A runbook for the alert: what's broken, what to check, what to do

**BREAK — the planted bug.** Tutor injects a subtle bug — something like: "list endpoint occasionally returns the wrong tenant's links because a goroutine-local context isn't being propagated correctly" or "p99 latency spikes for 1% of requests due to a missing index on a rarely-hit code path." The learner debugs from telemetry alone — no `println`, no debugger.

Tutor reveals the bug after the learner finds it (or after 45 minutes of stuck).

**Stretch — metric cardinality explosion.** Add a label like `user_id` to a counter. Watch Prometheus scrape times balloon. Fix.

**What the learner internalizes:**
- Telemetry is not observability; *being able to answer questions you didn't pre-plan* is observability
- Traces beat logs for "what happened on this specific request"; metrics beat both for "is the system healthy"
- Cardinality is the silent cost of metrics

---

### Loop 10 — Load test + capacity + postmortem

**Tier mapping:** T7 (entire), T6.7 (postmortems), T11 (peripheral — distributed failure modes if they emerge)
**Time:** 180 min
**Theme:** *break it on purpose, then write the RCA.*

**Build.** k6 load test ramping from 0 → 1000 RPS over 5 minutes. Soak at peak for 5 minutes. Identify the breaking point. Whatever fails first becomes the postmortem subject.

**WIN criteria:**
- Load test scripted, parameterized, reproducible
- Identified the bottleneck: connection pool, DB query, single-threaded code path, GC pauses, network egress, etc.
- Fixed (or capped, with a documented limit) the bottleneck
- Re-ran the load test; quantified the improvement
- Wrote a postmortem: timeline, contributing factors (not "root cause"), action items with owners (even if the owner is "future me")

**Reproduce-an-incident option.** Instead of waiting to see what breaks, deliberately reproduce one of:
- Cache stampede (revisit Loop 6's break under sustained load)
- Retry storm (caller has aggressive retries; downstream slows)
- Connection pool exhaustion (revisit Loop 2's break under load)
- Cascading timeout (timeout on hop A doesn't propagate to hops B and C)

**Postmortem template** (in `~/backend-dev/projects/loop-10-postmortem/postmortem.md`):
```markdown
# [Service] — [date] load test postmortem

## Summary
[1-2 sentences. What broke, what user-visible behavior, how long until recovery.]

## Timeline
- [HH:MM] load test started
- [HH:MM] first error rate above 1%
- [HH:MM] p99 above 1s
- [HH:MM] root contributing factor identified
- [HH:MM] fix applied; recovery confirmed

## Contributing factors
1. [Factor 1 — system, not person]
2. [Factor 2]
3. [Factor 3]

## What went well
- [E.g., the SLO alert fired correctly; the runbook from Loop 9 actually worked]

## Action items
- [ ] [Concrete change with owner]
- [ ] [Test added to prevent regression]
- [ ] [Documentation / runbook update]
```

**What the learner internalizes:**
- "Capacity" is a property you measure, not assume
- The first thing that breaks is rarely the thing you thought would break
- Postmortems are an artifact you write, not a meeting you attend; the writing is where the learning lives

---

## Cross-loop discipline

### Foundations spiral-back is mandatory

Builder-first is *not* a license to skip foundations — it's a different *order*. Every break in every loop is a foundations question in disguise. When the learner says "wait, why does Postgres lock the table here?" the answer is T2.3 (transactions/isolation) and T2.5 (migrations) — pause the loop, fill the foundation, *then* return.

**The tutor's job: notice the unfilled foundation, name it, fill it, return.** If a learner power-builds through every loop without ever asking "why," the tutor should *interject* with calibration probes — "before we move on, what specifically does `ACCESS EXCLUSIVE` block?" — and refuse to advance until the answer is real.

### Build-first does not mean code-first

The first 5 minutes of every loop is *theory* — the loop's `README.md`, the `BREAK.md`, the success criteria, the "you'll fight this exact thing in production" anchor from `incidents.md`. Then code.

### Per-language scaffolding rules

`assets/builder-first/<language>/loop-N-<slug>/`:
- **Go**: prefilled scaffold with TODOs, `go.mod`, `Dockerfile`, integration test stubs, `docker-compose.yml`
- **Python**: same but with `pyproject.toml` + uv lockfile
- **Other languages** (Node, Java, Kotlin, Rust): copy from `assets/builder-first/_spec-only/loop-N-<slug>/` instead — README, BREAK, WIN, NOTES, quickpass, no prefilled language code. Learner implements against the spec. Tutor reviews.

### Module / project structure across loops

The path is conceptually *one evolving service*, not 10 separate projects. Loop 1 and Loop 2 ship as standalone Go modules (their own `go.mod`) so a brand-new learner can `go run .` immediately. From Loop 3 onward, each loop dir contains *only the new files* for that loop — migrations, new packages, new commands. The learner's actual project is wherever they decide to evolve it (typically the loop-1 dir, renamed and grown in place).

When the tutor copies scaffolding to `~/backend-dev/projects/`, all 10 loop dirs land there as references. The tutor coaches the learner on whether to evolve loop-1 in place or copy each loop forward — both work; in-place is simpler.

Loop 3+ scaffolds assume the learner imports the new packages into their existing `go.mod`. A tutor checklist for each loop's setup: "verify `go.mod` has the new dep" before declaring the loop's tasks ready.

### Skip mechanism

`/loop skip` exists for a reason. If the learner has already shipped the loop's content in a prior job (e.g., they've owned WebSockets at scale), skipping Loop 8 with a 30-second summary preserves momentum. **Always offer `/loop quickpass` before `/loop skip`** — quickpass forces a small proof, skip doesn't.

### Loop dependency map

```
1 ──→ 2 ──→ 3
       └──→ 4 ──→ 5 ──→ 9 ──→ 10
            └──→ 6 ────┘
            └──→ 7 ────┴──→ 8
```

- 2 needs 1 (the API surface to persist)
- 3 needs 2 (a populated DB to migrate)
- 4 can fork off 2 (auth doesn't strictly need the DB to be migrated)
- 5 can fork off 4 (async work probably wants user-aware notifications)
- 6 can fork off 4 (caching is meaningful once there's user-specific data)
- 7 can fork off any of 4/5/6 (containerize whatever you have)
- 8 needs 7 (multi-instance requires deploy)
- 9 needs 7 (telemetry across containers is meaningfully different from local)
- 10 needs 7+9 (load test against a deployed, instrumented service)

The tutor enforces this via `/loop [N]` warnings if prereqs are missing.

---

## When to leave builder-first for a tier-by-tier sweep

Some learners will hit Loop 6 and realize they want to deep-dive Postgres for a week before continuing. That's fine — switch `orientation` to `foundations_first` in `progress.json`, run T2 sub-topics in order, then come back. The two paths are not mutually exclusive; they're orderings.

Likewise, a Senior-lane learner may run Loops 1-3 fast, then say "I just need T11 — I'm here for distributed-systems gap-fill." Honor it. Save loop progress; jump to T11 lessons; the loops will still be there if they want to return.

---

## Anti-patterns

- ❌ Hand the learner a fully-working solution at the start of any loop — the *building* is the lesson
- ❌ Skip a BREAK because "it'd take 10 minutes" — the BREAKs are where the foundations get filled
- ❌ Move to Loop N+1 before Loop N's WIN criteria are met — momentum is good, ungrounded momentum is debt
- ❌ Treat language preference as a barrier — if the learner picked Rust and we don't have prefilled scaffolding, hand them the spec, review their code
- ❌ Generate the loop's code with the tutor — they wrote it = they own it; the tutor coaches, doesn't pair-code unless the learner is genuinely stuck on the hint ladder's lower rungs
