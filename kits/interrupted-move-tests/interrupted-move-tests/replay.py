"""Reconstruct six historical rows; never import/run their research tools."""
import hashlib
import json
import re
import sys
from pathlib import Path

BASE=Path(__file__).resolve().parent
SOURCE='originals/TRICKS_RESULTS_1101.md'
SOURCE_PIN='41dce1c89b095f2fc601b988ac2a2fe8fa812a4162a4187be161ccb22edc6345'

CURATION={
    'T1':{
        'reader_group':'core',
        'status':'NO_COMPLETION_WITHIN_REPORTED_CAP',
        'reported_facts':{'search_trials':3,'search_cap_seconds_each':180,'baseline_seconds':'276','value_checks_UNKNOWN':2,'value_duration_seconds_reported':'119.6'},
        'qualification':'The source says WORSE, but capped non-completions and one reported baseline time do not certify an algorithmic cost ratio or a distributional ranking.'},
    'T2':{
        'reader_group':'tunnel',
        'status':'INTERRUPTED_NOT_A_VERDICT',
        'reported_facts':{'started_lanes':2,'planned_lanes':16,'interrupt_seconds_approx':18,'final_verdicts_reported':0},
        'qualification':'Only two lanes started and both were interrupted. A launch/reproduction control is not a negative verdict on the construction. Match any later completion by exact instance identity.'},
    'T3':{
        'reader_group':'core',
        'status':'MAP_WITHOUT_COMPLETED_WORK_IN',
        'reported_facts':{'map_probes':18,'map_cap_seconds':20,'completed_work_in_reported':False},
        'qualification':'A core-map observation is not a minimum-core proof. Read this note with the later p9 FREED-column, EQLINK and UNKNOWN-deletion corrections; no individual formula is reclassified here.'},
    'T4':{
        'reader_group':'junction',
        'status':'INTERRUPTED_NOT_A_VERDICT',
        'reported_facts':{'started_lanes':2,'planned_lanes':14,'interrupt_seconds_approx':13,'final_verdicts_reported':0},
        'qualification':'An interrupted partial junction sweep does not show that all planned junctions fail. This account does not claim that later team work never completed them.'},
    'T5':{
        'reader_group':'core',
        'status':'UNKNOWN_NOT_SAT',
        'reported_facts':{'UNKNOWN_results':16,'cap_seconds':60,'multi_block_necessity_proved':False},
        'qualification':'UNKNOWN at a time cap does not prove any single-block formula SAT. The note therefore does not establish that a contradiction requires multiple blocks. Conflict-count gradients are descriptive, not SAT/UNSAT or necessity certificates.'},
    'T6':{
        'reader_group':'rotation',
        'status':'REPORTED_UNSAT_SUBSET_NOT_GENERAL_BARRIER',
        'reported_facts':{'rotations_with_reported_UNSAT':31,'unresolved_rotation':0,'elapsed_seconds_range_reported':['0.6','0.7'],'conflicts_reported':0},
        'qualification':'These are recorded outcomes under one pinned door setup, not freshly replayed proofs or a theorem that rotation can never help another construction.'},
}


def digest(raw):return hashlib.sha256(raw).hexdigest()


def reconstruct():
    raw=(BASE/SOURCE).read_bytes()
    if digest(raw)!=SOURCE_PIN:raise ValueError('Original report edition changed')
    text=raw.decode('utf-8-sig');rows=[]
    for line_no,line in enumerate(text.splitlines(),1):
        if not re.match(r'^\| T[1-6] ',line):continue
        cells=[part.strip() for part in line.split('|')[1:-1]]
        if len(cells)!=3:raise ValueError('Unexpected table width')
        ident=cells[0].split()[0]
        rows.append({'id':ident,'source_line':line_no,
                     'recorded_test':cells[0],'recorded_move':cells[1],
                     'recorded_comparison':cells[2],**CURATION[ident]})
    if [r['id'] for r in rows]!=['T1','T2','T3','T4','T5','T6']:
        raise ValueError('Historical table inventory differs')
    # These anchors bind the typed fields to the actual recorded wording.
    anchors={'T1':['3x180 s','276 s','two value checks UNKNOWN 119.6 s'],
             'T2':['2 of 16','cut mid-solve','~18 s','no verdict'],
             'T3':['CAP-20','18-probe'],
             'T4':['2 of 14','cut mid-solve','~13 s','no verdict'],
             'T5':['16/16 UNKNOWN 60 s'],
             'T6':['r1-r31 UNSAT','0.6-0.7 s','0 conflicts']}
    for row in rows:
        for anchor in anchors[row['id']]:
            if anchor not in ' '.join(row[k] for k in ('recorded_test','recorded_move','recorded_comparison')):
                raise ValueError('Typed fact anchor missing from its own row: '+anchor)
    return {'format':'hashsmash-interrupted-move-tests-v1',
            'source_path':'research/runs_1101/tricks/TRICKS_RESULTS_1101.md',
            'source_sha256':SOURCE_PIN,'recorded_date':'2026-11-01 (MST, as labelled)',
            'records':rows,'count':6,'source_table_cells':18,
            'interrupted_partial_tests':['T2','T4'],
            'independently_replayed_solver_verdicts':0,'minimum_core_proved':False,
            'later_completions_reconciled':False,'new_compute_requested':False,
            'scope':'Exact historical table transcription and bounded interpretation. No solver, model, proof-certificate or attack-price replay. Archived proposed tests are not current operating instructions.'}


def main():
    if not __debug__:raise SystemExit('Run without -O')
    if sys.argv[1:] not in ([],['--emit-projection']):raise ValueError('Unknown arguments')
    manifest=json.loads((BASE/'manifest.json').read_text(encoding='utf-8'))
    wanted={SOURCE,'replay.py','README.txt','records.json'}
    if set(manifest['files'])!=wanted:raise ValueError('Manifest inventory differs')
    if any(digest((BASE/n).read_bytes())!=pin for n,pin in manifest['files'].items()):raise ValueError('Manifest member changed')
    result=reconstruct()
    if '--emit-projection' in sys.argv:
        print(json.dumps(result,indent=2));return
    if json.loads((BASE/'records.json').read_text(encoding='utf-8'))!=result:
        raise ValueError('Records differ from source and reviewed qualifications')
    print(json.dumps({'passed':True,'table_rows':6,'source_table_cells':18,
                      'interrupted_tests':2,'solver_verdicts_replayed':0,
                      'minimum_core_proved':False,'new_compute_requested':False}))


if __name__=='__main__':main()
