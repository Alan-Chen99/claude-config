# warden

`warden` writes a snapshot of a directory to a snapshot store and checks later
that the bytes have not moved under it.

## Example

    $ warden snapshot --name nightly ./src
    wrote nightly
    $ warden list
    nightly  2026-09-01T03:00:00Z  4 files
    $ warden verify
    ok

A snapshot directory holds one file per snapshot.
