# Writes nldtool start files (sha2, w=32). Usage: python -I mkxml.py <outdir>
import sys, os
D = '-' * 32; Q = '?' * 32
SEARCH = '''<search reseed="600" credits="10000">
  <phase twobit_complete="1">
    <setting prob="5">
      <mask word="W"/>
      <guess condition="?" push_stack_prob="0" choice_prob="1"/>
      <guess condition="x" push_stack_prob="1" choice_prob="0.2"/>
    </setting>
    <setting prob="1">
      <mask word="E"/>
      <mask word="A"/>
      <guess condition="?" push_stack_prob="0" choice_prob="1"/>
      <guess condition="x" push_stack_prob="1" choice_prob="0.2"/>
    </setting>
  </phase>
</search>'''
def xml(n, comment, W, A_rows, E_rows, Ein=None):
    L = []
    for i in range(-4, 0):
        e = (Ein or {}).get(i, D)
        L.append(f"{i:3d} A: {D} E: {e}")
    for i in range(n):
        a = Q if i in A_rows else D
        e = Q if i in E_rows else D
        L.append(f"{i:3d} A: {a} E: {e} W: {W.get(i, D)}")
    return (f'<config>\n<options>\n  <option name="f" value="sha2"/>\n  <option name="n" value="{n}"/>\n'
            f'  <option name="w" value="32"/>\n</options>\n<comment>{comment}</comment>\n<char value="\n'
            + "\n".join(L) + '\n  "/>\n' + SEARCH + '\n</config>\n')
out = sys.argv[1]
# SHA-256: lightest join-16 support (G_r40_all_splits/ANSWER.md), whole words free '?', W39 forced '-' by n=40
S = [8, 9, 10, 11, 12, 16, 17, 24, 26]
for n in (40, 39):
    open(os.path.join(out, f"s256_r{n}_join16.xml"), "w").write(
        xml(n, f"SHA-256 {n} steps SFS, support {S} whole words free, state A8-18 E8-22 free",
            {**{i: Q for i in S}, 8: "x" + "?" * 31}, range(8, 19), range(8, 23)))
# SHA-224 control: Li-Liu-Wang 2024/349 signed dW rows (cloud_luna_audit_1021.md sec 1), E-4 bit 28 'u'
P = {0: "===n============================", 9: "===u============================",
     10: "======n===u==========u==========", 11: "===n============================",
     12: "=======nn=======n===n===nn==uu=u", 13: "=============u=======nn=========",
     17: "======n===u==========u==========", 18: "===n============================",
     25: "=======n=n=======n==============", 27: "===u============================"}
W = {i: s.replace("=", "-") for i, s in P.items()}
assert all(len(s) == 32 for s in W.values())
open(os.path.join(out, "s224_r40_LLW_control.xml"), "w").write(
    xml(40, "SHA-224 40 steps FS control, LLW 2024/349 signed dW pinned, state A9-19 E9-23 free",
        W, range(9, 20), range(9, 24), Ein={-4: "---u" + "-" * 28}))
# Reaction-graph stages (outside/reaction_graph_1021.md second note): row 24 (stage 1) and rows 24+26 (stage 2) forced to zero
# difference; the tool enforces the modular expansion, so dW8 (and dW10) must take the cancelling values themselves.
S1 = [8, 9, 10, 11, 12, 16, 17, 26]   # W24 '-'; n=40 -> W39 '-'
open(os.path.join(out, "s256_r40_stage1.xml"), "w").write(
    xml(40, f"SHA-256 40 steps SFS stage 1: support {S1}, W24 and W39 zero, rows 0-7 zero",
        {**{i: Q for i in S1}, 8: "x" + "?" * 31}, range(8, 19), range(8, 23)))
S2 = [8, 9, 10, 11, 12, 16, 17]       # W24, W26 '-'; n=43 -> W39..W42 '-'
open(os.path.join(out, "s256_r43_stage2.xml"), "w").write(
    xml(43, f"SHA-256 stage 2: support {S2}, W24 W26 and W39..W42 zero, rows 0-7 zero (n=43 window)",
        {**{i: Q for i in S2}, 8: "x" + "?" * 31}, range(8, 19), range(8, 23)))
# stage 2 at n = 40, 41, 42 (to locate the initial-check failure seen at n=43)
for n in (40, 41, 42):
    open(os.path.join(out, f"s256_r{n}_stage2.xml"), "w").write(
        xml(n, f"SHA-256 stage 2 at n={n}: support {S2}, W24 W26 zero",
            {**{i: Q for i in S2}, 8: "x" + "?" * 31}, range(8, 19), range(8, 23)))
