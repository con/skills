from pathlib import Path
import hashlib, json, subprocess, sys
source = Path('/tmp/stamped-output-selection-review/primary-source')
clone = Path('/tmp/stamped-output-selection-review/primary/selected-workdir/clone')
files = subprocess.check_output(['git', '-C', str(source), 'ls-files'], text=True).splitlines()
def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
record = {'source_commit': subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip(),
          'source_status': subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain'], text=True),
          'source_sha256': {f: digest(source / f) for f in files}}
if sys.argv[1] == 'after':
    before = json.loads(Path('/tmp/stamped-output-selection-review/primary/before.json').read_text())
    record['source_unchanged'] = before == record
    record['clone_sha256'] = {f: digest(clone / f) for f in files}
    record['clone_matches_source'] = record['clone_sha256'] == record['source_sha256']
    record['clone_removal_commit_diff'] = subprocess.check_output(['git', '-C', str(clone), 'show', '--format=fuller', '--stat', 'HEAD'], text=True)
    record['clone_removal_commit_paths'] = subprocess.check_output(['git', '-C', str(clone), 'diff-tree', '--no-commit-id', '--name-status', '-r', 'HEAD'], text=True)
print(json.dumps(record, indent=2))
