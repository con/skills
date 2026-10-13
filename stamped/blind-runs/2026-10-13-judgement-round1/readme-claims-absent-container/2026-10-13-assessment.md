# Assessment: Brain volume versus age in ds007116 (R0)

## Verdict

**MUST**: 11 met, 6 unmet, 0 partial, 0 not-checked  
**SHOULD**: 5 met, 5 unmet, 0 partial, 0 not-checked  
**MAY**: 1 met, 0 unmet, 0 partial, 4 not-checked

## What to fix first

1. **Environment mismatch between documentation and implementation** (must/003, must/017, should/007, should/008) — The README claims to use the `neurodesk-freesurfer` container from `///repronim/containers`, but the Makefile calls Python directly. Git run records reference `code/containers/plotting.sif` which does not exist. The containers.json has dummy values. Until the actual execution environment matches the documented one, the study cannot be reliably reproduced.

2. **Host assumptions are not documented** (must/011, must/012) — The README and environment specs do not state OS requirements, required system packages, or Python version constraints. A reader attempting reproduction on a different system will have no guidance on compatibility.

3. **No process for updating environment specifications** (must/014, should/008) — There is no documented process for updating dependencies when requirements.in changes. The divergence between run records (containers) and actual execution (Makefile) shows this gap has real consequences.

4. **Environment artifacts are not archived** (should/007) — The container image referenced in run records is not included or retrievable. Only requirements.lock is available, which is insufficient for exact reproduction given the container claims.

5. **No disposable environments per execution** (should/004, should/005) — Both the local Makefile and CI workflow assume system Python and pip. Neither spawns fresh environments per run; the CI workflow reuses ubuntu-latest but without container isolation.

## What the project already does well

1. **Derived files are tracked with run records** — Both figures and results trace to re-executable records in git history (Makefile-based). This is the foundation for reproducibility.

2. **Input data is properly linked** — The ds007116 dataset is linked as a git submodule with a resolvable GitHub URL, and the link is clean (no '+' or 'U' flags).

3. **Code is modular and clear** — Raw data, code, results, and environment specs are in separate directories. The Makefile is simple and transparent about what it does.

## Per-item assessment

| Item | Principle | Status | Evidence | Reason |
|------|-----------|--------|----------|--------|
| must/001 | S.1 | met | README.md, .gitmodules | All source files, code, and results are nested under the object root |
| must/002 | S.1 | met | .gitmodules | All 1 linked module(s) carry urls that resolve from elsewhere |
| must/003 | S.1 | unmet | Makefile, code/containers.json, commit:b230d4f | Python dependencies are pinned but run records reference missing container; Makefile uses no container |
| must/004 | T.1,T.3,T.5 | met | git ls-files, git status | git tracks 10 text/code/config paths and status is empty |
| must/005 | T.1,T.3,T.5 | met | git ls-tree -r -l HEAD | No binary blob over 10 MiB; nothing in this object is large binary data |
| must/006 | T.1,T.3,T.5 | met | figures/brain-volume-vs-age.png, results/volumes.tsv | All 2 derived file(s) trace to re-executable record (2 run records) |
| must/007 | A.1 | met | README.md, Makefile | README.md has an install/usage/reproduce section |
| must/008 | A.1 | met | code/collect_volumes.py, code/plot_volumes.py | Starting point present and named in instructions |
| must/009 | P.1 | met | probe:no-abs-paths | No host-specific absolute paths in tracked text files |
| must/010 | P.1 | met | requirements.lock | Dependencies are pinned; no tracked script expects a tool to be present already |
| must/011 | P.1 | unmet | README.md | README does not document OS requirements, system libraries, or host assumptions |
| must/012 | P.2 | unmet | requirements.lock, README.md | No system dependencies or OS versions documented; README mentions python3 but no version constraint |
| must/013 | P.3 | met | requirements.lock | Environment spec is tracked in version control |
| must/014 | P.3 | unmet | Makefile, commit:a230dc2 | No documented process for updating environment specs; run records claim containers but implementation did not follow |
| must/015 | D.1 | met | commit:b230d4f, commit:ebe8aa1 | Run records reference pinned image or lockfile; no ':latest' reference tracked |
| must/016 | D.1 | met | requirements.lock in published repo | Environment specifications are shared via published git repository |
| must/017 | D.1 | unmet | README.md#L14, code/containers.json, Makefile | Documentation is contradictory: README claims neurodesk-freesurfer container but Makefile uses python3 directly; run records reference non-existent container |
| should/001 | T.2 | met | .gitmodules, git config | Git used for code/config, git submodules for inputs; single version control system |
| should/002 | A.2 | met | .github/workflows/rerun.yml | Workflow re-executes and rebuilds environment on push/PR |
| should/003 | M.1 | met | sourcedata/, code/, figures/, results/ | Raw data, code, derived results, and environment in distinct modules |
| should/004 | E.1 | unmet | .github/workflows/rerun.yml, Makefile | CI runs on ubuntu-latest but does not spawn disposable containers per execution |
| should/005 | E.1 | unmet | Makefile, README.md#L11 | Makefile assumes system Python; venv is reused, not disposable per run |
| should/006 | D.2 | met | .github/workflows/rerun.yml | CI workflow re-executes to verify reproducibility |
| should/007 | D.2 | unmet | code/containers.json, commit:b230d4f | requirements.lock is archived but container code/containers/plotting.sif referenced in run records does not exist |
| should/008 | D.2 | unmet | README.md | No documented process for updating environment specs (duplicate of must/014) |
| should/009 | M.4 | not-applicable | — | No restricted data or software in this object; all components are public |
| may/001 | M.2 | met | sourcedata/ds007116 | 1 external component(s) are linked as modules |
| may/002 | M.2 | not-checked | — | No probe covers this; would require reading the project's documentation on module relationships |
| may/003 | M.2 | not-checked | — | No probe covers this; would require reading independence of module boundaries |
| may/004 | M.2 | not-checked | — | No probe covers this; would require checking composition mechanism |
| may/005 | M.2 | not-checked | — | No probe covers this; would require reading documentation/tooling for navigating modules |