# stage 2 pin check at n=40: the single forced 'x' (bit 31) moved to W9..W12, W8 fully free
for p in (9, 10, 11, 12):
    open(os.path.join(out, f"s256_r40_stage2_pin{p}.xml"), "w").write(
        xml(40, f"SHA-256 stage 2 n=40, pin x at W{p} bit 31", {**{i: Q for i in S2}, p: "x" + "?" * 31},
            range(8, 19), range(8, 23)))
# SHA-224 shape as SHA-256 SFS: LLW signed dW pinned, CV difference zero (E-4 '-'), full state zero at the end (no truncation)
open(os.path.join(out, "s256_r40_llwshape_a.xml"), "w").write(
    xml(40, "SHA-256 40 SFS, LLW signed dW pinned, CV diff zero, state A9-19 E9-23 free", W, range(9, 20), range(9, 24)))
open(os.path.join(out, "s256_r40_llwshape_b.xml"), "w").write(
    xml(40, "SHA-256 40 SFS, LLW signed dW pinned, CV diff zero, state A0-19 E0-23 free", W, range(0, 20), range(0, 24)))
Wc = {i: s for i, s in W.items() if i != 0}
open(os.path.join(out, "s256_r40_llwshape_c.xml"), "w").write(
    xml(40, "SHA-256 40 SFS, LLW signed dW pinned except W0 zero, CV diff zero, state A9-19 E9-23 free", Wc, range(9, 20), range(9, 24)))
# Release set (G_r40_backcut/ANSWER.md: every R in REL has XOR dimension 0); modular test on the full pool,
# which contains every smaller R: support (S u REL) minus {24,26}; W24 W26 W39..W42 zero (n=43); rows 0-7 zero
REL = [18, 19, 23, 25, 27, 28, 31, 32, 33]
SR = sorted(set([8, 9, 10, 11, 12, 16, 17]) | set(REL))
open(os.path.join(out, "s256_r43_release_full.xml"), "w").write(
    xml(43, f"SHA-256 release pool: support {SR}, W24 W26 W39..W42 zero, rows 0-7 zero",
        {**{i: Q for i in SR}, 8: "x" + "?" * 31}, range(8, 30), range(8, 34)))
# Ledger 10-21 14:14: the published SHA-224 40-step shape as a SHA-256 semi-free-start instance: same signed dW pinned,
# same free state rows, NO input chaining-value difference (Ein omitted); 256-bit output difference zero is the '-' tail.
open(os.path.join(out, "s256_r40_LLWshape_sfs.xml"), "w").write(
    xml(40, "SHA-256 40 steps SFS: LLW 2024/349 SHA-224 shape, signed dW pinned, zero chaining difference, state A9-19 E9-23 free",
        W, range(9, 20), range(9, 24)))
# Ledger 10-21 14:16: variants after the SFS instance failed the initial check (the input difference is load-bearing):
# (a) drop the W0 difference: support W9..W27 only, zero chaining difference (the blog's "cluster starts at W9" shape);
# (b) keep W0, let the input E-4 row be free ('?') so the tool chooses the chaining difference (free-start, shape rigidity test).
Wa = {i: s for i, s in W.items() if i != 0}
open(os.path.join(out, "s256_r40_LLWshape_sfs_noW0.xml"), "w").write(
    xml(40, "SHA-256 40 steps SFS: LLW shape without the W0 difference, zero chaining difference, state A9-19 E9-23 free",
        Wa, range(9, 20), range(9, 24)))
open(os.path.join(out, "s256_r40_LLWshape_fs_freeEin.xml"), "w").write(
    xml(40, "SHA-256 40 steps FS: LLW shape, input E-4 row free, state A9-19 E9-23 free",
        W, range(9, 20), range(9, 24), Ein={-4: "?" * 32}))
# Ledger 10-21 14:19: release-set instance from G_backcut_2 (weak kernel T={13,14}): message support W8..W14 free, W15 and all
# later message words zero; schedule words 24, 26 and 39..42 must be zero (n=43 window); state rows 8-18 / 8-22 free; signs chosen by the tool.
open(os.path.join(out, "s256_r43_release_T1314.xml"), "w").write(
    xml(43, "SHA-256 43-step window SFS: release set T={13,14}, support W8..W14 free, W24 W26 W39..W42 zero, rows 0-7 zero",
        {**{i: Q for i in range(8, 15)}, 8: "x" + "?" * 31}, range(8, 19), range(8, 23)))
# Ledger 10-21 14:22: the release instance with the forced bit on W8 bit 31 fails the initial check like stage 2 did; two variants:
# (c) force the nonzero bit in the middle of W11 instead; (d) no forced bit at all (every support word '?') to see whether the check passes.
open(os.path.join(out, "s256_r43_release_T1314_w11.xml"), "w").write(
    xml(43, "release T={13,14}: support W8..W14 free, forced nonzero bit at W11 bit 15, W24 W26 W39..W42 zero",
        {**{i: Q for i in range(8, 15)}, 11: "?" * 16 + "x" + "?" * 15}, range(8, 19), range(8, 23)))
