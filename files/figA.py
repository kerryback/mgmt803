exec(open('figs.py').read().split('# ---------- Figure A')[0])
import matplotlib.patheffects as pe
HALO=[pe.withStroke(linewidth=3.2,foreground='white')]

k='GPQA Diamond'; d=DATA[k]; fr,op,sm=CURVES[k]
fig,ax=plt.subplots(figsize=(11.5,4.4))
ax.scatter(d.date,d.score,s=13,color=GRAY,zorder=1)
step(ax,fr,PLUM,'Best closed model (the frontier)')
step(ax,op,BLUE,'Best open-weights model')
step(ax,sm,SAGE,'Best open model under 40B parameters')

def arrow(pt,color):
    t0=fr[fr.score>=pt.score].date.iloc[0]
    ax.annotate('',xy=(pt.date,pt.score),xytext=(t0,pt.score),
                arrowprops=dict(arrowstyle='<|-|>',color=color,lw=1.7,
                                shrinkA=0,shrinkB=0,mutation_scale=13))
    return (pt.date-t0).days/30.44, pt['name']
mo_o,nm_o = arrow(op.iloc[-1],BLUE)
mo_s,nm_s = arrow(sm.iloc[-1],SAGE)

# callout block in the empty upper-left
ax.text(pd.Timestamp('2023-02-15'),0.98,'Reading the gap sideways',
        fontsize=12,color=INK,fontweight='bold',va='top')
ax.text(pd.Timestamp('2023-02-15'),0.915,
        f'{nm_o} matches the closed frontier\nof {mo_o:.0f} months earlier',
        fontsize=11,color=BLUE,va='top',linespacing=1.35)
ax.text(pd.Timestamp('2023-02-15'),0.775,
        f'{nm_s}, small enough for one\nGPU, matches it {mo_s:.0f} months earlier',
        fontsize=11,color=SAGE,va='top',linespacing=1.35)

LAB={'o1':(PLUM,-6,9,'right'),'GPT-6 Astra':(-2,0,0,0),
     'Kimi K3':(BLUE,-6,-21,'right'),'Qwen3.6 27B':(SAGE,4,-18,'left')}
for df in (fr,op,sm):
    for _,r in df.iterrows():
        if r['name'] in LAB and r['name']!='GPT-6 Astra':
            col,dx,dy,ha=LAB[r['name']]
            ax.annotate(r['name'],(r.date,r.score),textcoords='offset points',xytext=(dx,dy),
                        fontsize=10,color=col,ha=ha,path_effects=HALO)
g=fr.iloc[-1]
ax.annotate('GPT-6 Astra',(g.date,g.score),textcoords='offset points',xytext=(-3,11),
            fontsize=10,color=PLUM,ha='right',path_effects=HALO)

ax.set_ylabel('GPQA Diamond accuracy'); ax.set_ylim(0,1.06)
ax.yaxis.set_major_formatter(lambda v,p: f'{v:.0%}')
ax.xaxis.set_major_locator(mdates.YearLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.set_xlim(pd.Timestamp('2023-01-01'),pd.Timestamp('2026-12-15'))
ax.legend(loc='lower right',frameon=False,fontsize=11)
fig.tight_layout(); fig.savefig('fig_gpqa.png',dpi=200,bbox_inches='tight',pad_inches=0.06); plt.close(fig)
print('ok', mo_o, mo_s)
