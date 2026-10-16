from pathlib import Path
import subprocess,json,hashlib,sys
base=Path('/tmp/stamped-replay-comparator-review');out=base/'native-clean-check';out.mkdir();logs=[]
helper=base/'snapshot/skills/assess-alignment-with-stamped-principles/scripts/fresh_rerun.py'
def run(cmd,cwd=None):
 p=subprocess.run(list(map(str,cmd)),cwd=cwd,capture_output=True,text=True)
 logs.append({'argv':list(map(str,cmd)),'cwd':str(cwd or Path.cwd()),'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
 (out/'commands.json').write_text(json.dumps(logs,indent=2)+'\n')
 if p.returncode: raise RuntimeError(p.stderr)
 return p.stdout.strip()
def state(root):
 return {'head':run(['git','--no-optional-locks','rev-parse','HEAD'],root),'status':run(['git','--no-optional-locks','status','--porcelain'],root),'config':hashlib.sha256((root/'.git/config').read_bytes()).hexdigest(),'files':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None for p in [root/'input.tsv',root/'results/locked.tsv',root/'results/unlocked.tsv']}}
target=base/'native-clean/target'; absent=base/'native-clean/absent'
before={str(p):state(p) for p in [target,absent]}
ordinary=out/'ordinary-source';ordinary.mkdir();run(['git','init','-b','fixture'],ordinary);run(['git','config','core.hooksPath','/dev/null'],ordinary)
(ordinary/'results').mkdir();(ordinary/'results/plain.tsv').write_text('id\tvalue\n1\t3\n');(ordinary/'analysis.sh').write_text("mkdir -p results\nprintf 'id\\tvalue\\n1\\t3\\n' > results/plain.tsv\n")
run(['git','add','.'],ordinary)
trailers=run(['/Users/johnlee/.agents/skills/commit-provenance/scripts/resolve.sh'])
run(['git','commit','-m','test(replay): preserve ordinary non-annex output\n\n'+trailers],ordinary)
reports={}
for name,source,pattern in [('available-mixed',target,'results/*.tsv'),('available-unlocked',target,'results/unlocked.tsv'),('absent-unlocked',absent,'results/unlocked.tsv'),('ordinary',ordinary,'results/*.tsv')]:
 run([sys.executable,helper,'--path',source,'--entry','sh analysis.sh','--outputs',pattern,'--workdir',out/name,'--output',out/(name+'.json')]);r=json.loads((out/(name+'.json')).read_text());reports[name]={'status':r['status'],'entry_executed':any(x['step'].startswith('entry:') for x in r['steps']),'outputs_shipped':r.get('outputs_shipped'),'unavailable_comparators':r.get('unavailable_comparators'),'comparison':r.get('comparison')}
after={str(p):state(p) for p in [target,absent]}
assert before==after
assert reports['absent-unlocked']['status']=='not-checked' and not reports['absent-unlocked']['entry_executed']
assert reports['absent-unlocked']['outputs_shipped']=={'results/unlocked.tsv':None}
for name in ['available-mixed','available-unlocked','ordinary']:
 assert reports[name]['status']=='met' and reports[name]['entry_executed']
summary={'source_unchanged':before==after,'source_before':before,'source_after':after,'reports':reports}
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
