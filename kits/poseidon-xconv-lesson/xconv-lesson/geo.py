F=lambda c:1+3*(c//8)+2+3*(c%8)+2
COL={7:(128,269,1600),6:(64,139,704),5:(32,34,304),4:(16,18,128),3:(8,10,52),2:(4,6,20),1:(2,5,11)}
oc=lambda nb:2*nb+6
def pcost(a,k,l0,cnt,tw1=True):
    nb,k0,kp=COL[k]; calls=1<<(a-k); x=calls*(oc(nb)+k0+kp*cnt+F(cnt)+3)+2
    if tw1: x-=(1<<l0)*(((1<<k)-1)*cnt-3)
    return x
def cost(split,a,cnt,tw1=True):
    c=0;l0=0
    for k in split: c+=pcost(a,k,l0,cnt,tw1); l0+=k
    return c
def runsplit(a,nl,cnt,tw1=True):
    best=[(0,[])]+[None]*nl
    for Lr in range(1,nl+1):
        for k in range(1,min(7,Lr)+1):
            v=best[Lr-k][0]+pcost(a,k,Lr-k,cnt,tw1)
            if best[Lr] is None or v<best[Lr][0]: best[Lr]=(v,best[Lr-k][1]+[k])
    return best[nl]
