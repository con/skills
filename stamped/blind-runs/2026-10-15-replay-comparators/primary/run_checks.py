import datetime
import json
import pathlib
import shlex
import subprocess
import time

root = pathlib.Path('/tmp/stamped-replay-comparator-review/primary')
env = '/Users/johnlee/.codex/worktrees/harmonize-stamped-pr26/stamped-ai-research-next/pixi.toml'
helper = '/tmp/stamped-replay-comparator-review/snapshot/skills/assess-alignment-with-stamped-principles/scripts/fresh_rerun.py'
checks = [('target-unlocked', 'target', 'results/unlocked.tsv'), ('absent-unlocked', 'absent', 'results/unlocked.tsv'), ('target-all', 'target', 'results/*.tsv')]
records = []
for name, source, pattern in checks:
    command = ['pixi', 'run', '--manifest-path', env, 'python', helper, '--path', '/tmp/stamped-replay-route-review/native/' + source, '--entry', 'sh analysis.sh', '--outputs', pattern, '--workdir', str(root / name), '--timeout', '120', '--max-get-gb', '0.01', '-o', str(root / (name + '.json'))]
    rendered = shlex.join(command)
    with (root / 'commands.sh').open('a') as out:
        out.write(rendered + '\n')
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    t = time.monotonic()
    result = subprocess.run(command, capture_output=True, text=True)
    (root / (name + '.stdout.txt')).write_text(result.stdout)
    (root / (name + '.stderr.txt')).write_text(result.stderr)
    records.append({'name': name, 'command': command, 'shell_command': rendered, 'started_at': started, 'elapsed_seconds': time.monotonic()-t, 'returncode': result.returncode})
    (root / 'invocations.json').write_text(json.dumps(records, indent=2)+'\n')
    print(name, result.returncode, result.stdout, result.stderr, flush=True)
