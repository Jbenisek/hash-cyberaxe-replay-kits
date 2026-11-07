"""Finite arithmetic controls for the accompanying sparse-B proof.

This does NOT construct message schedules, compression collisions or prices.
The universal implication follows from the written recurrence proof.
"""
import json
import random
import hashlib
from pathlib import Path

THEOREM={'format':'hashsmash-sparse-b-lemma-v1','input_difference_words':[8,9,10,11,13,15],
         'expanded_difference_rows':[16,20,25,28,29],'last_schedule_row':39,
         'support_semantics':'exact, including nonzero W13 difference',
         'forced_top_bit_XOR_words':[13,20,29],'signed_orientation_fixed':False,
         'feasibility_proved':False,'attack_price_proved':False}


def main():
    if not __debug__:
        raise SystemExit('Run without -O')
    folder=Path(__file__).resolve().parent
    manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    expected_files={'replay.py','README.txt','PROOF.txt','theorem.json'}
    if set(manifest['files'])!=expected_files:
        raise ValueError('Wrong manifest inventory')
    for name,pin in manifest['files'].items():
        if hashlib.sha256((folder/name).read_bytes()).hexdigest()!=pin:
            raise ValueError('Changed kit member: '+name)
    if json.loads((folder/'theorem.json').read_text(encoding='utf-8'))!=THEOREM:
        raise ValueError('Theorem assumptions or conclusions changed')
    roots_checked=0
    for width in range(1,13):
        modulus=1<<width
        roots=[d for d in range(modulus) if (2*d)%modulus==0]
        if roots!=[0,modulus//2]:
            raise ValueError('Wrong roots')
        roots_checked+=modulus
    rng=random.Random(20261102)
    controls=0;orientation_controls=0
    for width in range(1,33):
        modulus=1<<width;mask=modulus-1;half=modulus//2
        for orientation in (0,1):
            for trial in range(16):
                a13=rng.randrange(half)|(orientation*half)
                b13=(a13+half)&mask
                common20=rng.randrange(modulus)
                common29=rng.randrange(modulus)
                common36=rng.randrange(modulus)
                a20=(common20+a13)&mask;b20=(common20+b13)&mask
                a29=(common29+a13)&mask;b29=(common29+b13)&mask
                a36=(common36+a20+a29)&mask;b36=(common36+b20+b29)&mask
                if a36!=b36 or any((a^b)!=half for a,b in ((a13,b13),(a20,b20),(a29,b29))):
                    raise ValueError('Cancellation or XOR implication failed')
                controls+=1
            orientation_controls+=1
    # Dropping the nonzero hypothesis gives an actual local equality-root case.
    a13=b13=0x12345678;mask=(1<<32)-1
    a20=(0xfedcba98+a13)&mask;b20=(0xfedcba98+b13)&mask
    a29=(0xdeadbeef+a13)&mask;b29=(0xdeadbeef+b13)&mask
    if (a20+a29)&mask!=(b20+b29)&mask or any(a^b for a,b in ((a13,b13),(a20,b20),(a29,b29))):
        raise ValueError('Trivial-root control failed')
    print(json.dumps({'passed':True,'root_residues_exhaustively_checked':roots_checked,
        'exhaustive_widths':list(range(1,13)),'local_recurrence_controls':controls,
        'orientation_width_combinations':orientation_controls,'trivial_root_retained_without_nonzero_assumption':True,
        'message_schedules_constructed':0,'collisions_checked':0,
        'scope':'Finite controls for modular cancellation and XOR top-bit conversion; not full schedules, feasibility evidence or an attack-price certificate.'},indent=2))


if __name__=='__main__':main()
