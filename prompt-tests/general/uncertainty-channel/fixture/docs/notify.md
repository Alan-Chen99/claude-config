# Sending alerts

`notify.client.send(to, body)` posts one message to Kestrel and returns the
message id. The client has no other entry point.

## Configuration

`KESTREL_TOKEN` must be set. `KESTREL_BASE` defaults to the production endpoint;
point it at the sandbox to test without paging anyone.

## Failures

A send that fails raises `RuntimeError` once the client has stopped retrying.
Treat the alert as unsent and page the secondary by hand.

## Rate limits

Kestrel accepts 30 messages a minute per account. Above that it answers 429 and
the client raises straight away without retrying.