open(os.path.join(out, "s256_r43_release_T1314_free.xml"), "w").write(
    xml(43, "release T={13,14}: support W8..W14 free, no forced bit, W24 W26 W39..W42 zero",
        {i: Q for i in range(8, 15)}, range(8, 19), range(8, 23)))
# Ledger 10-21 14:2x: pin the G_backcut_2 lightest T={13,14} vector (weight 66) as 'x' bits (signs free), W24 W26 W39..W42 zero, n=43.
def mrow(m): return "".join("x" if (m >> (31 - i)) & 1 else "-" for i in range(32))
M1314 = {8: 0x450258c0, 9: 0x42283180, 10: 0x681c8320, 11: 0x24ab7438, 12: 0x10208c48, 13: 0xf820001c, 14: 0x203401c7}
open(os.path.join(out, "s256_r43_release_T1314_pinned.xml"), "w").write(
    xml(43, "release T={13,14}: lightest XOR-kernel vector (weight 66) pinned as x bits on W8..W14, W24 W26 W39..W42 zero, rows 0-7 zero",
        {i: mrow(m) for i, m in M1314.items()}, range(8, 19), range(8, 23)))
# Ledger: the pinned T={13,14} vector fails the initial check; pin the T={13,15} (weight 64) and T={14,15} vectors likewise.
M1315 = {8: 0x22082a8c, 9: 0xa886805a, 10: 0x41081450, 11: 0x81600812, 12: 0xa10600f1, 13: 0x80210930, 15: 0x8c905ea4}
open(os.path.join(out, "s256_r43_release_T1315_pinned.xml"), "w").write(
    xml(43, "release T={13,15}: lightest XOR-kernel vector (weight 64) pinned as x bits on W8..W13,W15, W24 W26 W39..W42 zero",
        {i: mrow(m) for i, m in M1315.items()}, range(8, 19), range(8, 23)))
# Ledger: both pinned XOR vectors fail the first check; pin only W8's mask as x bits and leave W9..W14 free, so the tool must find signs/values itself.
open(os.path.join(out, "s256_r43_release_T1314_w8pin.xml"), "w").write(
    xml(43, "release T={13,14}: W8 pinned to the lightest vector's mask (x bits), W9..W14 free, W24 W26 W39..W42 zero",
        {**{i: Q for i in range(9, 15)}, 8: mrow(0x450258c0)}, range(8, 19), range(8, 23)))
# Ledger 10-21 CORRECTION: the release instances above force every non-support expanded word (16..42) to '-' (zero), but the kernel
# vectors have NONZERO expanded differences on 16..23, 25, 27..38; only 24, 26 and 39..42 must be zero. Rebuild with the expanded words free.
def relW(pins, free_words, zero_words, n):
    d = {}
    for i in range(16, n): d[i] = Q
    for i in zero_words: d[i] = D
    for i in free_words: d[i] = Q
    for i, m in pins.items(): d[i] = mrow(m)
    return d
ZERO = [24, 26, 39, 40, 41, 42]
open(os.path.join(out, "s256_r43_release_T1314_fix.xml"), "w").write(
    xml(43, "release T={13,14} FIXED: lightest vector pinned on W8..W14, expanded words 16..42 free except 24 26 39..42 zero",
        relW(M1314, [], ZERO, 43), range(8, 19), range(8, 23)))
open(os.path.join(out, "s256_r43_release_T1314_fix_w8.xml"), "w").write(
    xml(43, "release T={13,14} FIXED: W8 pinned, W9..W14 free, expanded words free except 24 26 39..42 zero",
        relW({8: 0x450258c0}, range(9, 15), ZERO, 43), range(8, 19), range(8, 23)))
# Ledger: second template error - A/E rows were free only through 18/22 while the pinned vector has nonzero expanded words through 38;
# free the state rows 8..42 entirely and let the tool decide where the state difference closes.
open(os.path.join(out, "s256_r43_release_T1314_fix2.xml"), "w").write(
    xml(43, "release T={13,14} FIX2: lightest vector pinned on W8..W14, expanded words free except 24 26 39..42 zero, state rows 8..42 free",
        relW(M1314, [], ZERO, 43), range(8, 43), range(8, 43)))
open(os.path.join(out, "s256_r43_release_T1314_fix2_w8.xml"), "w").write(
    xml(43, "release T={13,14} FIX2: W8 pinned, W9..W14 free, expanded words free except 24 26 39..42 zero, state rows 8..42 free",
        relW({8: 0x450258c0}, range(9, 15), ZERO, 43), range(8, 43), range(8, 43)))
