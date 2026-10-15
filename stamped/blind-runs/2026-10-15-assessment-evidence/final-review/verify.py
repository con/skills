import pathlib, hashlib, json, subprocess, datetime, os
root=pathlib.Path('/tmp/stamped-assessment-evidence-final-blind'); review=root/'review'
def run(args,cwd=None):
    p=subprocess.run(args,cwd=cwd,text=True,capture_output=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','GIT_OPTIONAL_LOCKS':'0'})
    row=dict(time=datetime.datetime.now(datetime.timezone.utc).isoformat(),argv=args,cwd=str(cwd) if cwd else None,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr)
    with (review/'commands.jsonl').open('a') as f: f.write(json.dumps(row)+'\n')
    print(json.dumps(row)); return p
objects={'numpy':'/tmp/stamped-assessment-evidence-final-fixtures/test_a_manifest_does_not_prove0/dependency-review','empty':'/tmp/stamped-assessment-evidence-final-fixtures/test_a_manifest_does_not_prove2/dependency-review','annex':'/tmp/stamped-assessment-evidence-fixtures/test_a_spec_whose_content_neve0/annexed-spec'}
for name,obj in objects.items():
    run(['python',str(root/'skills/assess-alignment-with-stamped-principles/scripts/run_probes.py'),obj,'--kind','component','--only','env-spec-tracked','-o',str(review/(name+'-probes.json'))])
    print((review/(name+'-probes.json')).read_text())
annex=pathlib.Path(objects['annex']); recipient=annex.parent/'recipient'
receipt=json.loads((annex.parent/'retrieval-receipt.json').read_text())
identity={'receipt_sha256':hashlib.sha256((annex.parent/'retrieval-receipt.json').read_bytes()).hexdigest(),'files':[]}
for obj in [annex,recipient]:
    path=obj/'code/containers/analysis.sif'
    content=path.read_bytes()
    row=dict(path=str(path),symlink=os.readlink(path),resolved_path=str(path.resolve()),size=len(content),sha256=hashlib.sha256(content).hexdigest(),matches_receipt=hashlib.sha256(content).hexdigest()==receipt['retrieved_sha256'])
    identity['files'].append(row)
    run(['git','config','--local','--get','annex.uuid'],obj)
    run(['git','log','-1','--format=%H%n%T%n%s'],obj)
(review/'payload-verification.json').write_text(json.dumps(identity,indent=2)+'\n'); print(json.dumps(identity))
exec_receipt=pathlib.Path(objects['empty']).parent/'execution-receipt.json'
run(['cat',str(exec_receipt.parent/'empty-runtime/pyvenv.cfg')])
print(json.dumps({'execution_receipt_sha256':hashlib.sha256(exec_receipt.read_bytes()).hexdigest()}))
