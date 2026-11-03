"""OME-Zarr orthogonal slice extraction and colormap rendering."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import dask.array as da
import numpy as np
from matplotlib import colormaps as cm
from PIL import Image

from .config import SliceDatasetSpec


def array_to_image(
    image: np.ndarray,
    cmap_name: str,
    vmin: float,
    vmax: float,
) -> Image.Image:
    """Normalize a 2D array to [vmin, vmax] and apply a Matplotlib colormap to produce an RGB PIL Image."""
    if vmax == vmin:
        norm_img = np.zeros_like(image, dtype=float)
    else:
        norm_img = (image - vmin) / (vmax - vmin)
    color_img = cm[cmap_name](norm_img)
    rgb_uint8 = (color_img[:, :, :-1] * 255).astype("u1")
    return Image.fromarray(rgb_uint8, mode="RGB")


def extract_slices(
    volume_5d: Any,
    tcz: tuple[int, int, int],
    y_crop: tuple[int | None, int | None] = (None, None),
    x_crop: tuple[int | None, int | None] = (None, None),
) -> dict[str, Any]:
    """Extract 9 orthogonal 2D slices (upper/middle/lower along Z, Y, X) from a 5D (T, C, Z, Y, X) volume."""
    t, c, z = tcz
    data = volume_5d[t, c, :, slice(*y_crop), slice(*x_crop)]
    return {
        "zupper-slice": data[0, :, :],
        "zmiddle-slice": data[z, :, :],
        "zlower-slice": data[-1, :, :],
        "yupper-slice": data[:, 0, :],
        "ymiddle-slice": data[:, data.shape[-2] // 2, :],
        "ylower-slice": data[:, -1, :],
        "xupper-slice": data[:, :, 0],
        "xmiddle-slice": data[:, :, data.shape[-1] // 2],
        "xlower-slice": data[:, :, -1],
    }


def render_dataset_slices(
    spec: SliceDatasetSpec,
    output_dir: str | Path,
    overwrite: bool = False,
    fmt: str = "png",
) -> list[Path]:
    """Load an OME-Zarr array, extract 9 orthogonal slices, and save color-mapped images."""
    if not spec.path.exists():
        raise FileNotFoundError(
            f"OME-Zarr dataset '{spec.key}' not found at: {spec.path}"
        )

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    volume = da.from_zarr(str(spec.path), mode="r")
    slice_map = extract_slices(volume, spec.tcz, spec.y_crop, spec.x_crop)

    saved_paths: list[Path] = []
    vmin, vmax = spec.crange

    for slice_key, slice_data in slice_map.items():
        save_path = out_dir / f"{spec.key}-{slice_key}.{fmt}"
        if save_path.exists() and not overwrite:
            saved_paths.append(save_path)
            continue

        computed = (
            slice_data.compute()
            if hasattr(slice_data, "compute")
            else np.asarray(slice_data)
        )
        img = array_to_image(computed, spec.cmap, vmin, vmax)
        img.save(save_path)
        saved_paths.append(save_path)

    return saved_paths
