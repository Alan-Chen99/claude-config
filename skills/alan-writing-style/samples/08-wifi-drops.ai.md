# Evening wifi drops — DFS radar detection

**Symptom.** Every wireless device drops for 30-60 seconds, several times between 19:00 and 22:00, most evenings for about three weeks. Wired devices unaffected.

**Checked first, none of them the cause.**

- Router firmware: current.
- DHCP lease pool: 30 of 200 leases used.
- 2.4 GHz channel congestion: neighbours on channels 1 and 11, router on 6; moving the router to 1 made no difference.
- Router temperature: warm at 51C, but within spec per the vendor page.

**Cause.** The router log shows a radar-detection (DFS) event on the 5 GHz channel at every drop. The 5 GHz radio was on channel 100, which is a DFS channel: when radar is detected the radio must leave the channel and stay off for 60 seconds. The source of the radar-like signal is unknown. The timing matches a nearby airport approach pattern, but that is only the timing — not verified.

**Fix.** Pinned the 5 GHz radio to channel 36, which is not a DFS channel. No drops in the nine days since. The cost is throughput: channel 36 is shared with two neighbours, and peak throughput on the laptop nearest the router went from about 600 to about 450 Mbps, measured with iperf3 to the wired desktop.

**Not done.** Separate SSIDs per band, which would let the 2.4 GHz band keep devices connected through a DFS event. Rejected because some devices then stick to 2.4 GHz permanently.

**How to recognise it again.** Router log lines containing "DFS" or "radar" immediately before a drop, and a drop that lasts exactly 60 seconds.
