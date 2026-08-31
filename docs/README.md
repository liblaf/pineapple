# Cache

`liblaf.cache` stores disposable computation results as inspectable local
directories. Publication is atomic, decorated calls are single-flight while a
live owner holds a key lock, and LRU pruning keeps the cache bounded.

Begin with [storage and entries](guides/storage.md), then read
[output codecs](guides/codecs.md) and [single-flight work](concepts/single-flight.md).
The [API reference](reference/liblaf/cache/README.md) documents the public
module; the root README contains installation and short usage examples.
