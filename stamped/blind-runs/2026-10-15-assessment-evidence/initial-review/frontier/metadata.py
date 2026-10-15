import json,pathlib,subprocess,os
out=pathlib.Path('/tmp/stamped-assessment-evidence-blind/frontier')
records=json.loads((out/'commands.json').read_text())
code='import sys,pathlib,json; sys.path.insert(0,"/tmp/stamped-assessment-evidence-blind/skills/assess-alignment-with-stamped-principles/scripts"); from probes.common import Object; from probes.structure import _spec_publication_evidence; print(json.dumps(_spec_publication_evidence(Object(pathlib.Path(sys.argv[1])),[".datalad/config","code/containers/analysis.sif"]),indent=2))'
base=pathlib.Path('/tmp/stamped-assessment-evidence-fixtures/test_a_spec_whose_content_neve0')
for name in ['annexed-spec','recipient']:
 argv=['pixi','run','--manifest-path','/Users/johnlee/.codex/worktrees/harmonize-stamped-pr26/stamped-ai-research-next/pixi.toml','python','-c',code,str(base/name)]
 p=subprocess.run(argv,text=True,capture_output=True,env={**os.environ,'GIT_OPTIONAL_LOCKS':'0','PYTHONDONTWRITEBYTECODE':'1'})
 records.append({'argv':argv,'cwd':None,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
 print(name,p.returncode,p.stdout,p.stderr)
 (out/f'{name}-locations.json').write_text(p.stdout)
(out/'commands.json').write_text(json.dumps(records,indent=2)+'\n')
