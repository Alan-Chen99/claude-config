Piece: a note to self after investigating why the home wifi drops every evening, kept in a personal notes folder so it does not have to be investigated again. Register: doc. The reader is the writer, months later, who will have forgotten the details; the note is the only record.

Available material:
- Symptom: wifi on every device drops for 30-60 seconds, several times between 19:00 and 22:00, most evenings for about 3 weeks. Wired devices fine.
- Checked first, not the cause: router firmware (current); DHCP lease pool (30 of 200 used); channel congestion on 2.4 GHz (neighbours on channels 1 and 11, router on 6, changing to 1 made no difference); router temperature (warm, 51C, within spec per the vendor page).
- Found: the router log shows a radar-detection event (DFS) on the 5 GHz channel at every drop. The 5 GHz radio is on a DFS channel (100); when radar is detected the radio must leave the channel and stay off for 60 seconds. The neighbour's weather-radar-like source is unknown; the timing matches a nearby airport approach pattern? -- not verified, just the timing.
- Fix: pinned the 5 GHz radio to a non-DFS channel (36). No drops in the 9 days since. Cost: channel 36 is shared with two neighbours, so peak throughput went from about 600 to about 450 Mbps on the laptop nearest the router (measured with iperf3 to the wired desktop).
- Not done: separate SSIDs per band, which would let the 2.4 GHz band keep devices connected during a DFS event; rejected because some devices then stick to 2.4 GHz permanently.
- How to recognise it again: `dmesg`-style router log lines with "DFS" or "radar" right before a drop; the drop is exactly 60 seconds.
