# Skill-use friction notes

- **Output naming conflicted with the case handoff.** The skill says to write `<date>-response.json`, while the assignment says “Complete the supplied response.json.” I completed the supplied file and used dated names for the other products.
- **The report count template omits not-applicable.** It says “MUST: n met / n partial / n unmet / n not-checked,” while the verdict vocabulary includes `not-applicable`. I added an explicit N/A count and retained the full denominator.
- **Extra-item spelling differs.** The probe is named `license-declared` and the skill calls it that, but the response-format example says `licence-declared`. I used the probe’s `license-declared` key.
- **Failure-log retention needs a non-default duct setting.** The assignment says “including failures,” but duct removes logs for quick failures by default. I had to rerun a failed, read-only annex query with `--fail-time 0` to retain its log.
- **The capture has two labels.** The supplied response points to `object-capture/manifest.json`; the case prompt calls it “the capture manifest.” The URI resolved the ambiguity, but using one label consistently would make the preservation boundary quicker to identify.
