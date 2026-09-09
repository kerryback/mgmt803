import pandas as pd, numpy as np, re, os
D='epoch'
meta = pd.read_csv(f'{D}/model_metadata.csv').dropna(subset=['model_version']).drop_duplicates('model_version')

SIZE = re.compile(r'(\d+(?:\.\d+)?)\s*[bB](?![a-zA-Z0-9])')
def params(name):
    if not isinstance(name,str): return np.nan
    hits = [float(x) for x in SIZE.findall(name)]
    return max(hits) if hits else np.nan

def load(f):
    d = pd.read_csv(f'{D}/{f}')
    d = d.merge(meta[['model_version','model_group','date','organization','accessibility']],
                left_on='Model version', right_on='model_version', how='left')
    d['date'] = pd.to_datetime(d['date'].fillna(d.get('Release date')), errors='coerce')
    col = next(c for c in ['mean_score','Accuracy mean','Score','EM'] if c in d.columns)
    d['score'] = pd.to_numeric(d[col], errors='coerce')
    d = d.dropna(subset=['date','score'])
    d['acc'] = d['accessibility'].fillna('')
    d['open'] = d['acc'].str.startswith('Open weights')
    d['closed'] = d['acc'].isin(['API access','Hosted access (no API)'])
    d['name'] = d['model_group'].fillna(d['Model version'])
    d['params'] = d['name'].map(params)
    # best score per model group (some models have multiple runs / scorers)
    d = d.sort_values('score', ascending=False).drop_duplicates(['name'])
    return d.sort_values('date')

def frontier(d):
    d = d.sort_values('date')
    out=[]; best=-1
    for _,r in d.iterrows():
        if r.score > best:
            best = r.score; out.append((r.date, best, r['name']))
    return pd.DataFrame(out, columns=['date','score','name'])

def lag_months(front, other):
    """For each record-setting open model, months since frontier first hit that score."""
    res=[]
    for _,r in other.iterrows():
        earlier = front[front.score >= r.score]
        if len(earlier)==0: continue
        t = earlier.date.iloc[0]
        res.append((r['name'], r.date.date(), r.score, t.date(), (r.date-t).days/30.44))
    return pd.DataFrame(res, columns=['open_model','open_date','score','frontier_first','lag_months'])

BENCH = {
 'GPQA Diamond':'gpqa_diamond.csv',
 'AIME (OTIS mock)':'otis_mock_aime_2024_2025.csv',
 'Terminal-Bench':'terminalbench_external.csv',
 'SciCode':'scicode_external.csv',
 'MMLU':'mmlu_external.csv',
 'FrontierMath T1-3':'frontiermath_tiers_1_3_v2.csv',
}
for label,f in BENCH.items():
    d = load(f)
    fr = frontier(d[d.closed])
    op = frontier(d[d.open])
    sm = frontier(d[d.open & (d.params<=40)])
    print(f'\n===== {label}  (n={len(d)}, closed={d.closed.sum()}, open={d.open.sum()}, small-open={(d.open&(d.params<=40)).sum()})')
    print(' frontier record holders:', ', '.join(f'{r["name"]} {r.date.date()} {r.score:.2f}' for _,r in fr.tail(4).iterrows()))
    print(' open record holders:    ', ', '.join(f'{r["name"]} {r.date.date()} {r.score:.2f}' for _,r in op.tail(4).iterrows()))
    print(' small record holders:   ', ', '.join(f'{r["name"]} {r.date.date()} {r.score:.2f}' for _,r in sm.tail(4).iterrows()))
    lo = lag_months(fr, op); ls = lag_months(fr, sm)
    if len(lo): print(f'  OPEN  lag: median {lo.lag_months.median():.1f} mo, last 4: ' + ', '.join(f'{r.open_model} {r.lag_months:.1f}' for _,r in lo.tail(4).iterrows()))
    if len(ls): print(f'  SMALL lag: median {ls.lag_months.median():.1f} mo, last 4: ' + ', '.join(f'{r.open_model} {r.lag_months:.1f}' for _,r in ls.tail(4).iterrows()))
