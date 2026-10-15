You are a fresh session working in a sandbox. Treat this as a normal user request.

**Working directory:** `/home/yoh/proj/CON/skills/.git-meta/scratch/stamped/r0-round2/r0-freesurfer-plot--skill-explicit--sonnet--r2` — a git (DataLad dataset) repository, already initialised and
committed. Everything you produce goes inside it. Do not write outside it.

**Your task:** /do-full-research-loop For the OpenNeuro dataset ds007116, plot brain volume against age, with the
grey-matter/white-matter volume ratio on a secondary axis, using the FreeSurfer
derivatives the dataset already ships.

Use the per-session ages. Carry it through to the figure.

The task above names a skill. It is installed in the sandbox under `.claude/skills/`, but there is no slash-command dispatcher here, so read its `SKILL.md` from disk and follow its procedure exactly as written, including the files it tells you to read. (Those skill files are tooling, not part of the project you are building: leave them out of what you commit.)

Operating constraints for this run:

1. `HOST-NOTES.md` in the sandbox describes the machine: read it first. It is the same
   file in every arm of this evaluation.
2. **The user is not available to answer questions.** Where you would ask, state the
   decision and your reason for it in the project instead, and carry on. Do not stop to
   wait for an answer.
3. **Do NOT read or search `/home/yoh/proj/CON/skills`**, with the single exception of your own working
   directory above (which happens to live under it, in an ignored scratch area):
   everything else under that path is off-limits for this run, including any plan,
   rubric, reference answer, or any other arm of this evaluation. This is a blind run:
   what you build is graded against criteria you must not see, and seeing them would
   destroy the measurement. Work from your task, the sandbox, and whatever you fetch from
   the network.
4. You may install packages, pull containers and fetch data. Permissions are wide open
   **inside the sandbox only**.
5. Carry the task through to its stated product. A plan with no result is a failed run.

**What to return as your final message** (keep it compact — it is read by a harness):

- What you built: the paths of the products, and the one-line method (tool, container,
  how the numbers were obtained).
- The numbers themselves: the per-subject table as text, if the task produced one.
- How you recorded what you did, if you did.
- Up to 5 bullets of **friction**: anything that was ambiguous, missing, contradictory,
  broken or slow — in the task, in the host, or in any instructions you were given —
  **quoting the wording or command at fault**. Be specific and critical; this is the most
  valuable part of your return.
