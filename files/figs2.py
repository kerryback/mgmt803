exec(open('figs.py').read().split('# ---------- Figure A')[0])
import matplotlib.patheffects as pe

# ---------- Figure A: GPQA Diamond, annotated ----------
k='GPQA Diamond'; d=DATA[k]; fr,op,sm=CURVES[k]
fig,ax=plt.subplots(figsize=(10.6,4.75))
ax.scatter(d.date,d.score,s=13,color=GRAY,zorder=1)
step(ax,fr,PLUM,'Best closed model (the frontier)')
step(ax,op,BLUE,'Best open-weights model')
step(ax,sm,SAGE,'Best open model under 40B parameters')

def arrow(pt,color,dy):
    t0=fr[fr.score>=pt.score].date.iloc[0]
    ax.annotate('',xy=(pt.date,pt.score),xytext=(t0,pt.score),
                arrowprops=dict(arrowstyle='<|-|>',color=color,lw=1.6,
                                shrinkA=0,shrinkB=0,mutation_scale=12))
    mid=t0+(pt.date-t0)/2
    ax.text(mid,pt.score+dy,f'{(pt.date-t0).days/30.44:.0f} months behind',
            ha='center',va='bottom',fontsize=9.5,color=color,fontweight='bold',
            path_effects=[pe.withStroke(linewidth=3.5,foreground='white')])
arrow(op.iloc[-1],BLUE,0.018)
arrow(sm.iloc[-1],SAGE,-0.075)

LAB_F={'GPT-4':(-6,10,'right'),'Claude 3 Opus':(-6,10,'right'),'o1':(-6,10,'right'),
       'Gemini 2.5 Pro':(-6,10,'right'),'GPT-6 Astra':(-2,12,'right')}
LAB_O={'Llama 3.1-405B':(6,-16,'left'),'DeepSeek-R1':(6,-16,'left'),'Kimi K3':(6,4,'left')}
LAB_S={'Qwen3-32B':(4,-17,'left'),'Qwen3.6 27B':(6,-15,'left')}
for df,labs,col in ((fr,LAB_F,PLUM),(op,LAB_O,BLUE),(sm,LAB_S,SAGE)):
    for _,r in df.iterrows():
        if r['name'] in labs:
            dx,dy,ha=labs[r['name']]
            ax.annotate(r['name'],(r.date,r.score),textcoords='offset points',xytext=(dx,dy),
                        fontsize=8.5,color=col,ha=ha,
                        path_effects=[pe.withStroke(linewidth=3,foreground='white')])
ax.set_ylabel('GPQA Diamond accuracy'); ax.set_ylim(0,1.06)
ax.yaxis.set_major_formatter(lambda v,p: f'{v:.0%}')
ax.xaxis.set_major_locator(mdates.YearLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
ax.set_xlim(pd.Timestamp('2023-01-01'),pd.Timestamp('2026-12-15'))
ax.legend(loc='lower right',frameon=False,fontsize=9.5)
fig.tight_layout(); fig.savefig('fig_gpqa.png',dpi=200,bbox_inches='tight',pad_inches=0.06); plt.close(fig)

# ---------- Figure C: where each tier stands today ----------
order=['GPQA Diamond','AIME','SciCode','FrontierMath (Tiers 1-3)','Terminal-Bench']
rows=[]
for k in order:
    fr,op,sm=CURVES[k]
    rows.append(dict(bench=k, front=fr.iloc[-1].score, open=op.iloc[-1].score, small=sm.iloc[-1].score,
                     olag=lag_at(fr,op.iloc[-1].date,op.iloc[-1].score),
                     slag=lag_at(fr,sm.iloc[-1].date,sm.iloc[-1].score)))
G=pd.DataFrame(rows).iloc[::-1].reset_index(drop=True)
fig,ax=plt.subplots(figsize=(11.5,4.3))
y=np.arange(len(G))
for i,r in G.iterrows():
    ax.plot([r.small,r.front],[i,i],color='#d7dad7',lw=3,zorder=1,solid_capstyle='round')
ax.scatter(G.front,y,s=95,color=PLUM,zorder=3,label='Best closed model')
ax.scatter(G['open'],y,s=95,color=BLUE,zorder=3,label='Best open weights')
ax.scatter(G.small,y,s=95,color=SAGE,zorder=3,label='Best open under 40B')
for i,r in G.iterrows():
    ax.text(1.045,i+0.13,f'{r.olag:.0f} mo',color=BLUE,fontsize=11,va='center',fontweight='bold')
    ax.text(1.045,i-0.19,f'{r.slag:.0f} mo',color=SAGE,fontsize=11,va='center',fontweight='bold')
ax.text(1.045,len(G)-0.42,'behind',color=INK,fontsize=10,va='center')
ax.set_yticks(y); ax.set_yticklabels(G.bench,fontsize=12)
ax.set_xlim(0,1.0); ax.set_xlabel('Score, best model in each tier as of September 2026')
ax.xaxis.set_major_formatter(lambda v,p: f'{v:.0%}')
ax.grid(axis='y',visible=False)
ax.legend(loc='lower left',frameon=False,fontsize=9.5,ncol=3,bbox_to_anchor=(0,-0.34))
fig.tight_layout(rect=[0,0.04,0.93,1]); fig.savefig('fig_gap.png',dpi=200,bbox_inches='tight',pad_inches=0.06); plt.close(fig)
print(G.round(2).to_string(index=False))
