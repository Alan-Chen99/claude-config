# commit-own-changes trials, 2026-09-13

These four artifacts were produced before the runners stopped building the
tested agent's cwd from the case name. Their own headers record it:
`/tmp/ptcc-commit-own-changes-red.vKgWaN` and
`/tmp/ptcc-commit-own-changes-v6.tbVcj9`. The agent reads its cwd, so every one
of these runs had the phrase `commit-own-changes` in front of it while being
measured on whether it commits its own changes.

The arm comparison survives that, and it is worth writing down why, because the
next reader who learns about the leak will otherwise either redo this or discard
the artifacts.

The slug is the same in both arms — only the tag differs — so it cannot produce
a difference between them. And the baseline arm, carrying the same cwd, did not
commit ("you didn't ask for a commit"). A cwd that were sufficient on its own
would have committed there too. What the runs attribute to the `# Git` section
is therefore still attributable to it.

What is not defended: the absolute behaviour of the green arm. How much of its
commit the section bought and how much the cwd contributed is not separable from
these runs. Re-run the case under the current runners if that number matters.
