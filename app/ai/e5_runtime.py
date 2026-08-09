"""Verified CPU-only query encoder for the selected multilingual E5-base artifact."""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np

MODEL_ID = "multilingual-e5-base-onnx-o4"
MODEL_DIRECTORY_NAME = MODEL_ID
MODEL_REVISION = "f5bd48cd75e61ca79c4cdffff9185cab1f07f4f0"
MODEL_REPOSITORY = "intfloat/multilingual-e5-base"
MODEL_FILES = {
    "config.json": "9dab198f24c8c0879e481cf7822005d5ecbceedbacb390ffafa594e28d31bac4",
    "tokenizer.json": "62c24cdc13d4c9952d63718d6c9fa4c287974249e16b7ade6d5a85e7bbb75626",
    "tokenizer_config.json": "efb5c0d09722e5fe59a462cd2a9976ee216d55b037597d997cd3fe833216da15",
    "special_tokens_map.json": "06e405a36dfe4b9604f484f6a1e619af1a7f7d09e34a8555eb0b77b66318067f",
    "onnx/model_O4.onnx": "f60256a833caee5c75a3903e589116752ee016ca7bc16f9b96e4db09984c5703",
}
VECTOR_DIMENSION = 768
MAX_SEQUENCE_TOKENS = 512


class E5RuntimeError(RuntimeError):
    """The selected embedding artifact or its strictly local CPU runtime is unavailable."""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_model_directory(model_dir: Path) -> None:
    """Require every pinned file before loading an ONNX session."""

    root = Path(model_dir)
    if not root.is_dir() or root.is_symlink():
        raise E5RuntimeError("assistant_embedding_model_unavailable")
    for relative, expected in MODEL_FILES.items():
        candidate = root / relative
        if not candidate.is_file() or candidate.is_symlink() or sha256(candidate) != expected:
            raise E5RuntimeError("assistant_embedding_model_unverified")


class E5QueryEncoder:
    """One retained CPU session; queries always receive the E5 query prefix."""

    def __init__(
        self, model_dir: Path, *, intra_op_threads: int = 2, inter_op_threads: int = 1
    ) -> None:
        if intra_op_threads < 1 or inter_op_threads < 1:
            raise E5RuntimeError("assistant_embedding_runtime_invalid")
        verify_model_directory(model_dir)
        try:
            import onnxruntime
            from tokenizers import Tokenizer
        except ImportError as error:
            raise E5RuntimeError("assistant_embedding_runtime_unavailable") from error
        options = onnxruntime.SessionOptions()
        options.intra_op_num_threads = intra_op_threads
        options.inter_op_num_threads = inter_op_threads
        self._session = onnxruntime.InferenceSession(
            str(Path(model_dir) / "onnx/model_O4.onnx"),
            sess_options=options,
            providers=["CPUExecutionProvider"],
        )
        if self._session.get_providers() != ["CPUExecutionProvider"]:
            raise E5RuntimeError("assistant_embedding_runtime_unavailable")
        self._input_names = {item.name for item in self._session.get_inputs()}
        if not {"input_ids", "attention_mask"} <= self._input_names:
            raise E5RuntimeError("assistant_embedding_runtime_unavailable")
        self._tokenizer = Tokenizer.from_file(str(Path(model_dir) / "tokenizer.json"))
        self._tokenizer.enable_truncation(max_length=MAX_SEQUENCE_TOKENS)
        self._tokenizer.enable_padding(pad_id=0, pad_token="[PAD]")
        self._count_tokenizer = Tokenizer.from_file(str(Path(model_dir) / "tokenizer.json"))

    def __call__(self, question: str) -> np.ndarray:
        if not isinstance(question, str) or not question.strip():
            raise E5RuntimeError("assistant_invalid_query")
        return self.encode_queries([question])[0]

    def encode_queries(self, queries: list[str]) -> np.ndarray:
        if not queries or any(not isinstance(query, str) or not query.strip() for query in queries):
            raise E5RuntimeError("assistant_invalid_query")
        return self._encode([f"query: {query}" for query in queries])

    def count_tokens(self, value: str) -> int:
        if not isinstance(value, str):
            raise E5RuntimeError("assistant_invalid_evidence")
        return len(self._count_tokenizer.encode(value).ids)

    def _encode(self, values: list[str]) -> np.ndarray:
        encoded = self._tokenizer.encode_batch(values)
        feeds = {
            "input_ids": np.asarray([item.ids for item in encoded], dtype=np.int64),
            "attention_mask": np.asarray([item.attention_mask for item in encoded], dtype=np.int64),
        }
        if "token_type_ids" in self._input_names:
            feeds["token_type_ids"] = np.asarray(
                [item.type_ids for item in encoded], dtype=np.int64
            )
        hidden = self._session.run(None, feeds)[0]
        mask = feeds["attention_mask"][..., None]
        pooled = (hidden * mask).sum(axis=1) / np.maximum(mask.sum(axis=1), 1)
        normalized = pooled / np.maximum(np.linalg.norm(pooled, axis=1, keepdims=True), 1e-12)
        vectors = normalized.astype(np.float32)
        if vectors.shape != (len(values), VECTOR_DIMENSION) or not np.isfinite(vectors).all():
            raise E5RuntimeError("assistant_embedding_runtime_invalid")
        return vectors