## Flagged items

Items with evidence of probe disagreement, unverified claims, or other complications:

- **must/003** (unverified-claim): Run records reference container but actual execution does not use one; claims about external software are not backed by evidence in the Makefile.
- **must/014** (probe-overridden): Probe marked env-spec-tracked as met, but no process exists for updating specs; divergence between git history and actual execution shows this is problematic.
- **must/017** (unverified-claim): README documentation contradicts implementation and run records; the stated container does not match the code.

## Not checked

Items that required a reading of the object but were left for manual judgment or lack evidence:

- **may/002**: Modular structure documented — documentation would clarify relationships between components; not verified.
- **may/003**: Modular boundaries independent — would require reading detailed documentation; not verified.
- **may/004**: Composition mechanism — not verified; would require reading or inferring from code.
- **may/005**: Documentation for navigating modules — not verified; would require reading documentation or looking for tooling.

## Goals and kind

**Stated goals** (from README.md): This is a small, fully recorded study that reads FreeSurfer tables from ds007116, joins them with per-session ages, and plots brain volume with the GM/WM ratio against age.

**Kind**: Study (a question answered with data and compute: the usual shape of STAMPED assessments).

**Emphasis for this kind**: All seven principles carry weight, with particular emphasis on **Tracked** (every derived file has a re-executable record), **Self-contained** (inputs and boundaries clear), and **Distributable** (others can retrieve and rebuild).

---

## Checklist app URL

