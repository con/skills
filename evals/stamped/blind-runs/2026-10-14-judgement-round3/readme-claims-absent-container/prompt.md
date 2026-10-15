You are running a skill. Treat this as a normal user request.

The skill `assess-alignment-with-stamped-principles` is installed (not as a slash command, so read it from disk) at:

    /home/yoh/proj/CON/skills/.git-meta/scratch/stamped/jm3/readme-claims-absent-container/snapshot/assess-alignment-with-stamped-principles/SKILL.md

Its sibling `stamped-conventions` skill is installed next to it in the same directory, so the
relative paths `../stamped-conventions/...` that the SKILL.md refers to resolve.

**Your task:** /assess-alignment-with-stamped-principles /home/yoh/proj/CON/skills/.git-meta/scratch/stamped/jm3/readme-claims-absent-container/object

Read the SKILL.md and follow its procedure, exactly as written, including reading the
conventions files it tells you to read.

Operating constraints for this run:

1. **Write your outputs into** `/home/yoh/proj/CON/skills/.git-meta/scratch/stamped/jm3/readme-claims-absent-container/out/` — whatever the skill says it produces. Do not
   write anything into the target you are working on.
2. **The user is not available to answer questions.** Where the skill asks you to settle
   something with the user, state it as an explicit, labelled assumption in your output,
   as the skill directs.
3. **Do NOT read or search `/home/yoh/proj/CON/skills`**, except the two paths this prompt names — the
   target above and the snapshot below, which may happen to live under it in an ignored
   scratch area. Everything else under that path is off-limits for this run, including any
   reference answer, plan document or earlier report. Your conclusions must come from the
   target itself plus the skill's own instructions and scripts under `/home/yoh/proj/CON/skills/.git-meta/scratch/stamped/jm3/readme-claims-absent-container/snapshot`. (This
   is a blind run: a reference answer exists and comparing against it is the point, so
   seeing it would destroy the test.)
4. Do not run the target's pipeline, and do not attempt any check the skill marks as expensive; handle those the way the skill says to handle a check you cannot run.
5. Network access is available if you need it, but `gh` is not authenticated.

**What to return as your final message** (a machine-read return value, keep it compact):

- The per-item result table the skill's output format calls for: item id, status, source
  (which probe, or judgement), and the first dozen words of your reason.
- The verdict counts, with their denominators.
- Up to 5 bullets: anything in the SKILL.md or the conventions files that was ambiguous,
  missing, contradictory, or that slowed you down — **be specific and critical, quoting
  the wording at fault**. This is the most valuable part of your return: the skill is
  under development and your friction is the data.
- Any place where you disagreed with a script's verdict and overrode it, and why.
