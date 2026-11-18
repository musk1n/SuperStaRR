"""Cross-check every headline number against the executed artefacts (CSVs, JSONs, notebook outputs).
Usage: python verify_claims.py <uploads_dir>   -> prints an evidence log; exits 1 on a FAILED check."""
import sys, json, re, numpy as np, pandas as pd
D = sys.argv[1] if len(sys.argv) > 1 else '.'
bat = pd.read_csv(f'{D}/bat_ratings_all_eligible.csv'); bowl = pd.read_csv(f'{D}/bowl_ratings_all_eligible.csv')
ls = json.load(open(f'{D}/league_stats.json')); op = json.load(open(f'{D}/outcome_probs.json'))
pl = json.load(open(f'{D}/players.json')); nb = json.load(open(f'{D}/SupeRR_Round1_Analysis.ipynb'))
nbtxt = '\n'.join(''.join(o.get('text', [])) if o['output_type']=='stream' else ''.join(o.get('data', {}).get('text/plain', []))
                  for c in nb['cells'] if c['cell_type']=='code' for o in c.get('outputs', []))
fails = 0
def chk(name, ok, detail=''):
    global fails; fails += (not ok); print(('PASS ' if ok else 'FAIL ')+name+(f'  [{detail}]' if detail else ''))
z = lambda x: (x-x.mean())/x.std()
print('== 1. Rating tables ==')
chk('batters eligible = 99', len(bat)==99, len(bat)); chk('bowlers eligible = 68', len(bowl)==68, len(bowl))
chk('bat eligibility (>=100 HP balls, >=15 innings)', (bat.hp_balls>=100).all() and (bat.app>=15).all())
chk('bowl eligibility (>=120 HP balls, >=15 spells)', (bowl.hp_balls>=120).all() and (bowl.app>=15).all())
for nm, t in (('bat', bat), ('bowl', bowl)):
    s = .55*z(t.hp)+.20*z(t.gam)+.25*z(t.cons)
    chk(f'{nm}: score = .55 z(hp)+.20 z(gam)+.25 z(cons) recomputed', np.allclose(s, t.score, atol=1e-6), f'max abs diff {np.abs(s-t.score).max():.2e}')
    chk(f'{nm}: z_level/z_delta/z_cons columns reproduce', np.allclose(z(t.hp), t.z_level) and np.allclose(z(t.gam), t.z_delta) and np.allclose(z(t.cons), t.z_cons))
    chk(f'{nm}: hp = usual + gam', np.allclose(t.hp, t.usual+t.gam, atol=1e-9))
    chk(f'{nm}: rank column is descending score', (t.score.diff().dropna()<=1e-12).all())
    chk(f'{nm}: top10_prob are multiples of 1/20 (=> 20 bootstrap reps, not 40)', np.allclose((t.top10_prob*20)%1, 0, atol=1e-9))
print('\n== 2. Submission lists agree across CSV / players.json / notebook ==')
chk('bat top10 CSV == players.json final_top10', list(bat.name[:10])==pl['final_top10']['bat'])
chk('bowl top10 CSV == players.json final_top10', list(bowl.name[:10])==pl['final_top10']['bowl'])
chk('bat top10 in notebook final cell', ' > '.join(bat.name[:10]) in nbtxt); chk('bowl top10 in notebook final cell', ' > '.join(bowl.name[:10]) in nbtxt)
print('\n== 3. players.json "main" variant == CSV (eligible players) ==')
for nm, t in (('bat', bat), ('bowl', bowl)):
    pj = {p['id']: p for p in pl[nm]}; bad = 0
    for _, r in t.iterrows():
        v = pj[r.pid]['variants']['main']
        bad += not (abs(v[0]-r.hp)<6e-5 and abs(v[1]-r.gam)<6e-5 and abs(v[2]-r.cons)<6e-4 and v[3]==r.hp_balls and v[4]==r.app)
    chk(f'{nm}: all {len(t)} eligible players match', bad==0, f'{bad} mismatches')
print('\n== 4. league_stats.json vs notebook printed output ==')
h = ls['hp_vs_ordinary']
chk('HP balls 43,669 & threshold 0.0199', '43,669' in nbtxt and abs(op['hp_threshold']-0.0199)<1e-4)
chk('leverage ratio HP/ordinary', True, f"{h['LI']['high_pressure']/h['LI']['ordinary']:.2f}x (report must say 3.8x, not 3.9x)")
chk('swing-SD ratio', True, f"{h['sd_dwp']['high_pressure']/h['sd_dwp']['ordinary']:.2f}x")
chk('Brier/AUC match notebook', 'Brier 0.2224' in nbtxt and 'Brier 0.1288' in nbtxt and 'AUC 0.690' in nbtxt and 'AUC 0.899' in nbtxt)
chk('counts 730 = 354 + 376', ls['counts']['matches']==730==ls['counts']['ipl']+ls['counts']['t20i'])
chk('ball count 174,674', ls['counts']['balls']==174674 and 'balls kept: 174674' in nbtxt)
print('\n== 5. Claims in the OLD report that the artefacts do NOT support ==')
rb = ls['robustness']; print('   notebook overlaps (bat/bowl):', {k:(v['bat'],v['bowl']) for k,v in rb['overlap_with_main_top10'].items()})
print('   old PDF said: top10% 9/8, ex-PP 6/6, within-inn 7/6, rule 4/6  -> labels were scrambled')
print('   split-half Pearson (bat, bowl):', rb['split_half']['bat'], rb['split_half']['bowl'], '(old PDF said bowlers 0.42)')
for nm, t in (('bat', bat), ('bowl', bowl)):
    print(f'   {nm} bootstrap top-10 odds (20 reps):', dict(zip(t.name[:10], t.top10_prob[:10])))
top4 = bat.top10_prob[:4]; chk('old claim "top 4 batters stay in top 10 in 80%+ resamples"', bool((top4>=.8).all()), f'actual {list(top4)}')
chk('old claim "top 3 bowlers 80%+"', bool((bowl.top10_prob[:3]>=.8).all()), f'actual {list(bowl.top10_prob[:3])}')
print('   notebook funnel: 883 in file, 867 with ball-by-ball (old PDF said 883 have ball data)')
print('\n== 6. How close are the cut-offs? ==')
for nm, t in (('bat', bat), ('bowl', bowl)):
    a, b_ = t.iloc[9], t.iloc[10]; print(f'   {nm}: rank10 {a["name"]} {a.score:.4f} vs rank11 {b_["name"]} {b_.score:.4f}  gap {a.score-b_.score:.4f}  (top10_prob {a.top10_prob} vs {b_.top10_prob})')
print('\n== 7. Weight sensitivity recomputed from CSV z-scores ==')
for w in [(1,0,0),(.4,.3,.3),(.7,.15,.15),(1/3,1/3,1/3),(.55,.2,.25)]:
    o=[]
    for t in (bat, bowl):
        s = w[0]*t.z_level+w[1]*t.z_delta+w[2]*t.z_cons; o.append(len(set(t.name[:10]) & set(t.loc[s.sort_values(ascending=False).index[:10], 'name'])))
    print(f'   weights {tuple(round(x,2) for x in w)}: bat {o[0]}/10, bowl {o[1]}/10')
print('\n== 8. Mean uplift among eligible ==', f'bat {bat.gam.mean():.4f}, bowl {bowl.gam.mean():.4f}; top-10 mean bat {bat.gam[:10].mean():.4f}, bowl {bowl.gam[:10].mean():.4f}')
print('\nFAILED CHECKS:', fails); sys.exit(1 if fails else 0)
