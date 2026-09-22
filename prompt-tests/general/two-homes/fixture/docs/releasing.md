# Releasing

Roughly monthly, whenever the changelog has enough in it to be worth reading.

1. Check that `main` is green on CI. A red main is never released from.
2. Write the changelog entry at the top of `CHANGELOG.md`, newest first.
3. Bump the version in `pyproject.toml`.
4. Commit the changelog and the bump together, message `release: <version>`.
5. Run `./release.sh`. It builds the wheel, uploads it, and prints the artifact
   URL it uploaded to.
6. Paste that URL into the release thread.

If `release.sh` fails halfway, nothing has been uploaded yet — the upload is the
last thing it does — so fix the cause and run it again.
