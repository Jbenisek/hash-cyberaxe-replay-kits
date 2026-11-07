# Selected historical arithmetic only; see README and PROVENANCE.
def ceil_frac(x):
    return (x.numerator + x.denominator - 1) // x.denominator

def lg(x):
    if isinstance(x, F):
        x = Decimal(x.numerator) / Decimal(x.denominator)
    else:
        x = Decimal(x)
    return x.ln() / Decimal(2).ln()

def r37_rows():
    p = os.path.join(ROOT, 'research/tools/build_pkg/scratch/pkgR37c/pkg/sha256-r37/experiments/xtab.py')
    m = load(p, 'xtab_d126')
    C = 2644
    BITS = m.PRE_ITEMS
    fixed_pre = sum(BITS[3:])
    x_pre = sum(BITS[:3])
    r16 = (1 << 34) * 32
    t0 = (1 << 32) * 8
    records = 15130951680 * 73024
    allow = F(2 ** 60 + 2 ** 50 + 2 ** 40)
    q3_log2 = m.Q3_LOG2
    fl = math.floor(q3_log2)
    q3ex = F(2) ** fl * F(math.floor(2 ** (q3_log2 - fl) * 2 ** 40), 2 ** 40)
    st = m.load_stats()
    nvar = sum((c[3] for c in m.CLASSES))
    g = nvar * F(68157440, 1 << 32) * F(287309824, 1 << 32)
    vbar = F(0)
    cls_cost = []
    cls_worst = []
    safety = m.STAT_SAFETY
    for ci, (_, _, _, n) in enumerate(m.CLASSES):
        n_, fb, bt, gr, pd = st[ci]
        assert n_ == n
        fb, bt, gr = (fb * safety, bt * safety, gr * safety)
        lanes = F(287309824, 1 << 32) * fb * (m.SCAN_LANE + 1 + m.SEG_OVH + m.LANE_UB[1])
        cls_cost.append(m.CLASS_OVH + (m.W6_OPS - 1) * bt + fb / 8 + F(23, 8) + lanes + F(287309824, 1 << 32) * gr * m.GROUP_OPS)
        nb = (n + 255) // 256
        ch = m.chunk_fixed_ops(256)
        cls_worst.append(m.CLASS_OVH + nb * (m.W6_OPS + 1 + ch) + n * (m.SCAN_LANE + 1 + m.SEG_OVH) + n * m.GROUP_OPS)
    pxub = F(16, 100)
    setup = pxub * (2 + m.ZPLANE_OPS + 1 + m.CVPRE_OPS)
    good = nvar * F(68157440, 1 << 32) * F(287309824, 1 << 32) * F(m.LANE_UB[0])
    c3b_pair = 201 + 23 + 1 + m.RARE_LOOKUP
    c3b_row = m.ROWCOMP + m.ROWCHECK + 1
    c3b_l = 2 + 6 + 2 * c3b_row
    rare = g * F(1052672, 1 << 32) * (c3b_pair + c3b_l + 19 * F(1, 512) * c3b_row)
    vbar = setup + F(68157440, 1 << 32) * sum(cls_cost) + good + rare
    vmax_fb = sum(cls_worst) + nvar * (m.LANE_UB[0] + m.LANE_UB[1] + 3 + c3b_pair + 32 * (c3b_l + 19 * c3b_row)) + 200 + 2 * m.ZPLANE_OPS
    slack = F(1, 2048)

    def mu_req(pcap):
        x = Decimal('0.61') - Decimal(pcap.numerator) / Decimal(pcap.denominator) - Decimal(2) ** (-60)
        d = Decimal(1) - (Decimal(-10.4) * Decimal(2).ln()).exp()
        mu = -x.ln() / d
        return F(int(math.floor(mu * 10 ** 8)) + 1, 10 ** 8)
    out = []
    for k in range(0, 33):
        shard = 1 << k
        pcap = F(1, 1 << 24)
        for _ in range(8):
            req = mu_req(pcap)
            nfb = ceil_frac(req / (g * 32 * q3ex / shard))
            pcap = F(vmax_fb, 1) / (slack * slack * nfb * vbar)
        vmax = ceil_frac((1 + slack) * nfb * vbar)
        pre = fixed_pre + sum((ceil_frac(F(v, shard)) for v in BITS[:3]))
        T = allow + F(nfb, 1) + F(nfb * m.FBFIX + vmax + ceil_frac(vmax_fb) + pre + 1600, C) + 6
        mem = (t0 + records) // shard + r16 + (1 << 33)
        out.append((k, nfb, T, mem, float(lg(T)), float(lg(mem))))
    return out

