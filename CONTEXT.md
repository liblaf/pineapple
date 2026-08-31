# liblaf.cache

`liblaf.cache` provides reusable local results for expensive computation. Its
terms distinguish disposable cached results from durable application data.

## Language

**Cache entry**:
A published directory containing one reusable result and its inspection data.
_Avoid_: Record, object, shelf

**Key**:
A deterministic caller-provided string that identifies one cache entry.
_Avoid_: Path, filename

**Owner**:
The active caller computing an uncached key while holding that key's lock.
_Avoid_: Leader, writer
