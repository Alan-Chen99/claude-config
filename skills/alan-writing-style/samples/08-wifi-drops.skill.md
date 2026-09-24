# Evening wifi drops

Wifi on every device drops for 30-60 seconds, several times between 19:00 and 22:00, most evenings for about three weeks; wired devices are fine. The router log shows a radar-detection (DFS) event on the 5 GHz channel at every drop: the radio was on channel 100, a DFS channel, and on radar detection it must leave the channel and stay off for 60 seconds. The radar source is unknown -- the timing matches a nearby airport approach pattern, not verified.

- Fix: pinned the 5 GHz radio to channel 36, which is not a DFS channel. No drops in the nine days since.
- Cost: channel 36 is shared with two neighbours, so peak throughput on the laptop nearest the router went from about 600 to about 450 Mbps, measured with iperf3 to the wired desktop.
- Not done: separate SSIDs per band, which would keep devices connected on 2.4 GHz through a DFS event. Rejected because some devices then stick to 2.4 GHz permanently.
- Recognising it again: "DFS" or "radar" in the router log right before a drop, and a drop of exactly 60 seconds.
- Checked first, not the cause: router firmware (current); DHCP lease pool (30 of 200 used); 2.4 GHz congestion (neighbours on channels 1 and 11, router on 6, moving to 1 made no difference); router temperature (51C, within spec per the vendor page).
