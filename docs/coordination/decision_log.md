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
| D8 | 2026-11-09 | **Founder decision needed: one canonical world/neighborhood line.** Competing: #37 lab (`scripts/neighborhood.gd`), #38 + #19 UCF street, #54/#55/#56/#57/#58/#60 ChatGPT neighborhoods, #67 W04 worldgen (on #19), #71 GM00 (on #60, already sent to founder as Xogot zip) | Integrating several world generators into one game is not possible without choosing a base; further integration work (W01/W03/W08 rebases) waits on this | Founder | **Yes** |
| D9 | 2026-11-09 | Workers are no longer dispatched in parallel until D8: only salvage messages (push existing work) | Second usage-limit failure wave at 23:44Z killed W01/W03/W05/W07/W09/W10 again | Director | No |
| D10 | 2026-11-09 | Game-side V2 intake (`scripts/asset_intake_v2.gd`, c2c18d6) is the single gate for F12 packages into the game; W06 `LL_ATLAS_OUTPUTS_V2` (#73) and W08 presentation adapter (#72) should feed it rather than add new loaders | Avoid duplicate asset pipelines (V2 directive rule 3/5) | W01 | No |
