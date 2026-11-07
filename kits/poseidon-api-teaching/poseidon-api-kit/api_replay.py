"""Bounded replay of the archived Poseidon API using already-public numerical data.

Keep this script beside poseidon_ref.py and finite-witnesses.json. No imported
organizer program or original workspace is needed. Temporary parameter JSON is
created only to adapt the public data to the historical API's file interface.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import tempfile
import time

SOURCE_SHA256='344246fc03ae862cd42beabcade902edea45d23df6cb62751f741c3df636f171'
DATA_SHA256='dd6dd429e8b69c6271bc438de48054c6bf912f47635d243a2a94be3e3778d7ae'


def require(condition,message):
    if not condition:raise RuntimeError(message)


def main():
    require(__debug__,'Do not use Python -O with this historical API')
    start=time.monotonic(); root=Path(__file__).resolve().parent
    source=root/'poseidon_ref.py'; datafile=root/'finite-witnesses.json'
    require(hashlib.sha256(source.read_bytes()).hexdigest()==SOURCE_SHA256,'Reference source hash mismatch')
    require(hashlib.sha256(datafile.read_bytes()).hexdigest()==DATA_SHA256,'Numerical data hash mismatch')
    data=json.loads(datafile.read_text()); params=data['parameters']['poseidon']
    adapted={'round_constants':params['round_constants_hex'],'mds':params['mds_hex']}
    prior=os.environ.get('ORCHARD_CONSTANTS_JSON')
    try:
        with tempfile.TemporaryDirectory(prefix='poseidon-api-parameters-') as directory:
            constants=Path(directory)/'parameters.json'
            constants.write_text(json.dumps(adapted))
            os.environ['ORCHARD_CONSTANTS_JSON']=str(constants)
            spec=importlib.util.spec_from_file_location('reviewed_poseidon_ref',source)
            module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    finally:
        if prior is None:os.environ.pop('ORCHARD_CONSTANTS_JSON',None)
        else:os.environ['ORCHARD_CONSTANTS_JSON']=prior
    require(module.P==int(params['modulus_hex'],16) and module.CAPACITY==int(params['capacity_hex'],16),'Model mismatch')
    results=[]
    def record(name,passed):
        require(passed,name+' failed'); results.append(name)
    for key,actual in (('round_constants',module.RC),('mds',module.MDS)):
        expected=tuple(tuple(int.from_bytes(bytes.fromhex(x),'little') for x in row)
                       for row in params['parameter_crosscopy_le_hex'][key])
        record('parameter_crosscopy_'+key,actual==expected)
    for i,vector in enumerate(data['known_answers']['poseidon_permutation_le_hex']):
        words=[int.from_bytes(bytes.fromhex(x),'little') for x in vector]
        record('full_permutation_'+str(i),module.perm(words[:3],56)==words[3:])
    for i,vector in enumerate(data['known_answers']['poseidon_hash_le_hex']):
        message=bytes.fromhex(vector[0]+vector[1]); expected=bytes.fromhex(vector[2])
        a,b=int.from_bytes(message[:32],'little'),int.from_bytes(message[32:],'little')
        record('full_hash_'+str(i),module.hash_full(a,b).to_bytes(32,'little')==expected)
        record('full_schedule_agreement_'+str(i),module.digest_bytes(message,56)==expected)
    record('r2_original_indices',module.schedule(2)==[0,1,2,3,4,5,60,61,62,63])
    count=0; identities=set(); mutated_profiles=set()
    for row in data['witnesses']:
        if not row['profile'].startswith('poseidon-orchard-'):continue
        require(time.monotonic()-start<20,'Finite replay deadline exceeded')
        match=re.fullmatch(r'poseidon-orchard-r([1-5])-prefix-v1',row['profile'])
        require(match is not None,'Unexpected reduced target')
        r=int(match[1]); a,b=bytes.fromhex(row['message_a_hex']),bytes.fromhex(row['message_b_hex'])
        identity=(r,*sorted((a,b))); require(identity not in identities,'Duplicate witness identity')
        identities.add(identity)
        expected=bytes.fromhex(row['expected_digest'])
        record('witness_'+str(count),a!=b and module.digest_bytes(a,r)==module.digest_bytes(b,r)==expected)
        count+=1
        if r not in mutated_profiles:
            changed=bytes([a[0]^1])+a[1:]
            record('mutation_r'+str(r),module.digest_bytes(changed,r)!=expected)
            mutated_profiles.add(r)
    require(count==33 and len(mutated_profiles)==5,'Witness inventory changed')
    rejected=[]
    def rejection(name,fn,exception=ValueError):
        try:fn()
        except exception:rejected.append(name)
        else:raise RuntimeError('Expected rejection: '+name)
    for i,value in enumerate((-1,module.P,True,False,1.0,None)):
        rejection('noncanonical_nk_'+str(i),lambda:module.hash_reduced(value,0,2))
        rejection('noncanonical_rho_'+str(i),lambda:module.hash_reduced(0,value,2))
    for i,value in enumerate((b'',bytes(63),bytes(65),bytearray(64),'')):
        rejection('byte_input_'+str(i),lambda:module.digest_bytes(value,2))
    rejection('encoded_modulus',lambda:module.digest_bytes(module.P.to_bytes(32,'little')+bytes(32),2))
    for r in (-1,57):rejection('schedule_'+str(r),lambda:module.schedule(r),AssertionError)
    print(json.dumps({'passed':True,'source_sha256':SOURCE_SHA256,
      'results':{'numerical_data_sha256':DATA_SHA256,'passed_checks':results,'rejected_invalid_inputs':rejected,
                 'distinct_witnesses':count,'mutated_profiles':len(mutated_profiles)},
      'elapsed_wall_seconds':round(time.monotonic()-start,4),
      'scope':'Finite archived API replay using already-published numerical parameters/vectors. Eleven full permutation and eleven full-hash known answers, full/reduced API agreement, 33 reduced-profile witnesses, five mutations and invalid-input controls. No search, success-rate or attack-cost proof.'},indent=2))


if __name__=='__main__':main()