Open this assessment in the web app:  
<https://checklist.stamped-principles.org/?checklist=0.3.1&responses_version=0.3.1&cols=auto&sections=off&format=3&responses=eyJjaGVja2xpc3RfdmVyc2lvbiI6IjAuMy4xIiwicmVzcG9uc2VzIjp7InN0YW1wZWQtY2hlY2tsaXN0Om11c3QvMDAxIjp7InZhbHVlIjoieWVzIiwicmVhc29uIjoiQWxsIHNvdXJjZSBmaWxlcywgY29kZSwgYW5kIHJlc3VsdHMgYXJlIG5lc3RlZCB1bmRlciB0aGUgb2JqZWN0IHJvb3Q7IHNvdXJjZWRhdGEvZHMwMDcxMTYgaXMgbGlua2VkIGFzIGEgc3VibW9kdWxlLiJ9LCJzdGFtcGVkLWNoZWNrbGlzdDptdXN0LzAwMiI6eyJ2YWx1ZSI6InllcyIsInJlYXNvbiI6IkFsbCAxIGxpbmtlZCBtb2R1bGUocykgY2FycnkgdXJscyB0aGF0IHJlc29sdmUgZnJvbSBlbHNld2hlcmU6IHNvdXJjZWRhdGEvZHMwMDcxMTYifSwic3RhbXBlZC1jaGVja2xpc3Q6bXVzdC8wMDMiOnsidmFsdWUiOiJubyIsInJlYXNvbiI6IlB5dGhvbiBkZXBlbmRlbmNpZXMgYXJlIHBpbm5lZCBpbiByZXF1aXJlbWVudHMubG9jaywgYnV0IHJ1biByZWNvcmRzIHJlZmVyZW5jZSBhcHB0YWluZXIvY29udGFpbmVyIGNvZGUvY29udGFpbmVycy9wbG90dGluZy5zaWYgd2hpY2ggZG9lcyBub3QgZXhpc3Q7IGFjdHVhbCBNYWtlZmlsZSBqdXN0IGNhbGxzIHB5dGhvbjMgZGlyZWN0bHkuIEVudmlyb25tZW50IHNwZWNpZmljYXRpb24gaXMgaW5jb21wbGV0ZS4ifSwic3RhbXBlZC1jaGVja2xpc3Q6bXVzdC8wMDQiOnsidmFsdWUiOiJ5ZXMiLCJyZWFzb24iOiJnaXQgdHJhY2tzIDEwIHRleHQsIGNvZGUgYW5kIGNvbmZpZ3VyYXRpb24gZmlsZShzKSwgYW5kIGBnaXQgc3RhdHVzYCBpcyBlbXB0eSBpbmNsdWRpbmcgc3VibW9kdWxlczogdGhlIGNvbW1pdHRlZCBzdGF0ZSBpcyB0aGUgd2hvbGUgc3RhdGUuIn0sInN0YW1wZWQtY2hlY2tsaXN0Om11c3QvMDA1Ijp7InZhbHVlIjoieWVzIiwicmVhc29uIjoiTm8gYmluYXJ5IGJsb2Igb3ZlciAxMCBNaUIgaW4gZ2l0LCBhbmQgbm8gbGFyZ2UtY29udGVudCBtZWNoYW5pc20gaXMgbmVlZGVkOiBub3RoaW5nIGluIHRoaXMgb2JqZWN0IGlzIGxhcmdlIGJpbmFyeSBkYXRhLiJ9LCJzdGFtcGVkLWNoZWNrbGlzdDptdXN0LzAwNiI6eyJ2YWx1ZSI6InllcyIsInJlYXNvbiI6IkFsbCAyIGRlcml2ZWQgZmlsZShzKSB0cmFjZSB0byBhIHJlLWV4ZWN1dGFibGUgcmVjb3JkICgyIHJ1biByZWNvcmQocyksIHdvcmtmbG93czogTWFrZWZpbGUpLiJ9LCJzdGFtcGVkLWNoZWNrbGlzdDptdXN0LzAwNyI6eyJ2YWx1ZSI6InllcyIsInJlYXNvbiI6IlJFQURNRS5tZCBoYXMgYW4gaW5zdGFsbC91c2FnZS9yZXByb2R1Y2Ugc2VjdGlvbi4ifSwic3RhbXBlZC1jaGVja2xpc3Q6bXVzdC8wMDgiOnsidmFsdWUiOiJ5ZXMiLCJyZWFzb24iOiJTdGFydGluZyBwb2ludCBwcmVzZW50OiBjb2RlL2NvbGxlY3Rfdm9sdW1lcy5weS4ifSwic3RhbXBlZC1jaGVja2xpc3Q6bXVzdC8wMDkiOnsidmFsdWUiOiJ5ZXMiLCJyZWFzb24iOiJObyBob3N0LXNwZWNpZmljIGFic29sdXRlIHBhdGhzIGluIHRyYWNrZWQgdGV4dCBmaWxlcy4ifSwic3RhbXBlZC1jaGVja2xpc3Q6bXVzdC8wMTAiOnsidmFsdWUiOiJ5ZXMiLCJyZWFzb24iOiJEZXBlbmRlbmNpZXMgYXJlIHBpbm5lZCBpbiByZXF1aXJlbWVudHMubG9jaywgYW5kIG5vIHRyYWNrZWQgc2NyaXB0IGV4cGVjdHMgYSB0b29sIHRvIGJlIHByZXNlbnQgYWxyZWFkeS4ifSwic3RhbXBlZC1jaGVja2xpc3Q6bXVzdC8wMTEiOnsidmFsdWUiOiJubyIsInJlYXNvbiI6IlJFQURNRSBkb2VzIG5vdCBkb2N1bWVudCBPUyByZXF1aXJlbWVudHMsIHN5c3RlbSBsaWJyYXJpZXMsIG9yIG90aGVyIGhvc3QgYXNzdW1wdGlvbnMgYmV5b25kIFB5dGhvbiB2ZXJzaW9uLiBObyBtZW50aW9uIG9mIHJlcXVpcmVkIHN5c3RlbSBwYWNrYWdlcy4ifSwic3RhbXBlZC1jaGVja2xpc3Q6bXVzdC8wMTIiOnsidmFsdWUiOiJubyIsInJlYXNvbiI6InJlcXVpcmVtZW50cy5sb2NrIGxpc3RzIFB5dGhvbiBwYWNrYWdlcyBidXQgbm8gc3lzdGVtIGRlcGVuZGVuY2llcyBvciBPUyB2ZXJzaW9ucyBhcmUgZG9jdW1lbnRlZC4gUkVBRE1FIG1lbnRpb25zIHB5dGhvbjMgYnV0IG5vIHZlcnNpb24gY29uc3RyYWludCBvciBzeXN0ZW0gcmVxdWlyZW1lbnRzLiJ9LCJzdGFtcGVkLWNoZWNrbGlzdDptdXN0LzAxMyI6eyJ2YWx1ZSI6InllcyIsInJlYXNvbiI6IlRyYWNrZWQ6IHJlcXVpcmVtZW50cy5sb2NrLiJ9LCJzdGFtcGVkLWNoZWNrbGlzdDptdXN0LzAxNCI6eyJ2YWx1ZSI6Im5vIiwicmVhc29uIjoiTm8gZG9jdW1lbnRlZCBwcm9jZXNzIGZvciB1cGRhdGluZyBlbnZpcm9ubWVudCBzcGVjcy4gcmVxdWlyZW1lbnRzLmluIGV4aXN0cyBidXQgbm8gZG9jdW1lbnRhdGlvbiBvZiBob3cvd2hlbiB0byB1cGRhdGUuIFJ1biByZWNvcmRzIGNsYWltIGNvbnRhaW5lcnMgYnV0IHRob3NlIGFyZSBub3QgYWN0dWFsbHkgdXNlZCBpbiBNYWtlZmlsZS4ifSwic3RhbXBlZC1jaGVja2xpc3Q6bXVzdC8wMTUiOnsidmFsdWUiOiJ5ZXMiLCJyZWFzb24iOiIyIHJ1biByZWNvcmQocykgcmVmZXJlbmNlIGEgcGlubmVkIGltYWdlIG9yIGxvY2tmaWxlLCBhbmQgbm8gJzpsYXRlc3QnIHJlZmVyZW5jZSBpcyB0cmFja2VkLiJ9LCJzdGFtcGVkLWNoZWNrbGlzdDptdXN0LzAxNiI6eyJ2YWx1ZSI6InllcyIsInJlYXNvbiI6IlRoZSBzcGVjaWZpY2F0aW9uIGlzIHRyYWNrZWQgaW4gYSByZXBvc2l0b3J5IHB1Ymxpc2hlZCBhdCBodHRwczovL2dpdGh1Yi5jb20vY29uL3N0YW1wZWQtZXZhbC1maXh0dXJlLXIwLmdpdCwgc28gaXQgdHJhdmVscyB3aXRoIHRoZSBvYmplY3QgZm9yIGFueW9uZSB3aG8gY2FuIGNsb25lIGl0LiJ9LCJzdGFtcGVkLWNoZWNrbGlzdDptdXN0LzAxNyI6eyJ2YWx1ZSI6Im5vIiwicmVhc29uIjoiUkVBRE1FIGNsYWltcyB0byB1c2UgbmV1cm9kZXNrLWZyZWVzdXJmZXIgY29udGFpbmVyIGZyb20gLy8vcmVwcm9uaW0vY29udGFpbmVycyBidXQgcnVuIHJlY29yZHMgcmVmZXJlbmNlIGNvZGUvY29udGFpbmVycy9wbG90dGluZy5zaWYgKHdoaWNoIGRvZXMgbm90IGV4aXN0KSwgYW5kIE1ha2VmaWxlIHVzZXMgbm8gY29udGFpbmVyIGF0IGFsbC4gRG9jdW1lbnRhdGlvbiBpcyBjb250cmFkaWN0b3J5IGFuZCBtaXNsZWFkaW5nLiJ9LCJzdGFtcGVkLWNoZWNrbGlzdDpzaG91bGQvMDAxIjp7InZhbHVlIjoieWVzIiwicmVhc29uIjoiR2l0IHVzZWQgZm9yIGNvZGUvY29uZmlnLCBnaXQgc3VibW9kdWxlcyBmb3IgaW5wdXRzIChkczAwNzExNiBtb2R1bGUpLiBTaW5nbGUgdmVyc2lvbiBjb250cm9sIHN5c3RlbSBhY3Jvc3MgY29tcG9uZW50cy4ifSwic3RhbXBlZC1jaGVja2xpc3Q6c2hvdWxkLzAwMiI6eyJ2YWx1ZSI6InllcyIsInJlYXNvbiI6Ii5naXRodWIvd29ya2Zsb3dzL3JlcnVuLnltbCByZS1leGVjdXRlcyB0aGUgd29ya2Zsb3cgb3IgcmVidWlsZHMgdGhlIGVudmlyb25tZW50LiJ9LCJzdGFtcGVkLWNoZWNrbGlzdDpzaG91bGQvMDAzIjp7InZhbHVlIjoieWVzIiwicmVhc29uIjoiNCBraW5kcyBvZiBjb21wb25lbnQgbGl2ZSBpbiBkaXN0aW5jdCBwbGFjZXM6IGlucHV0cyBpbiBzb3VyY2VkYXRhLCBzb3VyY2VkYXRhL2RzMDA3MTE2OyBjb2RlIGluIE1ha2VmaWxlLCBjb2RlOyBkZXJpdmVkIGluIGZpZ3VyZXMsIHJlc3VsdHM7IGVudmlyb25tZW50IGluIGNvZGUvY29udGFpbmVycy5qc29uLCByZXF1aXJlbWVudHMubG9jayJ9LCJzdGFtcGVkLWNoZWNrbGlzdDpzaG91bGQvMDA5Ijp7InZhbHVlIjpudWxsLCJyZWFzb24iOiJOL0E6IE5vIHJlc3RyaWN0ZWQgZGF0YSBvciBzb2Z0d2FyZSBpbiB0aGlzIG9iamVjdDsgYWxsIGNvbXBvbmVudHMgYXJlIHB1YmxpYy4ifSwic3RhbXBlZC1jaGVja2xpc3Q6c2hvdWxkLzAwNCI6eyJ2YWx1ZSI6Im5vIiwicmVhc29uIjoiQ0kgd29ya2Zsb3cgcnVucyBvbiB1YnVudHUtbGF0ZXN0IGJ1dCBkb2VzIG5vdCBzcGF3biBkaXNwb3NhYmxlIGNvbnRhaW5lcnMgcGVyIGV4ZWN1dGlvbi4gTWFrZWZpbGUgaGFzIG5vIGNvbnRhaW5lciBzdXBwb3J0LiJ9LCJzdGFtcGVkLWNoZWNrbGlzdDpzaG91bGQvMDA1Ijp7InZhbHVlIjoibm8iLCJyZWFzb24iOiJNYWtlZmlsZSBhc3N1bWVzIHN5c3RlbSBQeXRob24gYW5kIHBpcCBpbnN0YWxsIGludG8gLnZlbncuIE5vIGRpc3Bvc2FibGUgZW52aXJvbm1lbnQgcGVyIHJ1bi4gQ0kgd29ya2Zsb3cgcmV1c2VzIHVidW50dS1sYXRlc3QgYnV0IGRvZXMgbm90IGZ1bGx5IGlzb2xhdGUgZWFjaCBleGVjdXRpb24uIn0sInN0YW1wZWQtY2hlY2tsaXN0OnNob3VsZC8wMDYiOnsidmFsdWUiOiJ5ZXMiLCJyZWFzb24iOiIuZ2l0aHViL3dvcmtmbG93cy9yZXJ1bi55bWwgcmUtZXhlY3V0ZXMgdGhlIHdvcmtmbG93IG9yIHJlYnVpbGRzIHRoZSBlbnZpcm9ubWVudC4ifSwic3RhbXBlZC1jaGVja2xpc3Q6c2hvdWxkLzAwNyI6eyJ2YWx1ZSI6Im5vIiwicmVhc29uIjoicmVxdWlyZW1lbnRzLmxvY2sgaXMgYXJjaGl2ZWQgYnV0IGNvZGUvY29udGFpbmVycy9wbG90dGluZy5zaWYgcmVmZXJlbmNlZCBpbiBydW4gcmVjb3JkcyBkb2VzIG5vdCBleGlzdDsgY29udGFpbmVycy5qc29uIGhhcyBkdW1teSB2YWx1ZXMuIENvbnRhaW5lciBpbWFnZSBhcnRpZmFjdHMgYXJlIG5vdCBhcmNoaXZlZC4ifSwic3RhbXBlZC1jaGVja2xpc3Q6c2hvdWxkLzAwOCI6eyJ2YWx1ZSI6Im5vIiwicmVhc29uIjoiTm8gZG9jdW1lbnRlZCBwcm9jZXNzIGZvciB1cGRhdGluZyBlbnZpcm9ubWVudCBzcGVjcy4gKER1cGxpY2F0ZSBvZiBtdXN0LzAxNC4pIn0sInN0YW1wZWQtY2hlY2tsaXN0Om1heS8wMDEiOnsidmFsdWUiOiJ5ZXMiLCJyZWFzb24iOiIxIGV4dGVybmFsIGNvbXBvbmVudChzKSBhcmUgbGlua2VkIGFzIG1vZHVsZXM6IHNvdXJjZWRhdGEvZHMwMDcxMTYifSwic3RhbXBlZC1jaGVja2xpc3Q6bWF5LzAwMiI6eyJ2YWx1ZSI6bnVsbCwicmVhc29uIjoiTm8gcHJvYmUgY292ZXJzIHRoaXMgaXRlbTsgYSByZWFkaW5nIG9mIHRoZSBvYmplY3QgaXMgcmVxdWlyZWQuIn0sInN0YW1wZWQtY2hlY2tsaXN0Om1heS8wMDMiOnsidmFsdWUiOm51bGwsInJlYXNvbiI6Ik5vIHByb2JlIGNvdmVycyB0aGlzIGl0ZW07IGEgcmVhZGluZyBvZiB0aGUgb2JqZWN0IGlzIHJlcXVpcmVkLiJ9LCJzdGFtcGVkLWNoZWNrbGlzdDptYXkvMDA0Ijp7InZhbHVlIjpudWxsLCJyZWFzb24iOiJObyBwcm9iZSBjb3ZlcnMgdGhpcyBpdGVtOyBhIHJlYWRpbmcgb2YgdGhlIG9iamVjdCBpcyByZXF1aXJlZC4ifSwic3RhbXBlZC1jaGVja2xpc3Q6bWF5LzAwNSI6eyJ2YWx1ZSI6bnVsbCwicmVhc29uIjoiTm8gcHJvYmUgY292ZXJzIHRoaXMgaXRlbTsgYSByZWFkaW5nIG9mIHRoZSBvYmplY3QgaXMgcmVxdWlyZWQuIn19fQ%3D%3D>

---

## Stamp

Produced by `assess-alignment-with-stamped-principles` 0.2.0 with `stamped-conventions` 0.2.0, checklist 0.3.1 (`stamped-checklist-schema@v0.3.1`, `af259bad`), on <https://github.com/con/stamped-eval-fixture-r0.git> at commit `a230dc27f16d3d53964c317ac52d53a059f98fde`, 2026-10-13, claude-code / claude-haiku-4-5-20251001.

Probe output: `2026-10-13-probes.json`.

---

## Response JSON

Full per-item answers, evidence, and metadata: `2026-10-13-response.json`.
