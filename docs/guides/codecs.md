# Output codecs

Default codecs favor ordinary, inspectable files. They are selected from the
value itself, not from a user-supplied type tag.

| Value | Artifact |
| --- | --- |
| JSON-compatible values | `output.json` |
| `bytes` or `bytearray` | `output.bin` |
| NumPy array | `output.npy` |
| String-keyed mapping of NumPy arrays | `output.npz` |
| PyVista dataset | a VTK file such as `output.vtu` |
| Torch tensor | `output.pt` |
| Pandas or Polars dataframe | `output.parquet` plus a format marker |
| Other Python values | `output.joblib.gz` |

PyVista, Torch, Pandas, Polars, and NumPy are optional adapters. Reading an
entry that needs an unavailable adapter raises `ModuleNotFoundError`; it does
not guess a fallback format. The required joblib fallback is intended for
trusted local cache roots only. Do not read cache directories controlled by an
untrusted party.

Pass `inputs_writer`, `output_writer`, and `output_reader` directly to a
decorator for one local policy, or pass them to a storage constructor when
several calls should share the same policy. A custom writer owns only its
artifact; storage still owns `metadata.json`, locking, publication, and LRU
indexing.
