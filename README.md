# PressureIQ – SupeRR Selector S2, Round 1: supplementary material
Dashboard: https://pressureiq.kleap.io/

| Path | What it is |
|---|---|
| `SupeRR_Round1_Analysis_v2.ipynb` | Full analysis. Sections 1-11 analysis; 12 writes the dashboard JSONs; 13 audit cells. Needs the five raw CSVs next to it (`ball_by_ball, matches, competitions, competition_team_player_mapping, playing_eleven`). |
| `ratings/` | Eligible-player rating tables (99 batters, 68 bowlers). |
| `dashboard_data/` | The JSON files the dashboard reads (sample of the exact deployed inputs). |
| `proof/` | `verify_claims.py <dir>` re-computes scores and cross-checks CSV/JSON/notebook; `evidence_log.txt` is its output. |

Flow: raw CSVs -> notebook -> `ratings/*.csv` + `dashboard_data/*.json` -> dashboard.
