# Eval platforms: what exists, and what we should adopt

**Status:** survey, 2026-10-13. Decision below is a recommendation, not yet acted on.
**Why:** the harness in `evals/stamped/` is ours, and the moment judgement mutants
need to run against several models it starts growing into a framework. Better to
adopt one than to write one.

## What we actually need

In rough order of how hard it is to find:

1. **Build a fresh research object per sample.** Our samples are git repositories
   with one injected defect, built by `fixtures/make_r0_object.py` plus
   `mutants/*.py`. Nothing off the shelf does this, and nothing should: it is
   domain-specific and it is the part that makes the eval meaningful.
2. **Run an agent with file and shell tools against that object, isolated.**
3. **Score a structured product** — 31 item verdicts, their evidence, and whether
   the report names the specific defect — not a text-similarity metric.
4. **Several models, including local ones**, because the skills must not assume
   frontier judgement ([evals.md §4](evals.md#4-conditions)).
5. **Aggregate with denominators**, per item and per principle, never one score.
6. **Human review of transcripts**, because the friction report is half the point.

(3) is the unusual requirement: most frameworks are built to grade a *text answer*,
and ours is "did these 31 verdicts and this prose match a reference".

## The options

| Tool | Shape | Local models | Sandbox | pytest | Fit for us |
|---|---|---|---|---|---|
| [**Inspect AI**](https://inspect.aisi.org.uk/) (UK AISI, MIT) | tasks + solvers + scorers, CLI and `eval()` Python API, `inspect view` log viewer | 20+ providers; HuggingFace, vLLM, SGLang, [Ollama](https://inspect.aisi.org.uk/providers.html) | Docker, Kubernetes, Modal, Proxmox, Vagrant | via its `eval()` API inside a test | **Best fit for the outer loop.** `react()` agents with bash/python/text-editor tools, `model_graded_qa()` for the judgement half, sandboxes that match our "fresh container per run", and a transcript viewer we would otherwise build. |
| [**deepeval**](https://deepeval.com/docs/introduction) | metrics + thresholds, `assert_test()`, `deepeval test run` | Ollama via `deepeval set-ollama --model=…` | no | **native** — it *is* pytest | Good runner, wrong metrics: its library is answer-quality and RAG shaped (faithfulness, relevance), and our grader is a structured comparison. Would be a wrapper, not a win. |
| [**pytest-evals**](https://github.com/AlmogBaku/pytest-evals) | `@pytest.mark.eval` cases + `@pytest.mark.eval_analysis` aggregate | whatever your code calls | no | **native, minimal** | **Adopt now.** It turns "13 mutants × 2 models, assert per-item sensitivity ≥ threshold" into ordinary pytest with a report, without taking over the suite we already have. |
| [**promptfoo**](https://www.promptfoo.dev/docs/configuration/expected-outputs/) | one `promptfooconfig.yaml`, `promptfoo eval` | Ollama provider | no | no (JS/CLI) | Prompt-centric rather than object-centric. Worth borrowing its **`llm-rubric`** idea for grading "did the report name the defect" if substring matching proves brittle. |

Mutation testing *of a grader* has no off-the-shelf tool. The closest analogues are
`mutmut` and `cosmic-ray` for Python code, which mutate source and demand the test
suite notice; our mutants are that idea applied to a research object, and the
assessor is the test suite.

## Recommendation

1. **Keep** the object generators (`fixtures/`, `mutants/`), the structured scorer
   (`blind_run.py compare`, `judgement_calibrate.py score`) and the response format.
   No framework models "a filled STAMPED checklist", and `stamped-conventions` is
   where that lives.
2. **Adopt `pytest-evals` now**, for the aggregation layer: one eval case per
   (mutant × model), one analysis test asserting the done criteria of [evals.md §10](evals.md#10-done-criteria). Cheap,
   reversible, and it keeps `tox -e stamped-evals` as the single entry point.
   **Done, 2026-10-14** (`pytest-evals==0.3.4`, `evals/stamped/tests/test_eval_cases.py`): one case per scripted mutant plus the clean-object control, one case per *recorded* judgement round — model runs cannot be re-run for free, so the cases read what was recorded and hold it to the gate — and one analysis test per criterion. It paid for itself the hour it landed: two mutants had been producing collateral item flips that `calibrate.py` printed and nothing gated on, and the recorded judgement rounds carried no model label at all, so the per-tier criterion could not be read against them.
3. **Adopt Inspect AI at phase 3**, when the outer loop needs containers per run and
   more than one model tier. Map our pieces onto its vocabulary:
   - *dataset* → one sample per (use case or mutant), each carrying the path of the
     object a `setup` step builds;
   - *solver* → the blind-run prompt from `blind_run.py prepare`, run by `react()`
     with bash and file tools;
   - *scorer* → ours, wrapped: `compare` for the verdicts, plus `model_graded_qa()`
     for "did the report name the defect";
   - *sandbox* → Docker, which is the E.1 we ask of the projects we assess.
4. **Do not** adopt deepeval or promptfoo as the harness; borrow `llm-rubric` from
   the latter if keyword scoring proves brittle in the judgement mutants.

What this buys: the two things we currently cannot do — run the same eval against a
local model, and look at a transcript without reading JSONL by hand — without
rewriting the parts that encode what STAMPED means.

## Sources

- [Inspect AI](https://inspect.aisi.org.uk/) · [model providers](https://inspect.aisi.org.uk/providers.html) · [inspect_evals collection](https://github.com/UKGovernmentBEIS/inspect_evals)
- [DeepEval docs](https://deepeval.com/docs/introduction) · [unit testing in CI/CD](https://deepeval.com/docs/evaluation-unit-testing-in-ci-cd)
- [pytest-evals](https://github.com/AlmogBaku/pytest-evals)
- [promptfoo assertions and metrics](https://www.promptfoo.dev/docs/configuration/expected-outputs/)
- [AI agent eval frameworks 2026](https://www.digitalapplied.com/blog/ai-agent-eval-frameworks-testing-guide-2026) (overview, vendor-neutral)
