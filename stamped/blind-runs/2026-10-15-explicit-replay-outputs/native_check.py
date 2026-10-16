from pathlib import Path
import subprocess,json,hashlib,sys
base=Path('/tmp/stamped-output-selection-review');out=base/'native';out.mkdir();source=out/'source';source.mkdir();logs=[]
helper=base/'snapshot/skills/assess-alignment-with-stamped-principles/scripts/fresh_rerun.py';old=base/'old_fresh_rerun.py'
def run(cmd,cwd=None,check=True):
 p=subprocess.run(list(map(str,cmd)),cwd=cwd,capture_output=True,text=True)
 logs.append({'argv':list(map(str,cmd)),'cwd':str(cwd or Path.cwd()),'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr});(out/'commands.json').write_text(json.dumps(logs,indent=2)+'\n')
 if check and p.returncode:raise RuntimeError(p.stderr)
 return p
run(['git','init','-b','fixture'],source);run(['git','config','core.hooksPath','/dev/null'],source)
files={'input/participants.tsv':'participant_id\teffect\nsub-01\t2\nsub-02\t4\nsub-03\t6\n','results/group_summary.csv':'metric,value\nmean,4.0\n','skills/example/assets/icon.png':'synthetic unchanged icon bytes\n','results/reference-atlas-cache/manual.pdf':'synthetic unchanged reference bytes\n','analysis.py':"from pathlib import Path\nimport csv\nwith Path('input/participants.tsv').open() as stream:\n    rows = list(csv.DictReader(stream, delimiter='\\t'))\nvalue = sum(float(r['effect']) for r in rows) / len(rows)\nPath('results').mkdir(exist_ok=True)\nPath('results/group_summary.csv').write_text(f'metric,value\\nmean,{value}\\n')\n",'README.md':'# Synthetic study\n\nRun `python analysis.py` to compute the mean effect in input/participants.tsv.\nThe generated product is results/group_summary.csv. The PNG and reference PDF\nare supplied assets, not generated products.\n'}
for name,text in files.items():p=source/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
run(['git','add','.'],source);trailers=run(['/Users/johnlee/.agents/skills/commit-provenance/scripts/resolve.sh']).stdout.strip();run(['git','commit','-m','test(replay): retain participant and reference selection fixture\n\n'+trailers],source)
def state():return {'head':run(['git','rev-parse','HEAD'],source).stdout.strip(),'status':run(['git','status','--porcelain'],source).stdout,'hashes':{name:hashlib.sha256((source/name).read_bytes()).hexdigest() for name in files}}
before=state();reports={}
for name,script,selection in [('old-default',old,[]),('required-missing',helper,[]),('explicit-generated',helper,['--outputs','results/group_summary.csv'])]:
 r=run([sys.executable,script,'--path',source,'--entry','python analysis.py','--workdir',out/name,'-o',out/(name+'.json'),*selection],check=False)
 if name=='required-missing':
  assert r.returncode==2 and '--outputs' in r.stderr and not (out/name).exists() and not (out/(name+'.json')).exists()
  reports[name]={'exit_code':r.returncode,'workdir_exists':(out/name).exists(),'report_exists':(out/(name+'.json')).exists()};continue
 assert r.returncode==0
 report=json.loads((out/(name+'.json')).read_text());reports[name]=report
assert reports['old-default']['status']=='unmet' and not (out/'old-default/clone/input/participants.tsv').exists()
assert reports['explicit-generated']['status']=='met' and list(reports['explicit-generated']['outputs_shipped'])==['results/group_summary.csv']
protected=['input/participants.tsv','skills/example/assets/icon.png','results/reference-atlas-cache/manual.pdf']
assert all((source/p).read_bytes()==(out/'explicit-generated/clone'/p).read_bytes() for p in protected)
after=state();assert before==after
summary={'source_before':before,'source_after':after,'source_unchanged':before==after,'old_default_status':reports['old-default']['status'],'old_removed':next(x['log'] for x in reports['old-default']['steps'] if x['step'].startswith('removed ')),'missing_selection':reports['required-missing'],'explicit_status':reports['explicit-generated']['status'],'explicit_comparison':reports['explicit-generated']['comparison'],'protected_files_unchanged':protected}
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
