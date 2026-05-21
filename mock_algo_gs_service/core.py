"""3DGS Watermark — dual-channel attribute embedding with RS(12,4) error correction.

Embedds a 32-bit payload into a 3DGS PLY file via:
  - Channel 1 (primary): custom uint8 attributes wm_b0..wm_b11
  - Channel 2 (fallback): normal vectors nx, ny, nz

Extraction uses majority voting across K anchor gaussians before RS decoding.
"""

import struct
import numpy as np
from plyfile import PlyData, PlyElement
from reedsolo import RSCodec

__version__ = "1.0.0"

# RS(12,4) over GF(2⁸): 4 data bytes + 8 parity bytes
_RS = RSCodec(nsym=8)
PAYLOAD_BYTES = 4
CODEWORD_BYTES = 12
CUSTOM_ATTRS = [f"wm_b{i}" for i in range(CODEWORD_BYTES)]


class GS3DWatermark:
    """Embed and extract 32-bit payloads in 3DGS PLY files."""

    def __init__(self, redundancy: int = 8):
        if redundancy < 1:
            raise ValueError("redundancy must be >= 1")
        self.K = redundancy

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _encode_payload(payload: int) -> bytes:
        """RS(12,4) encode a 32-bit unsigned int → 12-byte codeword."""
        data = payload.to_bytes(PAYLOAD_BYTES, "big")
        return bytes(_RS.encode(data))

    @staticmethod
    def _decode_codeword(cw: bytes) -> int:
        """RS decode a 12-byte codeword → 32-bit unsigned int."""
        decoded, _, _ = _RS.decode(cw)
        return int.from_bytes(bytes(decoded), "big")

    @staticmethod
    def _select_anchors(vertex_data: np.ndarray, k: int) -> np.ndarray:
        """Select K stable anchors via position hashing (order-invariant)."""
        pts = np.stack([vertex_data["x"], vertex_data["y"], vertex_data["z"]], axis=1)
        q = np.round(pts * 1e6).astype(np.int64)
        keys = (q[:, 0] * 73856093) ^ (q[:, 1] * 19349663) ^ (q[:, 2] * 83492791)
        return np.argsort(keys)[:k]

    @staticmethod
    def _majority_vote(candidates: list[bytes]) -> bytes:
        """Byte-wise majority vote across K candidate codewords."""
        return bytes(
            np.bincount([c[i] for c in candidates], minlength=256).argmax()
            for i in range(CODEWORD_BYTES)
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def embed(self, ply_in: str, ply_out: str, payload: int) -> None:
        """Embed a 32-bit payload into a PLY file.

        Args:
            ply_in:  Source 3DGS PLY path.
            ply_out: Output PLY path (will be overwritten).
            payload: Unsigned 32-bit integer to embed.
        """
        if not 0 <= payload < 2**32:
            raise ValueError("payload must be a 32-bit unsigned integer")

        ply = PlyData.read(ply_in)
        vertex = ply["vertex"].data
        anchors = self._select_anchors(vertex, self.K)
        cw = self._encode_payload(payload)  # 12 bytes

        # Build extended dtype with custom uint8 attributes
        orig_dtype = vertex.dtype
        new_dtype = np.dtype(
            orig_dtype.descr + [(attr, "u1") for attr in CUSTOM_ATTRS]
        )
        extended = np.zeros(vertex.shape, dtype=new_dtype)
        for name in orig_dtype.names:
            extended[name] = vertex[name]

        f0, f1, f2 = struct.unpack("<3f", cw)

        for idx in anchors:
            # Channel 1: custom uint8 attributes
            for i, b in enumerate(cw):
                extended[CUSTOM_ATTRS[i]][idx] = b
            # Channel 2: normal vectors (float32 encoding of codeword)
            extended["nx"][idx] = f0
            extended["ny"][idx] = f1
            extended["nz"][idx] = f2

        PlyData([PlyElement.describe(extended, "vertex")]).write(ply_out)
        self._last_anchors = anchors

    def extract(self, ply_path: str) -> int:
        """Extract the 32-bit payload from a watermarked PLY file.

        Args:
            ply_path: Path to a watermarked PLY file.

        Returns:
            Extracted 32-bit unsigned integer payload.
        """
        ply = PlyData.read(ply_path)
        vertex = ply["vertex"].data
        anchors = self._select_anchors(vertex, self.K)

        has_custom = all(attr in vertex.dtype.names for attr in CUSTOM_ATTRS)

        candidates = []
        for idx in anchors:
            if has_custom:
                cw = bytes(vertex[CUSTOM_ATTRS[i]][idx] for i in range(CODEWORD_BYTES))
            else:
                cw = struct.pack(
                    "<3f", vertex["nx"][idx], vertex["ny"][idx], vertex["nz"][idx]
                )
            candidates.append(cw)

        merged = self._majority_vote(candidates)
        return self._decode_codeword(merged)
