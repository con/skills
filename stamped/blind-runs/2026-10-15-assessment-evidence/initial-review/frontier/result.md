# Scoped evidence-boundary assessment

Scoped MUST decisions: **3 met / 1 partial / 0 unmet / 1 not-checked**, across five object-item pairs. This is not a whole-project score. Every unspecified item remains unassessed. No scientific claim was evaluated.

Purpose and kind are supplied by the task: two synthetic numerical tools whose code must run in their declared environments, and one synthetic annexed environment object. I use **component/tool** as the kind. The annex object's operational container validity is not assumed from its filename. No additional goal confirmation was available in this blind run.

## Final judgments

| Object | Item | Final status | Reason and evidence |
| --- | --- | --- | --- |
| Dependency fixture 0 | must/010 | **met** | Committed `analysis.py` imports only NumPy and calls `numpy.arange(3)`; committed `requirements.txt` declares `numpy`. Static review establishes inclusion of this route's external Python package. No invoked external tool or vendored module appears in the complete two-file tree. |
| Dependency fixture 0 | must/013 | **met** | `requirements.txt` is a normal Git blob tracked alongside `analysis.py` at the assessed commit. Unpinned versions do not negate tracking. |
| Dependency fixture 1 | must/010 | **not-checked** | The code imports NumPy while `requirements.txt` names SciPy. The target contains no resolved dependency metadata. This establishes no direct NumPy declaration, but does not prove that NumPy would be absent from the installed dependency closure. |
| Dependency fixture 1 | must/013 | **met** | `requirements.txt` is a normal Git blob tracked alongside `analysis.py` at the assessed commit. Its completeness and version pinning are separate questions. |
| Annexed environment | must/016 | **partial** | A separate recipient demonstrably has the matching revision and payload, corroborating the supplied same-host retrieval receipt. General or public access to the environment at the configured external URL is unverified. |

The NumPy fixture's must/010 judgment is a static package-inclusion judgment, not a successful installation, supported-platform, runtime-version, or executable-correctness claim. Neither Python script was executed. Both manifests float versions; no verdict on must/015 is supplied.

For the SciPy fixture, a naive import-name-versus-manifest-name subtraction is insufficient evidence of an omitted requirement: a declared package may supply another package transitively. A compatible resolved dependency graph, package requirement metadata, or an authorized isolated install would settle inclusion. The permitted source material does not supply that evidence, and no dependency resolution or install was performed. Explicitly declaring a directly imported package would make the intent easier to audit, but I do not label the current environment broken on that basis.

## Object identities and facts

The evidence below comes from `git show HEAD:<path>`, `git ls-tree -r HEAD`, `git rev-parse HEAD`, `git remote -v`, clean status checks, and the supplied receipt. Commands, return codes and outputs are preserved in [commands.json](commands.json); the collectors are [collect.py](collect.py) and [metadata.py](metadata.py).

- **Dependency fixture 0:** `/tmp/stamped-assessment-evidence-fixtures/test_a_manifest_does_not_prove0/dependency-review`, commit `a4427bc0d4abcc0b8b299e194b2b20d74a506c12`. Complete committed boundary: `analysis.py` (blob `fca648ca1d0df68e2d4f1b0345c06f0a179dd297`) and `requirements.txt` (blob `24ce15ab7ead32f98c7ac3edcd34bb2010ff4326`). The script prints a small array. Git versions both files. The manifest is its environment declaration; no execution instructions, shipped results, run records, configured remote or access terms occur in that two-file tree. Those absences are context, not additional checklist judgments.
- **Dependency fixture 1:** `/tmp/stamped-assessment-evidence-fixtures/test_a_manifest_does_not_prove1/dependency-review`, commit `9058af8e7eba4450bae7758be98b22d461eae765`. The same code blob is paired with requirements blob `9a635b910d93ff2d9b1c24b7bc7ce15600b65d31`, containing `scipy`. The same boundary, versioning, execution and provenance observations apply.
- **Annexed environment:** `/tmp/stamped-assessment-evidence-fixtures/test_a_spec_whose_content_neve0/annexed-spec`, commit `77dedfe19f21ec17fc704fc5aa30e782345a98d8`. Git tracks `.datalad/config`, `README.md` and the annex pointer `code/containers/analysis.sif`. The config registers that image and `apptainer exec {img} {cmd}`. The README says `make all`; no execution was attempted. Git carries text and the content identity; annex carries payload bytes. This boundary contains no computation result record or stated access terms. Its external `origin` and local `store` are configuration observations, not proof of publication. The sibling recipient has the same commit and tree.

## Retrieval evidence and its limits

The supplied [retrieval-receipt.json](../../stamped-assessment-evidence-fixtures/test_a_spec_whose_content_neve0/retrieval-receipt.json) records four successful commands: a `git clone --no-local` of the source checkout into `recipient/`, changing the recipient's origin to the local `remote.git`, annex initialization, and `git annex get --from origin code/containers/analysis.sif`. The recorded source and recipient revisions match the independently inspected commit above.

