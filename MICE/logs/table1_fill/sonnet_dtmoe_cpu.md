# Sonnet 5.5 review of amendment e and dtmoe_cpu.sh / dtmoe_guard.sh (2026-10-19)

## Round 1 (35 s)
1. **P1: guard watches the wrong DR stream.** Location: `dtmoe_guard.sh` line 22, `ck=$(ls $DR/*.ckpt.npz | head -1)`.
   - Evidence: finished DR streams probably keep their `.ckpt.npz`, and `head -1` takes the first one alphabetically. A stale completed checkpoint has a constant `t`, so the slowdown check never sees the running stream and the DR 20% condition silently never fires.
   - Fix: pick the newest checkpoint by mtime (`ls -t | head -1`) and skip it if its mtime is older than about 10 minutes. Log "no live DR checkpoint" so a missing reference is visible.

2. **P2: kill race in the guard.** Location: `dtmoe_guard.sh` `trip()` and `dtmoe_cpu.sh` `task()` lines 20–22.
   - Evidence: the guard writes STOP, then kills once. A task that passed its `[ -e STOP ]` check just before the write can launch `run_ts.py` after the kill list was taken. That process survives, and the guard has already exited.
   - Fix: in `trip`, repeat the kill several times over about 10 s (for example `for i in 1 2 3 4 5; do kill…; sleep 2; done`) before exiting. Alternatively, have `task` re-check STOP right after launching.

3. **P2: death counter resets after a STOP restart.** Location: `dtmoe_cpu.sh` line 19 (`for a in 1 2`) and line 26.
   - Evidence: the attempt number `a` is local to one invocation. The protocol says "rerun once, a second death is GAVE UP", but a task that really died once and is then restarted after STOP gets two more attempts.
   - Evidence: the quarantine directory `$D/quarantine/$t.$a` is reused across invocations. `mkdir -p` followed by `mv` silently overwrites earlier quarantined files.
   - Fix: count deaths from `ls -d $D/quarantine/$t.[0-9]*` and exclude the STOP-stopped ones. Use a timestamped quarantine directory name.

4. **P2: `quarantine/$t.$a` mixes real deaths with stops.** Location: `dtmoe_cpu.sh` line 26 versus line 27.
   - Evidence: files are moved to `$t.$a` before the STOP check. A guard-killed partial is therefore stored under the "death" name, which conflicts with "not counted as deaths".
   - Fix: check STOP first and move to `$t.stop<ts>` in that case.

5. **P2: the grid-end count can overstate valid outputs.** Location: `dtmoe_cpu.sh` line 54, `ls $D/dev/P/*.npz | wc -l`.
   - Evidence: the glob also matches a leftover `*.tmp.npz` and any file whose device is not cpu. It reports "n of 180 outputs" without validating them.
   - Fix: count with `ls … | grep -v '\.tmp\.npz$'`, and run `loads` on each file. Log any missing tags against the `GRID` list.

6. **P2: a stale PASSED line can unlock the grid.** Location: `dtmoe_cpu.sh` line 51.
   - Evidence: `grep -q "probe pre PASSED" progress.txt` matches any past line, so the grid launches even if an `UNVERIFIED_*` file exists or a later probe failure was logged. A failed or aborted probe also leaves `probe_pre` in place, and line 40 then refuses to rerun it without manual cleanup.
   - Fix: use a `PASSED` marker file written once, and have the grid refuse if any `UNVERIFIED_*` file exists. Document the manual reset path.

7. **P2: the guard exits between phases.** Location: `dtmoe_guard.sh` line 17 together with the launch plan.
   - Evidence: the guard exits when no `dtmoe_cpu.sh` is running. After probe, bookend or oldcmp finishes, nothing protects the next phase unless the guard is relaunched by hand.
   - Fix: have `dtmoe_cpu.sh` start the guard itself if it is not running (pidfile or `flock`), or state in the plan that the guard must be relaunched before each phase.

## Round 2, re-check of the fixes (23 s)
1. **Wrong DR checkpoint:** Fixed. The guard now takes the newest `*.ckpt.npz` by mtime. A stale checkpoint left by a crashed stream could still be read if nothing newer exists.
2. **Kill race:** Fixed. `trip` writes STOP first, then kills six times at 5-second intervals, and `task` checks STOP before each launch.
3. **Death counter reset / quarantine overwrite:** Fixed. Deaths are counted per `<outdir>__<tag>` in a persistent file, and quarantine names carry a timestamp and a kind.
4. **Stop vs death quarantine naming:** Fixed. The names are `.stop.` and `.death.`, and a stop is not counted as a death.
5. **Grid count includes invalid:** Fixed. The count now uses `loads`, which also checks `device == cpu`.
6. **Stale PASSED line / UNVERIFIED not checked:** Fixed. Line 40 refuses to run when an `UNVERIFIED_*` marker exists, and the refusal-if-exists guards stop a stale PASSED from persisting.
7. **Guard exits between phases:** Fixed. Every invocation restarts the guard, and nothing runs between phases.

**New defects:**
- **Medium:** The guard's liveness check is `grep "^bash .*dtmoe_cpu.sh"`. If the coordinator is launched through the shebang (`./dtmoe_cpu.sh`), its args are `/bin/bash ./dtmoe_cpu.sh`. There is no match, so the guard exits after its first 120-second sleep and the lanes run unguarded. Match `[d]tmoe_cpu.sh` without the `^bash` anchor.
- **Low–medium:** The guard sleeps 120 s before its first check, so GPU_STOP, a dead `fecs_watch`, or high load goes unwatched for the first 2 minutes of every phase. Run one check before the sleep.
- **Low:** In `bookend`, if `task` returns 1 (STOP or gave up), the script still runs `$CMP`, which fails and writes `UNVERIFIED_<stage>`. The leftover `probe_post_<stage>` directory then blocks a rerun. Check the `task` return code first and exit without writing UNVERIFIED.
- **Low:** If a new invocation starts while the old guard is in its final moments, the new guard fails the flock and exits. The run is then left unguarded.

## Disposition (coordinator)
Round 1: all 7 accepted and fixed (finding 1: finished DR streams keep no checkpoint, so the old code was not wrong now, but ls -t is safer). Round 2: all 4 new findings accepted and fixed (unanchored liveness pattern, 10 s first sleep, bookend checks the task return code, flock -w 90).
