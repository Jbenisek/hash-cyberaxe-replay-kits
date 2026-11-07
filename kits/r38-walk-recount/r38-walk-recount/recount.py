"""Independent exact-rational recount, with inherited trial count held explicit."""
from datetime import datetime, timezone
from decimal import Decimal, localcontext, ROUND_FLOOR, ROUND_CEILING
from fractions import Fraction as F
import json
from pathlib import Path

PUB=Path(__file__).resolve().parents[1]
NCV=1095091666191254369080
C=2728

def ceil(x):
    return -(-x.numerator//x.denominator)

def integer_ledger(walk):
    """All probabilities here are inherited ledger coefficients, not fresh laws."""
    na=2**20
    p12=F(53096854,2**32)
    p12g=F(2051404269120,na*2**32)
    q_hi=p12g*F(12136,100000)
    probe=14+12+19*2+F(20*195,125)*8
    claw=(walk+2+16+8*24*p12+8*28*p12g+8*q_hi*3014)/8
    per_a0=F(235,256)+F(250,8192)*(20+21+probe)+F(160*44543396,2**32)*claw
    wbar=C+3+F(76+1024+na*per_a0,64)
    build=6+(15*2**19)*5+2**32*17+44543396*22+(120*2**19-44543396)*9
    a0max=F(228,256)+20+21+14+12+19*2+40*(8+walk)+40*6*(2+16+24+28+3014)+F(7,256)
    vmax=int(C+3+76+1024+na*a0max)
    epochs=ceil(F(NCV,2**26))
    vcv=ceil((1+F(1,2**16))*NCV*wbar)
    allowance=3*2**70*C
    overshoot=max(vmax,build)
    final=6*C+1600
    total=allowance+epochs*build+vcv+overshoot+final
    return {'WALK':walk,'per_a0':str(per_a0),'wbar':str(wbar),
            'first_blocks':NCV,'epochs':epochs,'build_per_epoch':build,
            'online_charge':vcv,'vmax':vmax,'preprocessing_word_operations':allowance,
            'overshoot':overshoot,'final_check':final,'N':total}

def log2_enclosure(n,d,places=7):
    """Decimal ln is correctly rounded; adjacent decimals enclose each exact ln.
    Directed division of those positive enclosures gives a conservative bound.
    This certifies rounding for this rational ratio, not its scientific premise.
    """
    with localcontext() as context:
        context.prec=100
        context.rounding=ROUND_FLOOR
        lo=Decimal(n)/Decimal(d)
        context.rounding=ROUND_CEILING
        hi=Decimal(n)/Decimal(d)
        lnlo=lo.ln().next_minus()
        lnhi=hi.ln().next_plus()
        ln2=Decimal(2).ln()
        divisorlo,divisorhi=ln2.next_minus(),ln2.next_plus()
        assert lnlo>0 and divisorlo>0
        context.rounding=ROUND_FLOOR
        lower=lnlo/divisorhi
        context.rounding=ROUND_CEILING
        upper=lnhi/divisorlo
        quantum=Decimal(1).scaleb(-places)
        rounded=upper.quantize(quantum,rounding=ROUND_CEILING)
        assert lower.quantize(quantum,rounding=ROUND_CEILING)==rounded
        return {'lower':str(lower),'upper':str(upper),'rounded_up':str(rounded),'decimal_places':places}

def main():
    prior=json.loads((PUB/'qa/r38-walk-conditional-recount.json').read_text())
    assert prior['passed'] and prior['guard_patterns_exhausted']==64
    rows=[]
    for inherited in prior['rows']:
        row=integer_ledger(inherited['walk_operations'])
        assert row['N']==int(inherited['N_word_operations'])
        assert row['first_blocks']==int(inherited['first_blocks'])
        row['time_log2']=log2_enclosure(row['N'],C)
        with localcontext() as context:
            context.prec=110
            score_lo=Decimal(row['time_log2']['lower'])+Decimal('7.916207')
            score_hi=Decimal(row['time_log2']['upper'])+Decimal('7.916207')
            upper=score_hi.quantize(Decimal('0.0000001'),rounding=ROUND_CEILING)
            assert score_lo.quantize(Decimal('0.0000001'),rounding=ROUND_CEILING)==upper
            row['score_given_memory_log2_27_916207']={'lower':str(score_lo),'upper':str(score_hi),'rounded_up':str(upper)}
        rows.append(row)
    baseline,nextrow=rows[:2]
    saved=baseline['N']-nextrow['N']
    report={'passed':True,'finished_at':datetime.now(timezone.utc).isoformat(),
            'rows':rows,'compression_price':C,'inherited_first_block_budget':NCV,
            'saving':{'word_operations':saved,'fraction':str(F(saved,baseline['N'])),
                      'bits':log2_enclosure(baseline['N'],nextrow['N'])},
            'exact_integer_rows_matching_source':len(rows),
            'scope':'Independent rational reconstruction and certified displayed rounding under a fixed inherited budget. Not a proof of ctz pricing, success law, implementation completeness or memory bound.',
            'memory_premise':'27.916207 is an inherited declared log2 memory term, not a fresh exact memory measurement.'}
    (PUB/'qa/r38-walk-exact-recount.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='rows'},indent=2))
    print(json.dumps([{'walk':r['WALK'],'N':r['N'],'time_up':r['time_log2']['rounded_up'],'score_up':r['score_given_memory_log2_27_916207']['rounded_up']} for r in rows],indent=2))

if __name__=='__main__':
    main()
