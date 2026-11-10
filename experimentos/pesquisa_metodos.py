"""Testes da pesquisa de métodos (md/PESQUISA.md). Uso: python3 experimentos/pesquisa_metodos.py"""
import numpy as np, os, sys
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
def carregar(p):
    out=[]
    i=1
    while os.path.exists(f'{p}/observada_{i:02d}.npy'):
        out.append((np.load(f'{p}/observada_{i:02d}.npy'),np.load(f'{p}/mascara_{i:02d}.npy').astype(bool),np.load(f'{p}/gabarito_{i:02d}.npy')));i+=1
    return out
PUB=carregar('dados');SIN=carregar('dados_sinteticos')
tipos=[l.split()[1] for l in open('dados_sinteticos/tipos.txt')]
def nr(x,m,g): h=~m; return np.sqrt(np.mean((x[h]-g[h])**2))/g[h].std()

def medias(o,m):
    n,c=o.shape;ge=o[m].mean()
    mc=np.array([o[m[:,j],j].mean() if m[:,j].any() else ge for j in range(c)])
    nc=m.sum(0)
    r=o-mc;d=np.array([r[i,m[i]].mean() if m[i].any() else 0 for i in range(n)])
    return ge,mc,nc,d
def base_v3(o,m):
    ge,mc,nc,d=medias(o,m);return np.where(m,o,mc+d[:,None])
def js(o,m):
    # James-Stein: encolhe médias das colunas para a média geral
    ge,mc,nc,d=medias(o,m);c=o.shape[1]
    resid=np.where(m,o-mc,np.nan);s2=np.nanvar(resid)  # variância dentro da coluna
    v=s2/np.maximum(nc,1)                               # variância de cada média
    S=np.sum((mc-mc.mean())**2)
    B=max(0.0,1-(c-3)*v.mean()/S) if S>0 and c>3 else 0.0
    mcs=mc.mean()+B*(mc-mc.mean())
    r=o-mcs;dd=np.array([r[i,m[i]].mean() if m[i].any() else 0 for i in range(o.shape[0])])
    # encolhe também o desvio das linhas
    nl=m.sum(1);vl=s2/np.maximum(nl,1);Sl=np.sum(dd**2)
    Bl=max(0.0,1-(o.shape[0]-2)*vl.mean()/Sl) if Sl>0 and o.shape[0]>2 else 0.0
    return np.where(m,o,mcs[None,:]+Bl*dd[:,None])
def gd_rank(x):
    n,c=x.shape;b=min(n,c)/max(n,c);s=np.linalg.svd(x,compute_uv=False)
    w=0.56*b**3-0.95*b**2+1.82*b+1.43   # aproximação de Gavish-Donoho, ruído desconhecido
    return int((s>w*np.median(s)).sum())
def hard(o,m,k,x,it=200):
    for _ in range(it):
        u,s,vt=np.linalg.svd(x,full_matrices=False);x=np.where(m,o,(u[:,:k]*s[:k])@vt[:k])
    return x
def hard_gd(o,m):
    x=base_v3(o,m);ge,mc,_,_=medias(o,m)
    k=max(0,gd_rank(x-mc))
    # reavalia rank após uma rodada
    if k==0: return x
    x=hard(o,m,k,x);k2=max(1,gd_rank(x-mc));return hard(o,m,k2,x)
def rpca(o,m):
    # PCA iterativa regularizada (Josse & Husson): s_k -> s_k - sigma^2/s_k
    ge,mc,_,_=medias(o,m);x=base_v3(o,m)
    n,c=o.shape;k=max(1,gd_rank(x-mc))
    for _ in range(200):
        mu=x.mean(0);u,s,vt=np.linalg.svd(x-mu,full_matrices=False)
        nm=(~m).sum()
        den=max(n*c-nm-(n+c)*k+k*k-c,1)
        sig2=np.sum(s[k:]**2)/den
        ss=np.maximum(s[:k]-sig2/s[:k],0)
        x=np.where(m,o,mu+(u[:,:k]*ss)@vt[:k])
    return x
def knn(o,m,K=5):
    x=base_v3(o,m);n=o.shape[0];out=x.copy()
    for i in range(n):
        if m[i].all(): continue
        d=[]
        for j in range(n):
            if j==i: continue
            cm=m[i]&m[j]
            d.append(np.sqrt(np.mean((o[i,cm]-o[j,cm])**2)) if cm.sum()>=2 else np.inf)
        d=np.array(d);idx=[j for j in range(n) if j!=i];ordem=np.argsort(d)[:K]
        viz=np.array([idx[t] for t in ordem]);w=1/(d[ordem]+1e-9)
        # usa resíduo em relação à coluna para comparar linhas de níveis diferentes
        ge,mc,_,dl=medias(o,m)
        est=mc+dl[i]+np.sum(w[:,None]*(x[viz]-mc-dl[viz][:,None]),0)/w.sum()
        out[i]=np.where(m[i],o[i],est)
    return out
def lls(o,m,K=8):
    # Local least squares: regride a linha i nas K linhas mais correlacionadas
    x=base_v3(o,m);n=o.shape[0];out=x.copy()
    for i in range(n):
        if m[i].all(): continue
        cor=np.array([abs(np.corrcoef(x[i,m[i]],x[j,m[i]])[0,1]) if j!=i and m[i].sum()>2 else -1 for j in range(n)])
        cor=np.nan_to_num(cor,nan=-1);viz=np.argsort(-cor)[:K]
        A=x[viz][:,m[i]].T;bvec=o[i,m[i]]
        A1=np.c_[A,np.ones(len(A))]
        coef=np.linalg.lstsq(A1.T@A1+1e-1*np.eye(A1.shape[1]),A1.T@bvec,rcond=None)[0]
        est=np.c_[x[viz].T,np.ones(o.shape[1])]@coef
        out[i]=np.where(m[i],o[i],est)
    return out
import importlib.util
spec=importlib.util.spec_from_file_location('v5','versoes/v5_candidatos.py');v5=importlib.util.module_from_spec(spec);spec.loader.exec_module(v5)
metodos={'v5 (atual)':v5.principal,'médias v3':base_v3,'James-Stein':js,'Hard + rank Gavish-Donoho':hard_gd,'PCA regularizada (Josse)':rpca,'KNN linhas':knn,'LLS':lls}
print(f"{'método':<28}{'público':>9}{'sintét.':>9}{'rank b.':>9}{'ruído':>9}{'col.c.':>9}{'juntos':>9}")
for nome,f in metodos.items():
    ep=[nr(np.asarray(f(o,m)),m,g) for o,m,g in PUB]
    es=[nr(np.asarray(f(o,m)),m,g) for o,m,g in SIN]
    t=np.array(tipos);es=np.array(es)
    rb=es[np.char.startswith(t,'rank')].mean();rp=es[t=='ruido_puro'].mean();cc=es[t=='colunas_constantes'].mean()
    print(f"{nome:<28}{np.mean(ep):9.4f}{es.mean():9.4f}{rb:9.4f}{rp:9.4f}{cc:9.4f}{np.mean(list(ep)+list(es)):9.4f}")
    if nome!='v5 (atual)': print('   público por matriz:',np.round(ep,3))
