# Scoped follow-up: dependency-review fixture 2

This synthetic engineering object is assessed only on must/010 and must/013. No scientific claim is evaluated. Target commit: `5697076be929f539b770d19efa899044e38d58b9` (`test: dependency declaration boundary`); its working tree was clean. I did not execute or modify the target.

## Probe suggestion

The frozen `env-spec-tracked` probe found `requirements.txt`, marked must/013 met, and left must/010 not-checked because it does not compare imports with dependencies. Its unedited output is `followup-probes.json` beside this report.

## Final judgments

| Item | Status | Evidence and reason |
|---|---|---|
| must/010 | **unmet** | `analysis.py` imports `numpy`, but tracked `requirements.txt` contains only `# no packages declared`. The documented route in `README.md` creates a fresh virtual environment without system site packages and installs that file. The supplied receipt names this exact source commit and records the fresh-runtime command failing at `import numpy` with `ModuleNotFoundError: No module named 'numpy'`. The declared environment omits a required dependency. |
| must/013 | **met** | `requirements.txt` is tracked in the target commit (blob `9153ba9d9c0a5ecf7f88f5224d239e979996db03`), alongside `analysis.py` and `README.md`. |

The probe suggestion and judgments differ only on must/010: dependency completeness required reading the import, declared route, and matching execution receipt. The receipt's `source_commit` equals the target commit, and its failure directly confirms the missing import in a fresh runtime.

## Remaining uncertainty

The receipt records the executed Python command and its import failure, but not Python/pip versions or a separate log of the preceding environment creation and install commands. Those details are not needed to establish this specific omission: the documented spec is empty and the matching-commit run reports NumPy absent. No other checklist items were assessed.

## Provenance

Assessor snapshot source commit: `afd2c0ff8b556788a3ab9e7d35eb0e4b24cd5d59`; all 19 files listed in `snapshot-sha256.json` were verified during the preceding scoped assessment. The snapshot identifies `assess-alignment-with-stamped-principles` 0.1.0 and `stamped-conventions` 0.1.0, using checklist 0.3.1 (`af259bad237fa57b856417db8dba45a1b283a527`). The synthetic receipt is `/tmp/stamped-assessment-evidence-final-fixtures/test_a_manifest_does_not_prove2/execution-receipt.json`.
