# AURELIUS — launch decisions the owner owes

**One sheet. Everything on it is a fact or a judgement only AGENOR can
supply.** Nothing here is guessed, and nothing here has a safe default that
I could pick on your behalf without inventing something.

`policy-ready` is blocked on this sheet and nothing else. It is the only
open gate that needs **no device and no wear time** — so it can be closed
today, in parallel with the physical matrix.

Fill in the right-hand column, tell me, and I will commit the answers and
re-derive the readiness record.

---

## A. The four TEST-1 account facts

These decide whether a **14-day, 12-tester closed test** stands between you
and production access. Getting this wrong in either direction is expensive:
wrongly on, you burn two weeks you didn't owe; wrongly off, you plan a
launch that Play will refuse.

Find them in Play Console → *Settings → Developer account → Account
details*, and on the *Dashboard*.

| # | Question | Answer |
|---|---|---|
| 1 | Account type — **personal** or **organisation**? | |
| 2 | Approximate creation date — **before or after 2023-11-13**? | |
| 3 | Is *Test and release → Production* currently accessible? | |
| 4 | Has a previous app already received production access on this account? | |

**What the answers change:**

- **Organisation account**, or **personal created before 2023-11-13** → the
  rule does not apply. No closed test, no 14-day wait.
- **Personal, created after 2023-11-13, no prior production access** → the
  rule applies. Twelve testers, opted in continuously for fourteen days,
  *before* you may even apply. The contingency plan already exists in
  `docs/reports/PHASE_4_TEST1_READINESS.md` — it is proposed only and I
  will not start recruiting without you saying so.
- **Production already accessible** → answer 3 effectively settles it
  regardless of 1 and 2.

---

## B. Support email and response commitment

Appears in the Play listing and in the privacy policy. Both need the same
address.

| Item | Answer |
|---|---|
| Support email address | |
| Response commitment (*"expect a reply within N business days"*) | |

**Suggestion, not a decision:** 3 business days is a common, easily-kept
commitment for a paid one-off utility. Anything faster is a promise you
have to keep on a bad week. You can also decline to state a number — the
draft copy works without one — but a stated commitment reads better on a
paid listing.

---

## C. Privacy policy hosting

The text is **already written and needs no editing** — see
`docs/commercial/aurelius/2.0.0-rc2/COPY_DRAFT.md`. Play requires a public
URL even for an app that collects nothing, and there is no repository
substitute for hosting.

| Item | Answer |
|---|---|
| Confirm the URL — `https://x1c7.com/privacy/aurelius` or something else? | |
| Who hosts it, and when will it be live? | |

Once you give me the support email, run:

```bash
python3 tools/render_privacy_policy.py --email <you@x1c7.com> --date 2026-07-26
```

That renders a self-contained `privacy_policy.html` ready to upload,
records its **sha256** in `PRIVACY_POLICY.json`, and gives the readiness
record a content checksum to bind — which it currently lacks. After the
page is live, the same tool can verify the hosted bytes still match what
was approved, so the policy cannot drift silently after submission.

---

## D. Price and initial markets

ChatGPT recommends **$3.99 one-time**. That is recorded in the repository
as a *recommendation* and has never been recorded as your decision.

| Item | Answer |
|---|---|
| Price (one-time) | |
| Initial markets | |

**My read, since you'll want one:** $3.99 is sensible for a first paid
watch face with no catalogue behind it. The floor for "this is a serious
object" is around $2.99; above $4.99 you are competing with faces that
ship companion apps and complication packs, which this deliberately does
not. A one-off purchase also keeps the data-safety declaration trivially
true — no accounts, no subscriptions, nothing to collect.

Worth knowing: Google Play allows a **paid app to become free**, but that
change is one-way — once the app is free, it cannot return to paid. An app
first published as free also cannot later become paid. If there is any
chance you want a permanently free edition, separate paid/free package, or
other tiering strategy, decide that before first publication.

---

## What I am NOT asking you to decide yet

- **Signing.** No production key exists and none is authorised under
  ADR-010 §5. That stays shut until architecture and policy are both
  approved — deliberately, so a key cannot be created early and quietly.
- **Publishing.** `publishable` is interlocked behind five predecessors.
  Nothing on this sheet opens it.

---

## TL;DR for this sheet

Four account facts, one email, one response commitment, one hosting
confirmation, one price. That is the whole of `policy-ready`.
