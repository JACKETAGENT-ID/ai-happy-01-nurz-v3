"""nurz entry for make.fun ai-happy-01 — the tortoise who finally wins.

Concept: a joyful old tortoise on a red skateboard, wearing a tiny gold
party hat, overtaking three astonished hares at sunset. Storybook warmth,
one clear joke, readable even as a thumbnail.

This program is deliberately boring on purpose: the artwork ships inside
the repo as ``image.png`` and we copy it byte-for-byte to the output
directory. Two runs therefore always produce identical bytes — there is
no clock, no randomness and no re-encoding anywhere in the path.

Validation happens before the copy. We check the PNG signature, walk
the first chunk to read the IHDR dimensions, and enforce the competition
limits (<= 1024 x 1024 px, <= 1,048,576 bytes) so a corrupt or oversized
asset fails loudly instead of submitting something invalid.
"""

from __future__ import annotations

import os
import shutil
import struct
import sys
from pathlib import Path

# Competition limits for ai-happy-01.
MAX_BYTES = 1_048_576
MAX_WIDTH = 1024
MAX_HEIGHT = 1024

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
# IHDR is always the first chunk: 8-byte signature, then a 4-byte length,
# the literal b'IHDR', then width and height as big-endian uint32.
IHDR_OFFSET = 8
IHDR_MIN_SPAN = 8 + 4 + 4 + 13  # signature + length + type + IHDR payload


class AssetError(RuntimeError):
    """Raised when the bundled artwork does not pass validation."""


def parse_ihdr_dimensions(blob: bytes) -> tuple[int, int]:
    """Return (width, height) parsed directly from the PNG IHDR chunk.

    This is a structural read only — no decompression, no CRC work. We
    confirm the signature and the chunk label, then unpack the two
    big-endian dimension fields that the PNG spec fixes at bytes 16..24.
    """
    if len(blob) < IHDR_MIN_SPAN:
        raise AssetError(f"file too short to be a PNG ({len(blob)} bytes)")
    if not blob.startswith(PNG_SIGNATURE):
        raise AssetError("missing PNG signature — not a PNG file")
    chunk_type = blob[IHDR_OFFSET + 4 : IHDR_OFFSET + 8]
    if chunk_type != b"IHDR":
        raise AssetError(f"first chunk is {chunk_type!r}, expected b'IHDR'")
    width, height = struct.unpack(">II", blob[16:24])
    if width == 0 or height == 0:
        raise AssetError(f"nonsensical IHDR dimensions: {width}x{height}")
    return width, height


def sanity_check_chunks(blob: bytes) -> None:
    """Walk chunk headers far enough to confirm a plausible PNG skeleton.

    CRC-free by design: we only verify that chunk lengths stay inside the
    file and that an IEND terminator exists. It catches truncated copies
    and accidental text-file substitutions without needing a decoder.
    """
    pos = IHDR_OFFSET
    saw_iend = False
    # A generous bound so a malformed length can never loop forever.
    for _ in range(4096):
        if pos + 8 > len(blob):
            break
        (length,) = struct.unpack(">I", blob[pos : pos + 4])
        chunk_type = blob[pos + 4 : pos + 8]
        next_pos = pos + 8 + length + 4  # header + payload + CRC
        if next_pos > len(blob):
            raise AssetError(
                f"chunk {chunk_type!r} at {pos} overruns end of file"
            )
        if chunk_type == b"IEND":
            saw_iend = True
            break
        pos = next_pos
    if not saw_iend:
        raise AssetError("no IEND chunk found — PNG looks truncated")


def validate_asset(path: Path) -> tuple[int, int, int]:
    """Validate the bundled image; return (size_bytes, width, height).

    Checks run cheapest-first: existence, then byte size, then the IHDR
    header fields, then the full chunk walk. That ordering means the
    common failures (missing file, oversized export) report in O(1)
    instead of after scanning the whole file.
    """
    if not path.is_file():
        raise AssetError(f"bundled image not found: {path}")
    blob = path.read_bytes()
    size = len(blob)
    if size == 0:
        raise AssetError("bundled image is empty")
    if size > MAX_BYTES:
        raise AssetError(f"image is {size} bytes, limit is {MAX_BYTES}")
    width, height = parse_ihdr_dimensions(blob)
    if width > MAX_WIDTH or height > MAX_HEIGHT:
        raise AssetError(
            f"image is {width}x{height}, limit is {MAX_WIDTH}x{MAX_HEIGHT}"
        )
    # Bit depth / colour type sit in the IHDR payload right after the
    # dimensions. We do not restrict them — the judge accepts any valid
    # PNG — but a zero bit depth would mean the header is corrupt, so
    # treat it as one more cheap tripwire before trusting the file.
    bit_depth = blob[24]
    if bit_depth == 0:
        raise AssetError("IHDR bit depth is 0 — header looks corrupt")
    sanity_check_chunks(blob)
    return size, width, height


def main() -> int:
    here = Path(__file__).resolve().parent
    source = here / "image.png"

    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    destination = out_dir / "entry.png"

    try:
        size, width, height = validate_asset(source)
    except AssetError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)
    # Byte-for-byte copy: the determinism guarantee lives here. Never
    # re-encode, resize or rewrite the pixels at run time.
    shutil.copyfile(source, destination)

    # Post-copy guard: if the bytes on disk differ, something is very
    # wrong with the filesystem — fail rather than submit silently.
    if destination.read_bytes() != source.read_bytes():
        print("error: copied file differs from source image", file=sys.stderr)
        return 1

    print(f"wrote {destination} ({size} bytes, {width}x{height})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
