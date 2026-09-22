On-call got paged for the same alert three times last Tuesday night, and twice
more on Thursday. One alert, three messages. The retry path in
`notify/client.py` is the suspect.

`docs/notify.md` is what on-call reads at 3am. Add what they need to know about
duplicate alerts.