# Ledger: FIX2-template instances for the other two release vectors (expanded words free except 24 26 39..42; state rows 8..42 free).
open(os.path.join(out, "s256_r43_release_T1315_fix2.xml"), "w").write(
    xml(43, "release T={13,15} FIX2: lightest vector pinned on W8..W13,W15, expanded words free except 24 26 39..42 zero, state rows 8..42 free",
        relW(M1315, [], ZERO, 43), range(8, 43), range(8, 43)))
M1415 = {8: 0xc0181471, 9: 0x3a994610, 10: 0x04b09185, 11: 0x201825c3, 12: 0xe4006311, 14: 0x80c00812, 15: 0x9c00200d}
open(os.path.join(out, "s256_r43_release_T1415_fix2.xml"), "w").write(
    xml(43, "release T={14,15} FIX2: lightest vector pinned on W8..W12,W14,W15, expanded words free except 24 26 39..42 zero, state rows 8..42 free",
        relW(M1415, [], ZERO, 43), range(8, 43), range(8, 43)))
# Ledger 10-21: two-block instances around the LLW control's chaining difference delta (E-4 = h word, bit 28, signed 'u').
# Output state after step 40: A36..A39 = d,c,b,a and E36..E39 = h,g,f,e, so delta's word h sits on row E36.
# B2: input E-4 = +delta, E36 = -delta (opposite sign, so h_in + h_state has zero modular difference), other output rows zero.
# B1: zero input (standard IV), E36 = +delta, other output rows zero. Message words and state rows 0..35 free in both.
def twoblock(n=40, bit=28):
    def row(c): return "-" * (31 - bit) + c + "-" * bit
    W = {i: Q for i in range(n)}
    A = range(0, n - 4); E = range(0, n - 4)
    def mk(comment, ein, eout):
        s = xml(n, comment, W, A, E, Ein=ein)
        return s.replace(f"{n-4:3d} A: {D} E: {D}", f"{n-4:3d} A: {D} E: {eout}")
    open(os.path.join(out, "s256_r40_twoblock_B2.xml"), "w").write(
        mk("SHA-256 40 steps two-block B2: CV diff +delta (E-4 bit 28 u), output E36 bit 28 n (-delta), other output rows zero, W free, state 0-35 free",
           {-4: row("u")}, row("n")))
    open(os.path.join(out, "s256_r40_twoblock_B1.xml"), "w").write(
        mk("SHA-256 40 steps two-block B1: standard IV (zero input diff), output E36 bit 28 u (+delta), other output rows zero, W free, state 0-35 free",
           None, row("u")))
if len(sys.argv) > 2 and sys.argv[2] == "twoblock": twoblock()
# Ledger 10-21 (twoblock_assembler RANK.tsv): two-block pairs for a chaining delta in e-side register r (e,f,g,h), bit j.
# Input row: e=E-1, f=E-2, g=E-3, h=E-4. Output row after 40 steps: e=E39, f=E38, g=E37, h=E36. Same signs as twoblock().
def twoblock_reg(reg, bit, n=40):
    def row(c): return "-" * (31 - bit) + c + "-" * bit
    ein = {"e": -1, "f": -2, "g": -3, "h": -4}[reg]
    eo = {"e": n - 1, "f": n - 2, "g": n - 3, "h": n - 4}[reg]
    W = {i: Q for i in range(n)}
    A = range(0, n - 4); E = range(0, n - 4)
    def mk(comment, ein_d, eout):
        s = xml(n, comment, W, A, E, Ein=ein_d)
        old = f"{eo:3d} A: {D} E: {D}"
        assert s.count(old) == 1
        return s.replace(old, f"{eo:3d} A: {D} E: {eout}")
    tag = f"{reg}{bit}"
    open(os.path.join(out, f"s256_r40_twoblock_B2_{tag}.xml"), "w").write(
        mk(f"SHA-256 40 steps two-block B2: CV diff +delta ({reg} = E{ein} bit {bit} u), output E{eo} bit {bit} n (-delta), other output rows zero, W free, state 0-35 free",
           {ein: row("u")}, row("n")))
    open(os.path.join(out, f"s256_r40_twoblock_B1_{tag}.xml"), "w").write(
        mk(f"SHA-256 40 steps two-block B1: standard IV (zero input diff), output E{eo} bit {bit} u (+delta), other output rows zero, W free, state 0-35 free",
           None, row("u")))
if len(sys.argv) > 2 and sys.argv[2] == "twoblock_reg":
    for d in sys.argv[3:]: twoblock_reg(d[0], int(d[1:]))