def r38_rows():
    """Header-shard trade model for the exact r38d ledger.

    This is a derived layout model: all 256 A0 blocks are still charged in
    the per-group sentinel pass, while stored header/table terms and their
    P6 preprocessing are divided among B=2^k shards.  It is not an unbuilt
    package claim.
    """
    p = os.path.join(ROOT, 'research/tools/build_pkg/scratch/pkgR38d/work/src/ledger38d.py')
    m = load(p, 'ledger38d_d126')
    cs = json.load(open(os.path.join(m.RUNS, 'costs.json')))
    p1 = json.load(open(os.path.join(m.RUNS, 'pre1.json')))
    p2 = json.load(open(os.path.join(m.RUNS, 'pre2.json')))
    C, SR, NB, ngw, W32 = (m.C, m.SR, m.NB, 22, 1 << 32)
    pf = F(m.F7, W32)
    ent = F(SR * ngw, W32)
    maxb = 14 * ngw * 768
    E = [3 * (ent + NB), ent * pf, ent * pf * F(1, 1 << m.MASK_E17_BITS), F(SR * pf * m.CNT17, 1 << 64)]
    caps0 = [3 * F(NB * (NB * maxb + NB), 1), F(NB * maxb), F(NB * maxb), F(NB * maxb)]
    per_group_fixed = cs['P0'] + cs['EPI'] + NB // 4 * (cs['GROUP4'] - 4 * cs['ITER'])
    cw = cs['PASS_ENTRY'] + cs['X_E17']
    c1 = cs['X_A17int'] - cs['X_E17']
    c2 = cs['X_SUCC'] - cs['X_A17int']
    fl = math.floor(-101.5)
    q3 = F(2) ** fl * F(math.floor(2 ** (-101.5 - fl) * 2 ** 40), 2 ** 40)
    S = F(SR) * pf * q3
    allow = F(2) ** 70 + F(2) ** 60 + F(2) ** 60
    init, fin_ops, fin_units = (1 << 32, 1024, 6)
    pre0 = m.pre_ops(cs, p1, p2, ngw, True)
    p6 = {'P6_zero', 'P6_count', 'P6_fill', 'P6_prefix'}
    pre_fixed = sum((v for key, v in pre0.items() if key not in p6))
    pre_shard = sum((pre0[key] for key in p6))
    table_words = NB * (1 << 64) + 3 * (SR * ngw * W32) + 3 * min(SR * ngw * W32, NB * (1 << 64))
    out = []
    for k in range(0, 46):
        B = 1 << k
        q_lb = S * F(1, B) * F(1, 2)
        Esh = [e / B for e in E]
        Be = F(NB * maxb, B)
        caps = [3 * (Be + F(NB, B)), Be, Be, Be]
        ptot = F(0)
        for _ in range(8):
            x = Decimal(1) - Decimal('0.39') - Decimal(ptot.numerator) / Decimal(ptot.denominator) - Decimal(2) ** (-60)
            mu = -x.ln()
            NG = int(-(-F(int(mu * 10 ** 30), 10 ** 30) // q_lb)) + 1
            ps = [F(caps[i], 1) / (F(1, 256) * NG * Esh[i]) for i in range(3)]
            ps.append(F(caps[3], 1) / (NG * Esh[3]))
            pn = sum(ps)
            if abs(pn - ptot) < F(1, 10 ** 12) * max(pn, F(1, 10 ** 12)):
                ptot = pn
                break
            ptot = pn
        NE = ceil_frac(F(NG) * Esh[0] * F(17, 16))
        NW = ceil_frac(F(NG) * Esh[1] * F(17, 16))
        N1 = ceil_frac(F(NG) * Esh[2] * F(17, 16))
        N2 = ceil_frac(F(NG) * Esh[3] * 2)
        online = NG * per_group_fixed + 2 * (NE + ceil_frac(caps[0])) + cw * (NW + ceil_frac(caps[1])) + c1 * (N1 + ceil_frac(caps[2])) + c2 * (N2 + ceil_frac(caps[3]))
        pre = pre_fixed + sum((ceil_frac(F(pre0[name], B)) for name in p6))
        T = allow + F(pre + init + online + fin_ops, C) + NG + fin_units
        words = ceil_frac(F(table_words, B)) + (1 << 33) + 3 * SR + 20000
        mem = words * 32
        out.append((k, NG, T, mem, float(lg(T)), float(lg(mem)), float(ptot)))
    return out
