# Architecture

One process. `svc/api.py` owns the HTTP surface, `svc/db.py` owns every
statement that reaches Postgres, and nothing else opens a connection.

Writes go through `insert_order`, which is the only place a ULID is minted. Reads
go through the three `select_*` helpers. There is no ORM and there is not going
to be one: the ordering guarantees the read path depends on are expressed in SQL
that an ORM would rewrite.
