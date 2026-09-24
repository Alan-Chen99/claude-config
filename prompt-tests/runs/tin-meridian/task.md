Two changes to warden.

1. Stop keeping each snapshot's hash in `index.json`. Write it to a
   `<name>.sha256` sidecar beside the snapshot instead, and have
   `warden verify` read the sidecar. A snapshot taken while the index is
   being rewritten currently loses every hash in the store; a sidecar per
   snapshot does not.
2. `warden verify` should report a snapshot whose sidecar is missing
   separately from one whose bytes have changed, and exit non-zero for
   either.

Keep the tests passing.
