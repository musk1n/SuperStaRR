import json,sys
A,B=sys.argv[1],sys.argv[2]   # shipped dir, generated dir
bad=0
def cmp(a,b,path,lenkeys=()):
    global bad
    if isinstance(a,dict):
        if not isinstance(b,dict): print('TYPE',path);bad+=1;return
        if path.endswith('variants') or path.endswith('names') or path.endswith('probs'): 
            ka=set(a);kb=set(b); 
            if path.endswith('probs') and ka!=kb: print('KEYS',path,ka^kb);bad+=1
            if a and b: cmp(next(iter(a.values())),next(iter(b.values())),path+'/*')
            return
        if set(a)!=set(b): print('KEYS',path,'only shipped',set(a)-set(b),'only generated',set(b)-set(a));bad+=1
        for k in a:
            if k in b: cmp(a[k],b[k],path+'/'+k)
    elif isinstance(a,list):
        if not isinstance(b,list): print('TYPE',path);bad+=1;return
        fixed=('li_percentiles','outcomes_bat','outcomes_bowl','leverage_by_over','hp_share_by_over','by_wickets_lost','by_required_rate','calibration','rows_wp','cols_balls_left','series_cols','wk','balls_left','need','runs')
        if path.split('/')[-1] in fixed and len(a)!=len(b): print('LEN',path,len(a),len(b));bad+=1
        if a and b and not (isinstance(a[0],(int,float)) and isinstance(b[0],(int,float))): cmp(a[0],b[0],path+'[]')
    else:
        if type(a).__name__!=type(b).__name__ and not({type(a).__name__,type(b).__name__}<={'int','float'}) and a is not None and b is not None: print('SCALAR',path,type(a).__name__,type(b).__name__);bad+=1
for f in ['league_stats','outcome_probs','wp_grid','players','matches']:
    a=json.load(open(f'{A}/{f}.json'));b=json.load(open(f'{B}/{f}.json')); n=bad; cmp(a,b,f); print(f'{f}.json:', 'structure identical' if bad==n else 'DIFFERENCES above')
# wp_grid dims
a=json.load(open(f'{A}/wp_grid.json'));b=json.load(open(f'{B}/wp_grid.json'))
for k in a['grids']: print(k,'dims shipped',(len(a['grids'][k]),len(a['grids'][k][0]),len(a['grids'][k][0][0])),'generated',(len(b['grids'][k]),len(b['grids'][k][0]),len(b['grids'][k][0][0])))
print('bad =',bad)
