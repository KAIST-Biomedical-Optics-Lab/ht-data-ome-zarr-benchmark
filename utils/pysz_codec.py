"""Thin numcodecs adapter that exposes SZ3 (pysz) with a pointwise absolute error bound.

Only the error mode used by the benchmark is exposed (ABS). The packet is self-describing:
a small header (dtype code, ndim, shape) precedes the SZ3 stream, and it is counted in the
compressed size like every other codec header.
"""
import struct

import numpy as np
from numcodecs.abc import Codec
from numcodecs.compat import ensure_bytes, ensure_ndarray, ndarray_copy
from pysz import sz, szConfig, szErrorBoundMode

_CODE_OF = {np.dtype("<f4"): 0, np.dtype("<f8"): 1}
_DTYPE_OF = {0: np.float32, 1: np.float64}


class SZ3Codec(Codec):
    """SZ3 (pysz) with an absolute error bound; float32/float64 arrays."""

    codec_id = "sz3_pysz"

    def __init__(self, abs_error: float = 1e-4):
        if not np.isfinite(abs_error) or abs_error <= 0:
            raise ValueError("abs_error must be finite and positive")
        self.abs_error = float(abs_error)

    def encode(self, buf):
        arr = ensure_ndarray(buf)
        code = _CODE_OF.get(arr.dtype.newbyteorder("<"))
        if code is None:
            raise ValueError(f"SZ3Codec supports float32/float64, got {arr.dtype}")
        arr = np.ascontiguousarray(arr, dtype=_DTYPE_OF[code])
        config = szConfig()
        config.errorBoundMode = szErrorBoundMode.ABS
        config.absErrorBound = self.abs_error
        compressed, _ = sz.compress(arr, config)
        header = struct.pack("<BB", code, arr.ndim) + struct.pack(f"<{arr.ndim}I", *arr.shape)
        return header + compressed.tobytes()

    def decode(self, buf, out=None):
        raw = ensure_bytes(buf)
        code, ndim = struct.unpack_from("<BB", raw, 0)
        shape = struct.unpack_from(f"<{ndim}I", raw, 2)
        payload = np.frombuffer(raw, dtype=np.uint8, offset=2 + 4 * ndim).copy()
        data, _ = sz.decompress(payload, _DTYPE_OF[code], shape)
        return ndarray_copy(data, out)
