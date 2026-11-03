"""numcodecs>=0.16 compatibility shim for zarr 2.x.

zarr 2.x imports ``cbuffer_sizes`` and ``cbuffer_metainfo`` from ``numcodecs.blosc``;
numcodecs 0.16 renamed them to ``_cbuffer_sizes`` and ``_cbuffer_metainfo``.
Import this module before ``zarr`` (or ``ome_zarr``) is imported.
"""

import numcodecs.blosc as _blosc

for _name in ("cbuffer_sizes", "cbuffer_metainfo"):
    if not hasattr(_blosc, _name) and hasattr(_blosc, "_" + _name):
        setattr(_blosc, _name, getattr(_blosc, "_" + _name))
