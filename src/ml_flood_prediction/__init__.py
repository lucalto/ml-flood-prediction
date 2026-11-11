from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _summarize_raster(path: Path) -> dict[str, Any]:
    """Read a raster file and return basic metadata for reporting."""
    try:
        import rasterio
    except ImportError as exc:  # pragma: no cover - runtime dependency check
        raise RuntimeError("rasterio is required to inspect flood rasters.") from exc

    with rasterio.open(path) as src:
        band = src.read(1)
        return {
            "name": path.name,
            "width": int(src.width),
            "height": int(src.height),
            "count": int(src.count),
            "crs": str(src.crs) if src.crs else None,
            "dtype": str(src.dtypes[0]),
            "bounds": {
                "left": float(src.bounds.left),
                "bottom": float(src.bounds.bottom),
                "right": float(src.bounds.right),
                "top": float(src.bounds.top),
            },
            "min": float(band.min()),
            "max": float(band.max()),
            "mean": float(band.mean()),
            "nodata": None if src.nodata is None else float(src.nodata),
        }


def summarize_data_dir(data_dir: str | Path = "data-generated") -> dict[str, Any]:
    """Summarize the raster inputs in a project data directory."""
    root = Path(data_dir)
    if not root.exists():
        raise FileNotFoundError(f"Data directory not found: {root}")

    raster_files = sorted(root.glob("*.tif"))
    if not raster_files:
        raise FileNotFoundError(f"No GeoTIFF files were found in {root}")

    return {
        "data_dir": str(root),
        "raster_count": len(raster_files),
        "rasters": [_summarize_raster(path) for path in raster_files],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Summarize the flood-susceptibility raster inputs used in this project.",
    )
    parser.add_argument(
        "--data-dir",
        default="data-generated",
        help="Directory containing the GeoTIFF layers for the project (default: data-generated).",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional path for a JSON summary file.",
    )
    args = parser.parse_args(argv)

    try:
        summary = summarize_data_dir(args.data_dir)
    except (FileNotFoundError, RuntimeError) as exc:
        parser.exit(1, f"Error: {exc}\n")

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
