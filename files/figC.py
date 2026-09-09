exec(open('figs.py').read().split('# ---------- Figure A')[0])
meta2=pd.read_csv('epoch/model_metadata.csv').dropna(subset=['model_group']).drop_duplicates('model_group')
ORGOF=dict(zip(meta2.model_group,meta2.organization))
ORGC={'OpenAI':'#595460','Anthropic':'#a8894e','Moonshot':'#6f8497','DeepSeek':'#7f9068',
      'Z.ai (Zhipu AI)':'#4f8079','Alibaba':'#a2695f'}
SHORT={'Z.ai (Zhipu AI)':'Z.ai'}
TIER={'frontier':'closed','open':'open weights','small':'open, under 40B'}

order=['GPQA Diamond','Terminal-Bench']
blocks=[]
for k in order:
    fr,op,sm=CURVES[k]
    # a lag is censored when the frontier's matching record is the first point in the
    # series -- the frontier was already above that score before the benchmark existed
    cens=lambda v: len(fr[fr.score>=v])>0 and fr[fr.score>=v].index[0]==fr.index[0]
    blocks.append((k,[
        ('frontier',fr.iloc[-1]['name'],fr.iloc[-1].score,None,False),
        ('open',op.iloc[-1]['name'],op.iloc[-1].score,lag_at(fr,op.iloc[-1].date,op.iloc[-1].score),cens(op.iloc[-1].score)),
        ('small',sm.iloc[-1]['name'],sm.iloc[-1].score,lag_at(fr,sm.iloc[-1].date,sm.iloc[-1].score),cens(sm.iloc[-1].score))]))

# y layout, top to bottom
ys=[]; ticks=[]; labels=[]; headers=[]; y=0.0
for k,pts in blocks:
    headers.append((y,k)); y-=0.80
    for p in pts:
        ys.append((y,p)); ticks.append(y); labels.append(p[1]); y-=0.70
    y-=0.42

fig,ax=plt.subplots(figsize=(9.0,2.45))
used=[]
for yy,(tier,name,score,lag,censored) in ys:
    org=ORGOF.get(name,'Alibaba'); c=ORGC.get(org,'#888'); used.append(org)
    ax.plot([0,score],[yy,yy],color='#e4e6e4',lw=2.6,zorder=1,solid_capstyle='butt')
    ax.scatter([score],[yy],s=150,color=c,zorder=3,edgecolor='white',linewidth=1.2)
    txt=f'{score:.0%}' if lag is None else f'{score:.0%}   {lag:.0f}{"+" if censored else ""} mo behind'
    ax.text(score+0.018,yy,txt,va='center',fontsize=10.5,color=c,fontweight='bold')
    ax.text(-0.98,yy,TIER[tier],va='center',ha='left',fontsize=9.5,color='#8b8d8b')
    ax.text(-0.62,yy,f'{name}  ({SHORT.get(org,org)})',va='center',ha='left',fontsize=11,color=c)
for yy,k in headers:
    ax.text(-0.98,yy,k,va='center',ha='left',fontsize=12,color='#3b3842',fontweight='bold')

ax.set_yticks([])
ax.set_ylim(min(ticks)-0.7,0.7)
ax.set_xlim(-0.98,1.30)
ax.set_xticks([0,.2,.4,.6,.8,1.0]); ax.xaxis.set_major_formatter(lambda v,p:f'{v:.0%}')
ax.set_xlabel('Best score in each tier, September 2026.   "Behind" is how long ago the closed frontier was at that score.\n'
              'Under 40B parameters is what a 32 GB consumer GPU holds at 4-bit; a 128 GB Mac holds several times more.',
              fontsize=10.5, color='#6b6d6b')
ax.grid(axis='y',visible=False); ax.tick_params(axis='y',length=0)
ax.spines['left'].set_visible(False)
fig.tight_layout()
fig.savefig('fig_gap.png',dpi=200,bbox_inches='tight',pad_inches=0.06)
plt.close(fig)
from PIL import Image
im=Image.open('fig_gap.png'); print(im.size, round(im.size[0]/im.size[1],2))
