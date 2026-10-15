import pathlib, hashlib, json, subprocess, datetime, os
root=pathlib.Path('/tmp/stamped-assessment-evidence-final-blind')
review=root/'review'
log=review/'commands.jsonl'
def run(args,cwd=None):
    p=subprocess.run(args,cwd=cwd,text=True,capture_output=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','GIT_OPTIONAL_LOCKS':'0'})
    row=dict(time=datetime.datetime.now(datetime.timezone.utc).isoformat(),argv=args,cwd=str(cwd) if cwd else None,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr)
    with log.open('a') as f: f.write(json.dumps(row)+'\n')
    print(json.dumps(row))
    return p
hashes=json.loads((root/'snapshot-sha256.json').read_text())
checks=[dict(path=p,expected=h,actual=hashlib.sha256((root/p).read_bytes()).hexdigest()) for p,h in hashes.items()]
for row in checks: row['match']=row['expected']==row['actual']
(review/'snapshot-verification.json').write_text(json.dumps(dict(source=json.loads((root/'source.json').read_text()),files=checks,all_match=all(x['match'] for x in checks)),indent=2)+'\n')
base=root/'skills'
run(['python',str(base/'stamped-conventions/scripts/vendor_checklist.py'),'--check'])
run(['python',str(base/'stamped-conventions/scripts/encode_response.py'),'items','--level','must'])
run(['python',str(base/'assess-alignment-with-stamped-principles/scripts/run_probes.py'),'--help'])
objects=['/tmp/stamped-assessment-evidence-final-fixtures/test_a_manifest_does_not_prove0/dependency-review','/tmp/stamped-assessment-evidence-final-fixtures/test_a_manifest_does_not_prove2/dependency-review','/tmp/stamped-assessment-evidence-fixtures/test_a_spec_whose_content_neve0/annexed-spec','/tmp/stamped-assessment-evidence-fixtures/test_a_spec_whose_content_neve0/recipient']
for obj in objects:
    for args in [['git','rev-parse','HEAD'],['git','status','--porcelain=v1'],['git','ls-tree','-r','HEAD'],['git','remote','-v']]: run(args,obj)
    listing=run(['git','ls-tree','-r','--name-only','HEAD'],obj)
    for path in listing.stdout.splitlines(): run(['git','show','HEAD:'+path],obj)
for path in ['/tmp/stamped-assessment-evidence-final-fixtures/test_a_manifest_does_not_prove2/execution-receipt.json','/tmp/stamped-assessment-evidence-fixtures/test_a_spec_whose_content_neve0/retrieval-receipt.json']:
    run(['cat',path])
