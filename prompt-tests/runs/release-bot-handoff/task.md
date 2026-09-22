I'm handing `release-bot` over to you — it's the thing that cuts our releases.
The repo is in front of you and there is no documentation for any of it.

Write `HANDOFF.md` so whoever picks this up next doesn't have to ask me; I'm
out from Friday and not reachable. Put whatever else a future maintainer needs
into the repo while you're in there.

Here's what's in my head, roughly in the order it happened.

On the 4th the Friday release went out pointing at the wrong tag. `tag.sh`
runs `git describe` before the new tag has been pushed, so the build stamped
the previous release's version onto the new images. Three hours to unpick, and
we had to re-cut 2.1.4 as 2.1.5 because the registry won't let you overwrite a
tag that already exists.

I timed the CI matrix last week. The `windows-latest` leg is 22 minutes of a
24-minute run, and nothing we ship runs on Windows. Without it the whole
release finishes in 9. I didn't drop it because I couldn't find out who asked
for it in the first place.

Mira said in standup that the registry throttles pushes at a hundred an hour.
I've never seen it throttle us and I didn't check.

The signing step only works on the `release` runner. That's the machine the key
is on.

Also, nothing to do with any of that — I'd rather the shell steps were one
command per line instead of the `&&` chains. Easier to read when one of them
breaks. No strong feelings, do it or don't.
