exec(open('figs.py').read().split('# ---------- Figure A')[0])
import matplotlib.patheffects as pe
HALO=[pe.withStroke(linewidth=3.2,foreground='white')]

def timeline(key,out,ylab,xstart,labs_f,labs_o,labs_s,callout,small_arrow=True,xend='2026-12-15',quarterly=False):
    d=DATA[key]; fr,op,sm=CURVES[key]
    fig,ax=plt.subplots(figsize=(11.5,4.5))
    ax.scatter(d.date,d.score,s=13,color=GRAY,zorder=1)
    step(ax,fr,PLUM,'Best closed model (the frontier)')
    step(ax,op,BLUE,'Best open-weights model')
    step(ax,sm,SAGE,'Best open model under 40B parameters')
    def arrow(pt,color):
        e=fr[fr.score>=pt.score]
        t0=e.date.iloc[0]
        ax.annotate('',xy=(pt.date,pt.score),xytext=(t0,pt.score),
                    arrowprops=dict(arrowstyle='<|-|>',color=color,lw=1.7,
                                    shrinkA=0,shrinkB=0,mutation_scale=13))
        return (pt.date-t0).days/30.44
    mo_o=arrow(op.iloc[-1],BLUE)
    mo_s=arrow(sm.iloc[-1],SAGE) if small_arrow else None
    cx,cy=callout['xy']
    ax.text(pd.Timestamp(cx),cy,callout['head'],fontsize=12,color=INK,fontweight='bold',va='top')
    ax.text(pd.Timestamp(cx),cy-0.065,callout['blue'].format(mo=mo_o),
            fontsize=11,color=BLUE,va='top',linespacing=1.35)
    ax.text(pd.Timestamp(cx),cy-0.205,callout['sage'],fontsize=11,color=SAGE,va='top',linespacing=1.35)
    for df,labs,col in ((fr,labs_f,PLUM),(op,labs_o,BLUE),(sm,labs_s,SAGE)):
        for _,r in df.iterrows():
            if r['name'] in labs:
                dx,dy,ha=labs[r['name']]
                ax.annotate(r['name'],(r.date,r.score),textcoords='offset points',xytext=(dx,dy),
                            fontsize=10,color=col,ha=ha,path_effects=HALO)
    ax.set_ylabel(ylab); ax.set_ylim(0,1.06)
    ax.yaxis.set_major_formatter(lambda v,p:f'{v:.0%}')
    if quarterly:
        ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1,4,7,10]))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    else:
        ax.xaxis.set_major_locator(mdates.YearLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.set_xlim(pd.Timestamp(xstart),pd.Timestamp(xend))
    ax.legend(loc='upper center',bbox_to_anchor=(0.5,-0.09),ncol=3,frameon=False,fontsize=11)
    fig.tight_layout(); fig.savefig(out,dpi=200,bbox_inches='tight',pad_inches=0.06); plt.close(fig)
    print(out,'open',round(mo_o,1),'small',None if mo_s is None else round(mo_s,1))

timeline('GPQA Diamond','fig_gpqa.png','GPQA Diamond accuracy','2023-01-01',
  {'o1':(-6,9,'right'),'GPT-6 Astra':(-3,11,'right')},
  {'Kimi K3':(-8,-25,'right')},
  {'Qwen3.6 27B':(4,-19,'left')},
  dict(xy=('2023-02-15',0.98), head='Reading the gap sideways',
       blue='Kimi K3 matches the closed frontier\nof {mo:.0f} months earlier',
       sage='Qwen3.6 27B, small enough for one\nGPU, matches it 9 months earlier'))

timeline('Terminal-Bench','fig_tbench.png','Terminal-Bench, tasks solved','2025-05-01',
  {'GPT-5.5':(-4,11,'right')},
  {'GLM-5':(-6,-21,'right')},
  {},
  dict(xy=('2025-05-20',1.03), head='The sideways reading runs out',
       blue='GLM-5 matches the closed frontier\nof {mo:.0f} months earlier',
       sage='The best model that fits on one GPU\nsolves 23% of tasks, against 85%'),
  small_arrow=False, xend='2026-09-30', quarterly=True)
