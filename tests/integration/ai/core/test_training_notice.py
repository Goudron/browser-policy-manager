from __future__ import annotations

import pytest

from app.documentation.assistant_contracts import SUPPORTED_LOCALES
from app.documentation.training_notice import training_notice


def test_training_notice_is_owned_by_all_supported_locales_and_rejects_unknown_locale() -> None:
    assert all(training_notice(locale) for locale in SUPPORTED_LOCALES)
    with pytest.raises(ValueError, match="assistant_unsupported_locale"):
        training_notice("unsupported")
