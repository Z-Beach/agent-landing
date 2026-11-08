"""QR-GIF: encode files into visual streams, recover them from frames."""
from .protocol import Fec, sha256  # noqa: F401
from .codec import (  # noqa: F401
    Collector,
    StreamConfig,
    build_frames,
    decode_frames,
    encode_file,
    iter_frames,
)
