"""Inspectable default output codecs with optional scientific adapters."""

from __future__ import annotations

import importlib
import pathlib
import sys
from typing import Any

import joblib
import msgspec

from liblaf.cache._src.io.json import read_json_output_sync, write_json_output_sync
from liblaf.cache._src.io.numpy import (
    read_numpy_output_sync,
    require_numpy,
    write_numpy_output_sync,
)


def _optional_module(name: str) -> Any | None:
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError as error:  # pragma: no cover - optional dependency
        if error.name != name:
            raise
        return None


def _module_for_value(name: str, value: Any) -> Any | None:
    module = sys.modules.get(name)
    if module is not None:
        return module
    if type(value).__module__.partition(".")[0] != name:
        return None
    return _optional_module(name)


def _remove_previous_outputs(folder: pathlib.Path) -> None:
    for name in (
        "output.json",
        "output.npy",
        "output.npz",
        "output.bin",
        "output.joblib.gz",
        "output.pt",
        "output.parquet",
        "output.parquet.format",
        "output.vtu",
        "output.vtp",
        "output.vtm",
        "output.vti",
    ):
        (folder / name).unlink(missing_ok=True)


def _write_numpy_mapping(folder: pathlib.Path, output: dict[Any, Any], np: Any) -> bool:
    if not output or not all(isinstance(key, str) for key in output):
        return False
    if not all(
        isinstance(value, np.ndarray) and not value.dtype.hasobject
        for value in output.values()
    ):
        return False
    np.savez_compressed(folder / "output.npz", **output)
    return True


def _pyvista_extension(output: Any, pv: Any) -> str | None:
    extensions = (
        ("UnstructuredGrid", ".vtu"),
        ("PolyData", ".vtp"),
        ("MultiBlock", ".vtm"),
        ("ImageData", ".vti"),
    )
    for name, extension in extensions:
        cls = getattr(pv, name, None)
        if cls is not None and isinstance(output, cls):
            return extension
    return None


def _write_optional_output(folder: pathlib.Path, output: Any) -> bool:
    pv = _module_for_value("pyvista", output)
    if pv is not None:
        extension = _pyvista_extension(output, pv)
        if extension is not None:
            output.save(folder / f"output{extension}")
            return True

    torch = _module_for_value("torch", output)
    tensor_type = getattr(torch, "Tensor", ()) if torch is not None else ()
    if torch is not None and isinstance(output, tensor_type):
        torch.save(output, folder / "output.pt")
        return True

    for module_name in ("pandas", "polars"):
        module = _module_for_value(module_name, output)
        dataframe = getattr(module, "DataFrame", ()) if module is not None else ()
        if module is not None and isinstance(output, dataframe):
            writer_name = "to_parquet" if module_name == "pandas" else "write_parquet"
            getattr(output, writer_name)(folder / "output.parquet")
            (folder / "output.parquet.format").write_text(module_name, encoding="utf-8")
            return True
    return False


def write_default_output_sync(folder: pathlib.Path, output: Any) -> None:
    """Write one output using the first matching inspectable format.

    Optional PyVista, Torch, Pandas, and Polars adapters are selected only
    when their dependency is installed. Arbitrary Python values use the
    required ``joblib`` last-resort codec.
    """
    _remove_previous_outputs(folder)
    if isinstance(output, (bytes, bytearray)):
        (folder / "output.bin").write_bytes(bytes(output))
        return
    np = _module_for_value("numpy", output)
    if np is not None and isinstance(output, np.ndarray) and not output.dtype.hasobject:
        write_numpy_output_sync(folder, output)
        return
    if (
        np is not None
        and isinstance(output, dict)
        and _write_numpy_mapping(folder, output, np)
    ):
        return
    try:
        write_json_output_sync(folder, output)
    except (TypeError, ValueError, msgspec.EncodeError):
        if _write_optional_output(folder, output):
            return
        joblib.dump(output, folder / "output.joblib.gz", compress=3)


def _read_npz(path: pathlib.Path) -> dict[str, Any]:
    np = require_numpy()
    with np.load(path, allow_pickle=False) as archive:
        return {key: archive[key] for key in archive.files}


def _read_torch(path: pathlib.Path) -> Any:
    torch = _optional_module("torch")
    if torch is None:
        message = "torch is required to read output.pt"
        raise ModuleNotFoundError(message)
    return torch.load(path, weights_only=False)


def _read_parquet(folder: pathlib.Path, path: pathlib.Path) -> Any:
    marker = folder / "output.parquet.format"
    module_name = marker.read_text(encoding="utf-8") if marker.exists() else "pandas"
    module = _optional_module(module_name)
    if module is None:
        message = f"{module_name} is required to read output.parquet"
        raise ModuleNotFoundError(message)
    return module.read_parquet(path)


def _read_pyvista(path: pathlib.Path) -> Any:
    pv = _optional_module("pyvista")
    if pv is None:
        message = "pyvista is required to read VTK output"
        raise ModuleNotFoundError(message)
    return pv.read(path)


def read_default_output_sync(folder: pathlib.Path) -> Any:
    """Read an output selected by its inspectable filename."""
    readers = (
        ("output.bin", lambda path: path.read_bytes()),
        ("output.json", lambda _path: read_json_output_sync(folder)),
        ("output.npy", lambda _path: read_numpy_output_sync(folder)),
        ("output.npz", _read_npz),
        ("output.joblib.gz", joblib.load),
        ("output.pt", _read_torch),
        ("output.parquet", lambda path: _read_parquet(folder, path)),
        ("output.vtu", _read_pyvista),
        ("output.vtp", _read_pyvista),
        ("output.vtm", _read_pyvista),
        ("output.vti", _read_pyvista),
    )
    for name, reader in readers:
        path = folder / name
        if path.exists():
            return reader(path)
    message = f"no output file found under {folder}"
    raise FileNotFoundError(message)


__all__ = ["read_default_output_sync", "write_default_output_sync"]
