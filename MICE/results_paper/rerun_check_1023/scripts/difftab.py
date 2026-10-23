import re,glob,os,sys
L,W=sys.argv[1],sys.argv[2]
def cells(p):
    t=open(p).read()
    t=re.sub(r"\\(first|second|third|textbf|underline)\{([^{}]*)\}",r"\2",t).replace("$-$","-").replace("$","")
    return [[c.strip() for c in r.split("&")] for r in t.split("\\\\") if "&" in r]
def num(c):
    c=c.replace(",","").replace("%","").replace("{","").replace("}","")
    return float(c) if re.fullmatch(r"[+-]?\d+(\.\d+)?",c) else None
for g in sorted(glob.glob(f"{W}/MICE/overleaf/*/tab_*_rows.tex")):
    b=os.path.basename(g); p=f"{L}/{b}"
    if not os.path.exists(p): print(f"{b:26s} not in latest/"); continue
    A,B=cells(p),cells(g)
    if len(A)!=len(B): print(f"{b:26s} row count {len(A)} vs {len(B)}"); continue
    n=ch=0; mx=0; ex=[]
    for ra,rb in zip(A,B):
        for j,(ca,cb) in enumerate(zip(ra,rb)):
            x,y=num(ca),num(cb)
            if x is None or y is None:
                if ca!=cb: ch+=1; ex.append((ra[0],j,ca,cb))
                continue
            n+=1
            if ca!=cb:
                ch+=1; ex.append((ra[0][:22],j,ca,cb)); mx=max(mx,abs(x-y))
    ex.sort(key=lambda e: -abs((num(e[2]) or 0)-(num(e[3]) or 0)))
    print(f"{b:26s} cells {n:4d} changed {ch:3d} max {mx:.2f}  top: {ex[:3]}")
