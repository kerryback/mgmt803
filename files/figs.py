import pandas as pd, numpy as np, re, os, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import timedelta

PLUM='#595460'; BLUE='#6f8497'; SAGE='#7f9068'; GRAY='#c9cbc9'; INK='#3b3842'; PANEL='#fbfbfa'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12.5,'text.color':INK,
    'axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK,'axes.edgecolor':'#b9bcbc',
    'figure.facecolor':'white','axes.facecolor':'white','axes.grid':True,'grid.color':'#e9eaea',
    'grid.linewidth':0.8,'axes.spines.top':False,'axes.spines.right':False})

D='epoch'
meta = pd.read_csv(f'{D}/model_metadata.csv').dropna(subset=['model_version']).drop_duplicates('model_version')
SIZE = re.compile(r'(\d+(?:\.\d+)?)\s*[bB](?![a-zA-Z0-9])')
def params(n):
    if not isinstance(n,str): return np.nan
    h=[float(x) for x in SIZE.findall(n)]
    return max(h) if h else np.nan

def load(f):
    d = pd.read_csv(f'{D}/{f}')
    d = d.merge(meta[['model_version','model_group','date','accessibility']],
                left_on='Model version', right_on='model_version', how='left')
    d['date'] = pd.to_datetime(d['date'].fillna(d.get('Release date')), errors='coerce')
    col = next(c for c in ['mean_score','Accuracy mean','Score','EM'] if c in d.columns)
    d['score'] = pd.to_numeric(d[col], errors='coerce')
    d = d.dropna(subset=['date','score'])
    d['acc']=d['accessibility'].fillna('')
    d['open']=d['acc'].str.startswith('Open weights')
    d['closed']=d['acc'].isin(['API access','Hosted access (no API)'])
    d['name']=d['model_group'].fillna(d['Model version'])
    d['params']=d['name'].map(params)
    return d.sort_values('score',ascending=False).drop_duplicates('name').sort_values('date')

def rec(d):
    out=[];best=-1
    for _,r in d.sort_values('date').iterrows():
        if r.score>best: best=r.score; out.append((r.date,best,r['name']))
    return pd.DataFrame(out,columns=['date','score','name'])

def step(ax,df,color,label,lw=2.2,z=3):
    if len(df)==0: return
    x=list(df.date)+[pd.Timestamp('2026-09-08')]; y=list(df.score)+[df.score.iloc[-1]]
    ax.step(x,y,where='post',color=color,lw=lw,label=label,zorder=z)
    ax.scatter(df.date,df.score,color=color,s=22,zorder=z+1)

def lag_at(front, pt_date, pt_score):
    e=front[front.score>=pt_score]
    if len(e)==0: return None
    return (pt_date-e.date.iloc[0]).days/30.44

BENCH={'GPQA Diamond':'gpqa_diamond.csv','AIME':'otis_mock_aime_2024_2025.csv',
       'SciCode':'scicode_external.csv','FrontierMath (Tiers 1-3)':'frontiermath_tiers_1_3_v2.csv',
       'MMLU':'mmlu_external.csv','Terminal-Bench':'terminalbench_external.csv'}
DATA={k:load(v) for k,v in BENCH.items()}
CURVES={k:(rec(d[d.closed]),rec(d[d.open]),rec(d[d.open&(d.params<=40)])) for k,d in DATA.items()}

# ---------- Figure A: GPQA Diamond, annotated ----------
k='GPQA Diamond'; d=DATA[k]; fr,op,sm=CURVES[k]
fig,ax=plt.subplots(figsize=(10.6,4.75))
ax.scatter(d[d.closed].date,d[d.closed].score,s=14,color=GRAY,zorder=1)
ax.scatter(d[d.open].date,d[d.open].score,s=14,color=GRAY,zorder=1)
step(ax,fr,PLUM,'Best closed model (frontier)')
step(ax,op,BLUE,'Best open-weights model')
step(ax,sm,SAGE,'Best open model under 40B parameters')

# horizontal lag arrow at the current open record
cur=op.iloc[-1]; t0=fr[fr.score>=cur.score].date.iloc[0]
ax.annotate('', xy=(cur.date,cur.score), xytext=(t0,cur.score),
            arrowprops=dict(arrowstyle='<->',color=INK,lw=1.3))
ax.text(t0+(cur.date-t0)/2, cur.score+0.022, f'{(cur.date-t0).days/30.44:.0f} months',
        ha='center',fontsize=10,color=INK,fontweight='bold')
cs=sm.iloc[-1]; s0=fr[fr.score>=cs.score].date.iloc[0]
ax.annotate('', xy=(cs.date,cs.score), xytext=(s0,cs.score),
            arrowprops=dict(arrowstyle='<->',color=INK,lw=1.3))
ax.text(s0+(cs.date-s0)/2, cs.score+0.022, f'{(cs.date-s0).days/30.44:.0f} months',
        ha='center',fontsize=10,color=INK,fontweight='bold')

