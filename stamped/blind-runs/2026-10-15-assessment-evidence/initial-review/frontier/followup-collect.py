import subprocess,pathlib,json,os,hashlib
out=pathlib.Path('/tmp/stamped-assessment-evidence-blind/frontier')
root=pathlib.Path('/tmp/stamped-assessment-evidence-final-fixtures/test_a_manifest_does_not_prove2/dependency-review')
records=[]
def run(argv):
 p=subprocess.run(argv,cwd=root,text=True,capture_output=True,env={**os.environ,'GIT_OPTIONAL_LOCKS':'0','PYTHONDONTWRITEBYTECODE':'1'})
 rec={'argv':argv,'cwd':str(root),'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
 records.append(rec);(out/'followup-commands.json').write_text(json.dumps(records,indent=2)+'\n');print(json.dumps(rec,indent=2));return p
run(['git','rev-parse','HEAD']);run(['git','status','--porcelain=v1'])
tree=run(['git','ls-tree','-r','HEAD'])
for line in tree.stdout.splitlines():
 meta,path=line.split('\t',1)
 if meta.startswith('100644'):run(['git','show','HEAD:'+path])
receipt=root.parent/'execution-receipt.json'
text=receipt.read_text()
(out/'followup-receipt-evidence.json').write_text(json.dumps({'path':str(receipt),'sha256':hashlib.sha256(receipt.read_bytes()).hexdigest(),'content':json.loads(text)},indent=2)+'\n')
print(text)
run(['pixi','run','--manifest-path','/Users/johnlee/.codex/worktrees/harmonize-stamped-pr26/stamped-ai-research-next/pixi.toml','python','/tmp/stamped-assessment-evidence-blind/skills/assess-alignment-with-stamped-principles/scripts/run_probes.py',str(root),'--kind','component','--only','env-spec-tracked','-o',str(out/'followup-probes.json')])