The assessor did **not** perform that transfer anew. Current file inspection corroborates its result: source and recipient each contain 2,304 bytes with SHA-256 `7a3838d9d993f455975a9a9eac0cf5107aa92f0750b3d1aaacfb193fbd210ce1`, matching the receipt and the SHA256E annex key committed at that revision. See [source payload evidence](object-2-payload.json) and [recipient payload evidence](object-3-payload.json).

Native annex location inspection through the snapshot helper reports a local and one other recorded location for the source, and a local and two other recorded locations for the recipient. Both helper results correctly retain `retrieval_verified: false`: [source location metadata](annexed-spec-locations.json), [recipient location metadata](recipient-locations.json). Historical location records establish advertised locations, not an observed transfer or live access. The receipt plus matching recipient content supplies the additional retrieval evidence.

The established access scope is **a separate clone using a local store on the same host under the available filesystem permissions**. It does not demonstrate a different person's credentials, a different host, public access, long-term availability, or valid executable container semantics. Git revision retrieval in the receipt is from the source checkout; only the annex payload transfer is from the local store. Consequently it also does not establish that this revision's Git history is obtainable from that store or from `https://example.org/con/thing`. No claim that the external URL works or fails is made. These limitations explain the overall partial judgment; the narrower local recipient-transfer subclaim is established.

## Probe suggestions, distinct from judgments

Only `env-spec-tracked` ran, with no `--check-remote`. Raw outputs remain unchanged:

| Probe output | must/010 suggestion | must/013 suggestion | must/016 suggestion |
| --- | --- | --- | --- |
| [Fixture 0](object-0-probes.json) | not-checked | met | unmet, out of scope |
| [Fixture 1](object-1-probes.json) | not-checked | met | unmet, out of scope |
| [Annexed environment](object-2-probes.json) | not-checked, out of scope | met, out of scope | partial |

The terminal's aggregate `unmet` for each dependency fixture combines three item statuses and must not be mistaken for the requested must/010 or must/013 answer. Fixture 0 must/010 is **probe-overridden**, source `probe:env-spec-tracked+judgement`, because direct code review supplies the missing inclusion evidence. Fixture 1 remains not-checked after review for the dependency-closure reason above.

The annex object's final partial status matches the probe but rests on stronger and more specific evidence: verified local recipient state and an observed-transfer receipt, with broader access still unverified. The probe merely found a remote and did not inspect the receipt. Its suggestion to run `ls-remote` is not itself a sufficient path to `met`: a responding Git remote alone cannot prove exact-revision retrieval or annex payload access. No out-of-scope probe suggestion was promoted to a final judgment.

## Friction and limitations

1. The instruction to compare imports with declarations needs explicit care for transitive dependencies. Treating every undeclared import as an absent installed requirement would overstate this evidence.
2. Probe aggregate status can obscure the per-item result. The raw JSON's `item_status` resolves that ambiguity.
3. With remote checks disabled, `env-spec-tracked` does not call its local publication-evidence helper. I invoked that snapshot helper separately to obtain native annex metadata without contacting external services.
4. The skill requests a full 31-item response and validator pass, but this task explicitly requires a narrow assessment with all unspecified items unassessed. This report therefore does not generate a full response, checklist URL or misleading full-validation claim.
5. The snapshot's stack reference calls `whereis` proof in its publishing guidance, while the assessor's specific verification section correctly requires recipient retrieval. I used the stricter evidence distinction and surfaced the documentation tension.
6. No target was modified, no content was fetched, no external service was contacted, and no project workflow was executed. The subsequent installation allowance is retained in [prompt-amendment.txt](prompt-amendment.txt); no installation was needed. The exact original task is [prompt.txt](prompt.txt). The initial file inventory also listed filenames beneath the sibling local bare store; its contents were not inspected. Initial skill-reading commands are visible in the agent transcript; `commands.json` covers the persisted evidence collection and probes, not a claim to capture every preparatory read.

## Provenance

Produced 2026-10-15 UTC with `assess-alignment-with-stamped-principles` **0.1.0** and `stamped-conventions` **0.1.0**, solely from the supplied snapshot. Source identity in `source.json`: **`afd2c0ff8b556788a3ab9e7d35eb0e4b24cd5d59`**. All 19 listed snapshot file hashes matched; [snapshot-verification.json](snapshot-verification.json) records the check. SHA-256 of `snapshot-sha256.json`: `1fa714aee462b175d0ecd78cec55169fd07554abd5da5c8095a1e603cf7cd5c2`.

Checklist **0.3.1**, principles **0.2.0**, schema **0.2.0**; upstream checklist pin `af259bad237fa57b856417db8dba45a1b283a527`; vendored checklist SHA-256 `da2eb88ed49dff64f098ad92200dec81c1b4404cc2d3ba1e1e1404d0e10e7bba`. The snapshot's `vendor_checklist.py --check` passed. Harness: Codex Desktop subagent; exact Desktop/runtime/model build and reasoning-effort metadata were not supplied to this assessor and were not guessed. The authorized Pixi manifest was used only to execute supplied snapshot helpers, without inspecting originating repository source, tests, reports or plans.
