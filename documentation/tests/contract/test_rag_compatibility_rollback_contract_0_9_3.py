from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[3]
pytestmark=pytest.mark.docs_contract
def test_m11_02_is_fail_closed_and_preserves_lexical_search():
 c=json.loads((ROOT/'documentation/config/rag-compatibility-rollback-contract-0.9.3.json').read_text())
 g=(ROOT/'documentation/tools/generate_chat_rag_exact_generations_0_9_3.py').read_text()
 assert c['backlog_item']=='BPM093-M11-02'
 assert 'mixed values are rejected' in c['rules'][0]
 assert 'os.replace' in g and 'active_pointer' in g
 assert 'lexical search remains available' in c['rules'][-1]
