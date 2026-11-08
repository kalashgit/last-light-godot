# LAST LIGHT — Decision log

| # | Date | Decision | Why | Owner | Founder needed |
| --- | --- | --- | --- | --- | --- |
| D1 | 2026-11-08 | Known-good baseline = #26 `f17b35b` | Only stack where all 13 suites pass on Godot 4.6.3 | Director | No |
| D2 | 2026-11-08 | Two duplicate integration PRs exist (#37 Director, #38 W01), both porting #18 onto #26 | Workers launched in parallel without a shared queue | W01 picks; Director recommends #37 (superset: adds lab + 2006-check suite) | Yes, if #19 street viewer must be kept |
| D3 | 2026-11-08 | Workers are resumed in waves of ≤4, not 10 at once | 10 parallel Opus sessions hit the 5-hour account limit in ~40 min; 7 workers died with no pushed work | Director | No |
| D4 | 2026-11-08 | Per-zombie state arrays must be sized from `infected.size()` everywhere | #36 hard-coded 2 entries; crashes the 6-zombie lab | W02 | No |
| D5 | 2026-11-08 | W03 must rebase onto the integration candidate, not #10 | #39 base 86bff44 predates #26 world art; 9 conflict hunks | W03 | No |
| D6 | 2026-11-08 | One world generator: W04 extends `scripts/neighborhood.gd` (lab) | Avoid competing generators (UCF #19 Python, lab GDScript) | W04/W01 | No |
| D7 | 2026-11-08 | Save schema 3 (#36) must keep lab `lab_world` digest check | Lab saves must not load into a different generated world | W02/W01 | No |
