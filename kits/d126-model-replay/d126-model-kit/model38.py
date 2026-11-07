# Selected historical arithmetic only; see README and PROVENANCE.
C = 2728
SR = 191773672732
F7 = 287309824
NB = 256
MASK_E17_BITS = 10
CNT17 = 1 << 20

def pre_ops(cs, p1, p2, ngw, lev):
    """Preprocessing in word operations: every term is (items) x (executed operations per item) + loop control."""
    W32 = 1 << 32
    t = {}
    t['P1_G'] = W32 * (p1['G_hit_ops'] + 3)
    if lev:
        t['P1_live'] = 32 * W32 * (p1['LIVE_ops'] + 3) + 32 * p1['LIVE_g']
    t['P2_F7'] = W32 * (p1['F7_in_ops'] + 3)
    t['P2_zero'] = 4 * ((1 << 34) + W32 + 2)
    t['P3_A2'] = W32 * (p1['A2_hit_ops'] + 3) + 768 * 4
    t['P4_rec'] = p1['A2REC_total_ops'] + p1['GREC_total_ops']
    t['P5_enum'] = NB * 768 * (p2['P5_SETUP'] + (1 << 29) * (p2['P5_BODY_MAX'] + p2['P5_LOOP'])) + SR * p2['P5_APPEND']
    t['P6_zero'] = NB * (1 << 64) * 4
    entries = SR * ngw * W32
    t['P6_count'] = SR * W32 * (p2['P6_COUNT'] + 3) + SR * 16
    t['P6_fill'] = SR * W32 * (p2['P6_FILL'] + 3) + SR * 16
    t['P6_prefix'] = NB * (1 << 64) * (p2['P6_PREFIX_EMPTY'] + 3) + min(entries, NB * (1 << 64)) * (p2['P6_PREFIX_NONEMPTY'] - p2['P6_PREFIX_EMPTY'])
    return t
