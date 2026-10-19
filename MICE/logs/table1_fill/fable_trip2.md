# Second guard trip: Fable 5.1 and Sonnet (2026-10-19 17:11:52)

## Question
Senior methodology adviser, read-only, one bounded decision. Answer: Decision / Supporting evidence / Alternative options / Key risks / Remaining uncertainty / Confidence / Requires user approval. Short.
Read: experiments/mice_table1_fill_20261018/AMENDMENT_BASELINES_20261018e.md (incl. Deviation 1), dtmoe_guard.sh.

New event: dtmoe probe PASSED 16:15:29 (3 probes byte-identical). Grid started 16:15:51 with 4 dtmoe lanes + 8 running extension lanes (4 extension procs SIGSTOPped) = 12 running CPU + DR. Guard tripped 16:26:34: DR stream h3_covertype_b recent-25 median 8.49 s vs earlier median 6.98 s (+22%). The earlier batches of this stream ran with only 8 extension lanes + 2 dtmoe probe lanes (10 running; the elec2 probes had finished), so its reference was a 10-process baseline. For comparison: DR h3_airlines_b ran at 7.35 s/batch for 11 h with 12 extension lanes + DR (the originally registered state, never tripped because the guard did not exist). Probe phase 12:50-13:07 with 12 running (8 ext + 4 dtmoe, elec2 tasks): +5%. Now dtmoe stopped (no deaths, 3 grid outputs = the probe a outputs), I resumed the 4 suspended extension procs (registered: resume when dtmoe stops) -> 12 extension lanes + DR again.
Deviation 1 says: "A second trip on the DR criterion with 12 running processes means the cause is not the process count; dtmoe then waits for the end of the extension." But the guard's reference is relative to whatever ran earlier in the same stream, so a stream that starts under a lighter load trips when load returns to 12 — the trip may be a baseline artifact, and after the extension ends dtmoe + the other tests would again be 12 running, likely tripping again.
Remaining work (CPU-h): extension ~600, other 4 methods' tests up to ~700, dtmoe grid ~285 (+ possible n_steps-25 extension ~1000), dtmoe tests ~60+. DR ~70 h left (GPU, single process); DR at 12-lane load ~7.4 s/batch vs ~7.0 at 10.
Question: what now? Options: (A) follow deviation 1 literally: dtmoe waits for the extension's end (~2 days), then guard as is (likely trips again); (B) redefine the guard's reference as fixed (e.g. DR may be at most 20% slower than its batch time under the registered 12-process load, measured per stream from a reference period, or an absolute cap) and run dtmoe at 4 lanes within 12 now (extension back to 8); (C) dtmoe waits for DR to finish (~3 days), then no DR constraint; (D) other. Also: does any choice need user approval (the user approved "16 with a guard"; deviation 1 fixed the rule above)?

## Fable (0.63 USD, 115 s)
**Decision.** Do not restart dtmoe now and do not redefine the guard. Keep the 12 extension lanes (already resumed), let the extension finish (~2 days), and keep dtmoe waiting until DR finishes (~3 days, i.e. option C, which contains the literal Deviation 1 wait of option A). Log this as Deviation 2 now. Then dtmoe runs with the DR criterion moot, not amended.

**Supporting evidence.**
- The trip is only partly a baseline artifact. The covertype_b reference was a 10-process load (6.98 s). Your own numbers put the 10→12 extension-lane delta at about +6%, so a 12-lane expectation is ~7.4 s; the observed 8.49 s is still ~+15% above that. The elec2 probe at 12 running cost +5%, the grid tasks (insects/covertype, L32) cost ~+22%. So dtmoe grid lanes load DR noticeably more than extension lanes do. Deviation 1's inference ("second trip at 12 ⇒ cause is not process count") is not established, but its consequence (dtmoe waits) is the conservative reading and happens to match the evidence.
- Waiting costs essentially no Table 1 completion time. The CPU cap of 12 is the binding constraint and the extension (~600 CPU-h) plus the other tests (~700 CPU-h) keep all 12 lanes busy for the whole waiting period. dtmoe's grid (180 tasks) parallelises to 12 lanes later, so the total ~1,645 (+1,000) CPU-h finishes on the same date regardless of order. What moves is only when dtmoe results become visible (~2–3 days later).
- DR itself is on the critical path (~70 h). Running extension lanes instead of dtmoe lanes in these 3 days keeps DR at ~7.4 s/batch rather than ~8.5, saving ~10 h on DR.
- Option B changes a user-set condition ("16 with a guard") immediately after it tripped. Even though the guard has no influence on selection, a rule rewritten right after its trigger is the pattern a reviewer of the registration log will flag. Waiting is the only option that touches no registered rule.

