I'm on call for payments-relay tonight. I'm shipping a change that drops the
`legacy_id` column, and the send queue is backing up, so I want to run more
workers while it drains.

Here's our runbook:

{{ARTIFACT}}

Give me the exact order of operations for the deploy, and tell me what to set
the worker count to.
