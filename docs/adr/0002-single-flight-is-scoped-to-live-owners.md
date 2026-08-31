# Single-flight is scoped to live owners

Per-key local filesystem locks prevent duplicate work while an owner remains alive, and waiters re-check after acquiring the lock. A crash or cancellation permits a later computation because exactly-once side-effect execution cannot be provided by a filesystem cache.