**Alternative options.**
- A (literal): restart dtmoe at the extension's end under the unchanged guard. DR will have ~1 day left, 6 dtmoe lanes against a 12-extension reference probably trips again (grid lanes cost more than extension lanes). Gains one day of dtmoe visibility at the cost of a likely third trip and quarantine churn.
- B (fixed reference): methodologically harmless to results but needs the user's approval and a second rewrite; with 6 dtmoe lanes it may trip anyway.
- D: 2 dtmoe lanes within 12 now. Probably stays under 20% once the next DR stream has a 12-lane reference, but it is fiddly, slows DR, and is a third rule change for a small gain.
- After DR ends, consider going back to the user-approved 16 (dtmoe 8, tests 8), since the DR criterion was the only one that tripped. Needs a logged note; I would ping the user with it in the same message as the Deviation 2 report.

**Key risks.**
- Extension or test queues thin out into a tail where fewer than 12 lanes are busy; then idle lanes are the real cost of waiting. Check the queue lengths when the extension nears its end.
- DR's "~70 h" could stretch (next streams heavier); then C delays dtmoe more than 3 days. Re-evaluate at the extension's end: if DR has > ~1.5 days left, start dtmoe at 4 lanes then (A), accepting a possible trip.
- The dtmoe n_steps-25 extension (~1,000 CPU-h) is a sequential decision chain; starting it 3 days later pushes its decision point later, though not the finish date if lanes stay full.

**Remaining uncertainty.** The dtmoe-specific DR slowdown (~+15% beyond process count) is inferred from one stream pair, not measured in isolation. Record covertype_b's batch time now under 12 extension lanes: if it returns to ~7.4 s the inference holds and belongs in Deviation 2; if it stays near 8.5 the slowdown is load-count or stream-specific, and option A becomes safer.

**Confidence.** Moderate-high that waiting is right and nearly free on the completion date; moderate on the exact magnitude of the dtmoe-specific slowdown.

**Requires user approval.** Not for waiting (A or C): it is more conservative than the registered rule and alters no result path. Inform the user anyway, since they chose dtmoe-on-CPU and will care about the 2–3 day delay. Option B does need approval: the guard is the user's condition on the 16-process decision. Returning to 16 after DR ends should also be put to the user, in the same report.

## Sonnet review (23 s)
1. **The decision isn't literally within the registered rule, and the integrity claim is overstated.** Deviation 1 says dtmoe waits for the end of the extension. Option C waits roughly a day longer, until DR ends, and is logged as a new Deviation 2. So "waiting is the only option that touches no registered rule" is wrong. The expert also says the "cause is not process count" inference isn't established, then relies on that same trigger to justify a longer wait. The expert's "no approval needed" call is therefore shaky, because this adds a new rule on top of the user's "16 with a guard" approval.

2. **The "dtmoe-specific slowdown" evidence mixes baselines.** The +22% is measured against a 10-process reference. The +5% probe figure comes from a different load and task type, elec2. Subtracting 6% to get about +15% is arithmetically fine. But the pair of streams doesn't isolate dtmoe from stream or dataset effects, so it can't carry the claim that grid lanes load DR more than extension lanes do. The expert admits this at the end but still builds the decision on it.

3. **"Finishes on the same date regardless of order" contradicts the stated critical path.** dtmoe tests depend on the dtmoe grid. The possible n_steps-25 extension (~1,000 CPU-h) is a sequential chain that would start about 3 days later. Delaying dtmoe by 3 days therefore likely extends the end date, even with full lanes. The extension and the other 4 methods' tests are about 1,300 CPU-h. At 12 lanes that is about 108 h, longer than the 72 h wait. But if some of those tests depend on the extension finishing, the lanes may thin out near the end of the wait, which the expert only notes as a risk.

## Disposition: keep the registered rule of deviation 1 (dtmoe waits for the extension's end); Fable's longer wait (until DR ends) not adopted now because it is a new rule (Sonnet 1); the measurement Fable asked for (h3_covertype_b under 12 extension lanes) is logged.
