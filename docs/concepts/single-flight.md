# Single-flight work

A cached function is single-flight while one live owner holds its per-key
local-filesystem lock. Waiters acquire the same lock, re-check the entry, and
reuse the published result instead of repeating the computation.

This is deliberately not exactly-once execution. A process can be cancelled
or crash after performing external side effects and before publishing an
entry; a later owner may then compute the key again. Cached functions should
therefore be idempotent or isolate non-repeatable work behind a durable system.

The lock and atomic publish boundary are local-filesystem mechanisms. They are
not a distributed lock and should not be assumed to provide a network-filesystem
or multi-host consistency contract.
