# Prefer inspectable serializers

The default registry writes JSON, bytes, NumPy arrays, NumPy array mappings,
and optional PyVista, Torch, Pandas, and Polars values in ordinary files.
Arbitrary Python values use required compressed joblib output as the sole
last-resort serializer; direct pickle fallback is intentionally absent. This
preserves convenient caching without making opaque serialization the normal
format.
