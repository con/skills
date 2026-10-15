import subprocess,json,pathlib,os
base=pathlib.Path('/tmp/stamped-annex-init-check-v3'); base.mkdir(exist_ok=True)
records=[]
def run(args,cwd=base,check=True):
 p=subprocess.run(args,cwd=cwd,text=True,capture_output=True);records.append(dict(args=args,cwd=str(cwd),returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
 (base/'commands.json').write_text(json.dumps(records,indent=2)+'\n')
 if check and p.returncode: raise RuntimeError(records[-1])
 return p
source='/tmp/stamped-assessment-evidence-fixtures/test_a_spec_whose_content_neve0/annexed-spec'
parent=base/'parent'; run(['git','init',str(parent)])
for name in ['selected','unrelated']:
 run(['git','-c','protocol.file.allow=always','submodule','add',source,name],parent)
trailers=subprocess.check_output(['/Users/johnlee/.agents/skills/commit-provenance/scripts/resolve.sh'],text=True)
run(['git','commit','-m','test: register annex initialization fixture\n\n'+trailers],parent)
raw=base/'raw'; run(['git','clone',str(parent),str(raw)])
run(['git','-c','protocol.file.allow=always','submodule','update','--init','--','selected'],raw)
child=raw/'selected'; initial_uuid=run(['git','config','--get','annex.uuid'],child,False); before=run(['git','annex','whereis','--json','code/containers/analysis.sif'],child,False)
head=run(['git','rev-parse','HEAD'],child).stdout.strip(); blob=run(['git','show','HEAD:code/containers/analysis.sif'],child).stdout
run(['git','annex','init'],child)
after=run(['git','annex','whereis','--json','code/containers/analysis.sif'],child)
assert run(['git','rev-parse','HEAD'],child).stdout.strip()==head
assert run(['git','show','HEAD:code/containers/analysis.sif'],child).stdout==blob
assert not (child/'code/containers/analysis.sif').exists(); assert not (raw/'unrelated/.git').exists()
native=base/'native'; run(['git','clone',str(parent),str(native)])
run(['git','-c','protocol.file.allow=always','config','--local','protocol.file.allow','always'],native)
env=os.environ.copy();env['GIT_ALLOW_PROTOCOL']='file'
p=subprocess.run(['datalad','get','-n','selected'],cwd=native,text=True,capture_output=True,env=env);records.append(dict(args=['datalad','get','-n','selected'],cwd=str(native),returncode=p.returncode,stdout=p.stdout,stderr=p.stderr));(base/'commands.json').write_text(json.dumps(records,indent=2)+'\n');assert p.returncode==0
run(['git','annex','whereis','--json','code/containers/analysis.sif'],native/'selected')
assert not (native/'selected/code/containers/analysis.sif').exists();assert not (native/'unrelated/.git').exists()
single=base/'single'; run(['git','clone','--single-branch','--no-local',source,str(single)]); single_before=run(['git','annex','whereis','--json','code/containers/analysis.sif'],single,False); run(['git','annex','init'],single); single_after=run(['git','annex','whereis','--json','code/containers/analysis.sif'],single,False)
result={'raw_initial_uuid_absent':initial_uuid.returncode!=0,'single_before_returncode':single_before.returncode,'single_before_stderr':single_before.stderr,'single_after_stdout':single_after.stdout,'single_after_stderr':single_after.stderr,'raw_whereis_before_returncode':before.returncode,'raw_whereis_before_stderr':before.stderr,'raw_whereis_after_returncode':after.returncode,'raw_dotgit_native_layout':str((child/'.git').resolve()),'raw_head_and_blob_preserved':True,'native_get_no_data_succeeded':True,'payloads_not_fetched':True,'unrelated_not_initialized':True,'fixture_parent':run(['git','rev-parse','HEAD'],parent).stdout.strip()}
(base/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
