import subprocess, pathlib, json, hashlib, datetime, os
out=pathlib.Path('/tmp/stamped-assessment-evidence-blind/frontier')
base=out.parent
records=[]
def run(argv,cwd=None):
 p=subprocess.run(argv,cwd=cwd,text=True,capture_output=True,env={**os.environ,'GIT_OPTIONAL_LOCKS':'0','PYTHONDONTWRITEBYTECODE':'1'})
 rec={'argv':argv,'cwd':str(cwd) if cwd else None,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
 records.append(rec); (out/'commands.json').write_text(json.dumps(records,indent=2)+'\n')
 print(json.dumps(rec,indent=2))
 return p
hashes=json.loads((base/'snapshot-sha256.json').read_text())
verified={p:hashlib.sha256((base/p).read_bytes()).hexdigest()==v for p,v in hashes.items()}
(out/'snapshot-verification.json').write_text(json.dumps({'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'manifest_sha256':hashlib.sha256((base/'snapshot-sha256.json').read_bytes()).hexdigest(),'files':verified},indent=2)+'\n')
assert all(verified.values())
pixi=['pixi','run','--manifest-path','/Users/johnlee/.codex/worktrees/harmonize-stamped-pr26/stamped-ai-research-next/pixi.toml','python']
conv=base/'skills/stamped-conventions'
run(pixi+[str(conv/'scripts/vendor_checklist.py'),'--check'])
run(pixi+[str(conv/'scripts/encode_response.py'),'items','--level','must'])
fixture=pathlib.Path('/tmp/stamped-assessment-evidence-fixtures')
roots=[fixture/'test_a_manifest_does_not_prove0/dependency-review',fixture/'test_a_manifest_does_not_prove1/dependency-review',fixture/'test_a_spec_whose_content_neve0/annexed-spec',fixture/'test_a_spec_whose_content_neve0/recipient']
for i,root in enumerate(roots):
 run(['git','rev-parse','HEAD'],root)
 run(['git','status','--porcelain=v1'],root)
 tree=run(['git','ls-tree','-r','HEAD'],root)
 run(['git','remote','-v'],root)
 for line in tree.stdout.splitlines():
  meta,path=line.split('\t',1)
  if meta.startswith('100644'):
   run(['git','show','HEAD:'+path],root)
 if i<3:
  run(pixi+[str(base/'skills/assess-alignment-with-stamped-principles/scripts/run_probes.py'),str(root),'--kind','component','--only','env-spec-tracked','-o',str(out/f'object-{i}-probes.json')])
 if i>=2:
  run(['git','show','HEAD:code/containers/analysis.sif'],root)
  path=root/'code/containers/analysis.sif'
  rec={'path':str(path),'symlink':str(path.readlink()) if path.is_symlink() else None,'available':path.exists()}
  if path.exists():rec.update(size=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
  (out/f'object-{i}-payload.json').write_text(json.dumps(rec,indent=2)+'\n');print(json.dumps(rec))
