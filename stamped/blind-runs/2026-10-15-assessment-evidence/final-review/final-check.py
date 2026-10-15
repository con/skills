import pathlib, hashlib, json, subprocess, datetime, os
root=pathlib.Path('/tmp/stamped-assessment-evidence-final-blind'); review=root/'review'
manifest=json.loads((root/'snapshot-sha256.json').read_text())
checks={p:hashlib.sha256((root/p).read_bytes()).hexdigest()==h for p,h in manifest.items()}
objects=['/tmp/stamped-assessment-evidence-final-fixtures/test_a_manifest_does_not_prove0/dependency-review','/tmp/stamped-assessment-evidence-final-fixtures/test_a_manifest_does_not_prove2/dependency-review','/tmp/stamped-assessment-evidence-fixtures/test_a_spec_whose_content_neve0/annexed-spec','/tmp/stamped-assessment-evidence-fixtures/test_a_spec_whose_content_neve0/recipient']
statuses=[]
for obj in objects:
    p=subprocess.run(['git','status','--porcelain=v1'],cwd=obj,text=True,capture_output=True,env={**os.environ,'GIT_OPTIONAL_LOCKS':'0'})
    rec=dict(time=datetime.datetime.now(datetime.timezone.utc).isoformat(),argv=['git','status','--porcelain=v1'],cwd=obj,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr)
    with (review/'commands.jsonl').open('a') as f: f.write(json.dumps(rec)+'\n')
    statuses.append(rec)
receipts=[pathlib.Path(objects[1]).parent/'execution-receipt.json',pathlib.Path(objects[2]).parent/'retrieval-receipt.json']
result=dict(snapshot_all_match=all(checks.values()),snapshot_count=len(checks),source_metadata_sha256=hashlib.sha256((root/'source.json').read_bytes()).hexdigest(),snapshot_manifest_sha256=hashlib.sha256((root/'snapshot-sha256.json').read_bytes()).hexdigest(),all_objects_still_clean=all(x['returncode']==0 and not x['stdout'] for x in statuses),receipts=[dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in receipts])
(review/'final-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