for _,r in fr.iterrows():
    if r['name'] in ('GPT-4','Claude 3 Opus','GPT-4o','o1','Gemini 2.5 Pro','GPT-5','GPT-6 Astra'):
        ax.annotate(r['name'],(r.date,r.score),textcoords='offset points',xytext=(-4,9),
                    fontsize=8.5,color=PLUM,ha='right')
for _,r in op.iterrows():
    if r['name'] in ('Llama 3.1-405B','DeepSeek-R1','Kimi K2 Thinking','Kimi K3'):
        ax.annotate(r['name'],(r.date,r.score),textcoords='offset points',xytext=(4,-14),
                    fontsize=8.5,color=BLUE)
ax.set_ylabel('GPQA Diamond accuracy'); ax.set_ylim(0,1.04)
ax.yaxis.set_major_formatter(lambda v,p: f'{v:.0%}')
ax.xaxis.set_major_locator(mdates.YearLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.set_xlim(pd.Timestamp('2023-01-01'),pd.Timestamp('2026-11-01'))
ax.legend(loc='lower right',frameon=False,fontsize=9.5)
fig.tight_layout(); fig.savefig('fig_gpqa.png',dpi=200,bbox_inches='tight',pad_inches=0.06); plt.close(fig)

# ---------- Figure B: four benchmarks ----------
picks=['GPQA Diamond','AIME','SciCode','FrontierMath (Tiers 1-3)']
fig,axes=plt.subplots(2,2,figsize=(11.5,5.0),sharex=True)
for ax,k in zip(axes.ravel(),picks):
    d=DATA[k]; fr,op,sm=CURVES[k]
    ax.scatter(d.date,d.score,s=8,color=GRAY,zorder=1)
    step(ax,fr,PLUM,None,lw=1.9); step(ax,op,BLUE,None,lw=1.9); step(ax,sm,SAGE,None,lw=1.9)
    ax.set_title(k,fontsize=10.5,color=INK,loc='left',pad=4)
    ax.set_ylim(0,1.04); ax.yaxis.set_major_formatter(lambda v,p: f'{v:.0%}')
    ax.xaxis.set_major_locator(mdates.YearLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.set_xlim(pd.Timestamp('2023-06-01'),pd.Timestamp('2026-11-01'))
h=[plt.Line2D([],[],color=c,lw=2.2) for c in (PLUM,BLUE,SAGE)]
fig.legend(h,['Best closed (frontier)','Best open weights','Best open under 40B'],
           loc='lower center',ncol=3,frameon=False,fontsize=9.5,bbox_to_anchor=(0.5,-0.015))
fig.tight_layout(rect=[0,0.055,1,1]); fig.savefig('fig_four.png',dpi=200,bbox_inches='tight',pad_inches=0.06); plt.close(fig)

# ---------- Figure C: the lag, in months ----------
rows=[]
for k in ['GPQA Diamond','AIME','SciCode','FrontierMath (Tiers 1-3)','Terminal-Bench','MMLU']:
    fr,op,sm=CURVES[k]
    lo=lag_at(fr,op.iloc[-1].date,op.iloc[-1].score) if len(op) else None
    ls=lag_at(fr,sm.iloc[-1].date,sm.iloc[-1].score) if len(sm) else None
    rows.append((k,lo,ls,op.iloc[-1].score if len(op) else np.nan,
                 sm.iloc[-1].score if len(sm) else np.nan, fr.iloc[-1].score))
L=pd.DataFrame(rows,columns=['bench','open_lag','small_lag','open_s','small_s','front_s'])
print(L.round(1).to_string(index=False))
L=L.iloc[::-1]
fig,ax=plt.subplots(figsize=(10.6,4.2))
y=np.arange(len(L)); h=0.36
ax.barh(y+h/2,L.open_lag,height=h,color=BLUE,label='Best open-weights model')
ax.barh(y-h/2,L.small_lag,height=h,color=SAGE,label='Best open model under 40B')
for yi,v in zip(y+h/2,L.open_lag):
    if pd.notna(v): ax.text(v+0.3,yi,f'{v:.0f}',va='center',fontsize=9.5,color=INK)
for yi,v in zip(y-h/2,L.small_lag):
    if pd.notna(v): ax.text(v+0.3,yi,f'{v:.0f}',va='center',fontsize=9.5,color=INK)
ax.set_yticks(y); ax.set_yticklabels(L.bench,fontsize=10)
ax.set_xlabel('Months behind the closed-model frontier')
ax.grid(axis='y',visible=False); ax.legend(frameon=False,fontsize=9.5,loc='lower right')
fig.tight_layout(); fig.savefig('fig_lag.png',dpi=200,bbox_inches='tight',pad_inches=0.06); plt.close(fig)

# score gaps table
print()
for k in BENCH:
    fr,op,sm=CURVES[k]
    print(f'{k:26s} frontier {fr.iloc[-1].score:.2f} ({fr.iloc[-1]["name"]}) | open {op.iloc[-1].score:.2f} ({op.iloc[-1]["name"]}) | small {sm.iloc[-1].score:.2f} ({sm.iloc[-1]["name"]})' if len(sm) else f'{k}: no small')
