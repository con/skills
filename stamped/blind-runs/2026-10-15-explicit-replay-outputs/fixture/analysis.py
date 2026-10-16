from pathlib import Path
import csv
with Path('input/participants.tsv').open() as stream:
    rows = list(csv.DictReader(stream, delimiter='\t'))
value = sum(float(r['effect']) for r in rows) / len(rows)
Path('results').mkdir(exist_ok=True)
Path('results/group_summary.csv').write_text(f'metric,value\nmean,{value}\n')
