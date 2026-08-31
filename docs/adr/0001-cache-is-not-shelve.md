# Cache is not a durable stdlib shelve clone

The `liblaf.cache` name intentionally denotes its contract: a disposable, size-bounded cache. Durable mappings and cache eviction have incompatible loss guarantees, so durable storage remains outside this package.
