from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import numpy as np
import pytest

from app.ai import e5_runtime


class _Encoding:
    ids = [1, 2]
    attention_mask = [1, 1]
    type_ids = [0, 0]


class _Tokenizer:
    def enable_truncation(self, *, max_length: int) -> None:
        assert max_length == e5_runtime.MAX_SEQUENCE_TOKENS

    def enable_padding(self, *, pad_id: int, pad_token: str) -> None:
        assert (pad_id, pad_token) == (0, "[PAD]")

    def encode_batch(self, values: list[str]) -> list[_Encoding]:
        assert all(value.startswith("query: ") for value in values)
        return [_Encoding() for _ in values]

    def encode(self, value: str) -> _Encoding:
        assert isinstance(value, str)
        return _Encoding()


class _Session:
    def __init__(
        self,
        providers: list[str] | None = None,
        names: tuple[str, ...] = ("input_ids", "attention_mask", "token_type_ids"),
    ) -> None:
        self._providers = providers or ["CPUExecutionProvider"]
        self._names = names

    def get_providers(self) -> list[str]:
        return self._providers

    def get_inputs(self) -> list[SimpleNamespace]:
        return [SimpleNamespace(name=name) for name in self._names]

    def run(self, unused: object, feeds: dict[str, np.ndarray]) -> list[np.ndarray]:
        del unused
        return [
            np.ones((len(feeds["input_ids"]), 2, e5_runtime.VECTOR_DIMENSION), dtype=np.float32)
        ]


def _install_fake_modules(monkeypatch: pytest.MonkeyPatch, session: _Session) -> None:
    onnxruntime = ModuleType("onnxruntime")
    onnxruntime.SessionOptions = SimpleNamespace
    onnxruntime.InferenceSession = lambda *args, **kwargs: session
    tokenizers = ModuleType("tokenizers")
    tokenizers.Tokenizer = SimpleNamespace(from_file=lambda path: _Tokenizer())
    monkeypatch.setitem(sys.modules, "onnxruntime", onnxruntime)
    monkeypatch.setitem(sys.modules, "tokenizers", tokenizers)


def test_verify_model_directory_requires_regular_checksum_pinned_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    model = tmp_path / "model"
    model.mkdir()
    monkeypatch.setattr(
        e5_runtime, "MODEL_FILES", {"config.json": hashlib.sha256(b"ok").hexdigest()}
    )
    with pytest.raises(e5_runtime.E5RuntimeError, match="unverified"):
        e5_runtime.verify_model_directory(model)
    (model / "config.json").write_bytes(b"wrong")
    with pytest.raises(e5_runtime.E5RuntimeError, match="unverified"):
        e5_runtime.verify_model_directory(model)
    (model / "config.json").write_bytes(b"ok")
    e5_runtime.verify_model_directory(model)
    linked = tmp_path / "linked-model"
    linked.symlink_to(model, target_is_directory=True)
    with pytest.raises(e5_runtime.E5RuntimeError, match="unavailable"):
        e5_runtime.verify_model_directory(linked)


def test_encoder_cpu_session_prefixes_queries_counts_and_normalizes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_fake_modules(monkeypatch, _Session())
    monkeypatch.setattr(e5_runtime, "verify_model_directory", lambda path: None)
    encoder = e5_runtime.E5QueryEncoder(tmp_path, intra_op_threads=3, inter_op_threads=2)

    vector = encoder("привет")
    assert vector.shape == (e5_runtime.VECTOR_DIMENSION,)
    assert np.isclose(np.linalg.norm(vector), 1.0)
    assert encoder.encode_queries(["one", "two"]).shape == (2, e5_runtime.VECTOR_DIMENSION)
    assert encoder.count_tokens("evidence") == 2
    for invalid in ("", "   ", None):
        with pytest.raises(e5_runtime.E5RuntimeError, match="invalid_query"):
            encoder(invalid)  # type: ignore[arg-type]
    with pytest.raises(e5_runtime.E5RuntimeError, match="invalid_query"):
        encoder.encode_queries([])
    with pytest.raises(e5_runtime.E5RuntimeError, match="invalid_evidence"):
        encoder.count_tokens(None)  # type: ignore[arg-type]


def test_encoder_supports_a_session_without_token_type_ids_and_handles_missing_runtime(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_fake_modules(monkeypatch, _Session(names=("input_ids", "attention_mask")))
    monkeypatch.setattr(e5_runtime, "verify_model_directory", lambda path: None)
    assert e5_runtime.E5QueryEncoder(tmp_path)("query").shape == (e5_runtime.VECTOR_DIMENSION,)
    monkeypatch.setitem(sys.modules, "onnxruntime", None)
    monkeypatch.setitem(sys.modules, "tokenizers", None)
    with pytest.raises(e5_runtime.E5RuntimeError, match="unavailable"):
        e5_runtime.E5QueryEncoder(tmp_path)


@pytest.mark.parametrize(
    ("session", "message"),
    [
        (_Session(providers=["CUDAExecutionProvider"]), "unavailable"),
        (_Session(names=("input_ids",)), "unavailable"),
    ],
)
def test_encoder_rejects_non_cpu_or_incomplete_session(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, session: _Session, message: str
) -> None:
    _install_fake_modules(monkeypatch, session)
    monkeypatch.setattr(e5_runtime, "verify_model_directory", lambda path: None)
    with pytest.raises(e5_runtime.E5RuntimeError, match=message):
        e5_runtime.E5QueryEncoder(tmp_path)


def test_encoder_rejects_invalid_thread_counts_and_invalid_runtime_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with pytest.raises(e5_runtime.E5RuntimeError, match="invalid"):
        e5_runtime.E5QueryEncoder(tmp_path, intra_op_threads=0)
    _install_fake_modules(monkeypatch, _Session())
    monkeypatch.setattr(e5_runtime, "verify_model_directory", lambda path: None)
    encoder = e5_runtime.E5QueryEncoder(tmp_path)
    encoder._session.run = lambda unused, feeds: [np.full((1, 2, 1), np.nan)]  # type: ignore[method-assign]
    with pytest.raises(e5_runtime.E5RuntimeError, match="invalid"):
        encoder("query")
