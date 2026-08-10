from __future__ import annotations

import hashlib
import json
import re
import struct
import xml.etree.ElementTree as ET
import zlib
from collections import Counter, defaultdict
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENTATION_ROOT = REPOSITORY_ROOT / "documentation"
MATRIX = DOCUMENTATION_ROOT / "config/user-guide-screenshot-matrix-0.9.1.json"
USER_GUIDE_MAP = DOCUMENTATION_ROOT / "config/user-guide-map-0.9.0.json"
PROFILE_FIXTURES = DOCUMENTATION_ROOT / "fixtures/profile-states/profile-states-0.9.0.json"
SCREENSHOT_CAPTURE = DOCUMENTATION_ROOT / "tools/capture_user_guide_screenshots.py"
LOCALES = ("en", "ru", "de", "zh-CN", "fr", "es-ES")
REQUIRED_ROW_FIELDS = {
    "id",
    "scenario_id",
    "guide_id",
    "topic_id",
    "locale",
    "viewport",
    "theme",
    "fixture_state",
    "route",
    "filename",
    "asset_path",
    "caption_key",
    "alt_text_key",
}

pytestmark = pytest.mark.docs_contract


def _json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as image:
        header = image.read(24)
    assert header.startswith(b"\x89PNG\r\n\x1a\n"), path
    return struct.unpack(">II", header[16:24])


def _png_chunks(path: Path) -> list[str]:
    data = path.read_bytes()
    assert data.startswith(b"\x89PNG\r\n\x1a\n"), path
    chunks: list[str] = []
    position = 8
    while position < len(data):
        assert position + 12 <= len(data), path
        chunk_length = struct.unpack(">I", data[position : position + 4])[0]
        chunk_type_bytes = data[position + 4 : position + 8]
        chunk_data_start = position + 8
        chunk_data_end = chunk_data_start + chunk_length
        chunk_crc_end = chunk_data_end + 4
        assert chunk_crc_end <= len(data), path
        expected_crc = struct.unpack(">I", data[chunk_data_end:chunk_crc_end])[0]
        actual_crc = (
            zlib.crc32(chunk_type_bytes + data[chunk_data_start:chunk_data_end]) & 0xFFFFFFFF
        )
        assert actual_crc == expected_crc, path
        chunk_type = chunk_type_bytes.decode("ascii")
        chunks.append(chunk_type)
        position = chunk_crc_end
        if chunk_type == "IEND":
            assert position == len(data), path
            break
    assert chunks and chunks[0] == "IHDR" and chunks[-1] == "IEND", path
    return chunks


def _user_guide_topic_ids() -> set[str]:
    case_map = _json(USER_GUIDE_MAP)
    return {
        topic["topic_id"]
        for section in case_map["sections"]
        for topic in section["topics"]
        if isinstance(topic, dict)
    }


def _xml_text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return " ".join("".join(element.itertext()).split())


def test_minimal_user_guide_screenshot_matrix_covers_all_locales_and_scenarios() -> None:
    matrix = _json(MATRIX)
    scenarios = matrix["scenarios"]
    rows = matrix["matrix"]

    assert matrix["target_bpm_version"] == "0.9.1"
    assert matrix["backlog_item"] == "BPM091-M2-02"
    assert matrix["guide_id"] == "user-guide"
    assert matrix["locales"] == list(LOCALES)
    assert len(scenarios) == 6
    assert len(rows) == len(scenarios) * len(LOCALES)

    scenario_ids = {scenario["scenario_id"] for scenario in scenarios}
    by_locale = {locale: set() for locale in LOCALES}
    for row in rows:
        assert REQUIRED_ROW_FIELDS <= set(row)
        assert row["scenario_id"] in scenario_ids
        assert row["locale"] in LOCALES
        by_locale[row["locale"]].add(row["scenario_id"])
    assert all(ids == scenario_ids for ids in by_locale.values())


def test_user_guide_screenshot_matrix_is_user_guide_only_and_links_to_existing_topics() -> None:
    matrix = _json(MATRIX)
    topic_ids = _user_guide_topic_ids()

    assert matrix["scope"]["excluded_guides"] == [
        "firefox-policy-guide",
        "cis-settings-guide",
        "api-integration-guide",
        "administrator-guide",
    ]
    for row in matrix["matrix"]:
        assert row["guide_id"] == "user-guide"
        assert row["topic_id"] in topic_ids
        assert row["topic_id"].startswith("ug-")
        assert not row["topic_id"].startswith(("fx-", "cis-", "api-", "admin-"))


def test_user_guide_screenshot_matrix_names_capture_contract_for_every_row() -> None:
    matrix = _json(MATRIX)
    profile_fixtures = {profile["id"] for profile in _json(PROFILE_FIXTURES)["profiles"]}
    scenario_by_id = {scenario["scenario_id"]: scenario for scenario in matrix["scenarios"]}

    for row in matrix["matrix"]:
        scenario = scenario_by_id[row["scenario_id"]]
        assert row["fixture_state"] in profile_fixtures
        if secondary := row.get("secondary_fixture_state"):
            assert secondary in profile_fixtures
        assert row["route"] == scenario["route"]
        assert row["filename"] == scenario["filename"]
        assert row["caption_key"] == scenario["caption_key"]
        assert row["alt_text_key"] == scenario["alt_text_key"]
        assert row["asset_path"] == (
            f"documentation/assets/screenshots/{row['locale']}/{row['filename']}"
        )
        assert row["filename"].endswith(".png")
        assert row["caption_key"].startswith("screenshots.user_guide.")
        assert row["alt_text_key"].startswith("screenshots.user_guide.")


def test_user_guide_screenshot_capture_states_are_frozen_and_diagnostic() -> None:
    matrix = _json(MATRIX)
    contract = matrix["capture_state_contract"]
    profiles = {profile["id"]: profile for profile in _json(PROFILE_FIXTURES)["profiles"]}
    scenarios = {scenario["scenario_id"]: scenario for scenario in matrix["scenarios"]}
    required_failure_fields = set(contract["required_failure_context_fields"])

    assert contract["backlog_item"] == "BPM091-M5-01"
    assert contract["status"] == "frozen"
    assert contract["profile_fixture_source"] == (
        "documentation/fixtures/profile-states/profile-states-0.9.0.json"
    )
    assert (
        contract["runtime"]["seed_mode"] == "recreate from synthetic fixtures for every capture run"
    )
    assert contract["runtime"]["network"] == "localhost only"
    assert {
        "production databases",
        "local user browser profiles",
        "customer profiles",
        "secrets",
        "private hosts",
    } <= set(contract["runtime"]["forbidden_sources"])
    assert contract["viewports"] == {
        "desktop": {"width": 1440, "height": 1000, "device_scale_factor": 1},
        "narrow": {"width": 390, "height": 900, "device_scale_factor": 1},
    }
    assert {
        "locale",
        "topic_id",
        "route",
        "state_id",
        "matrix_row_id",
        "scenario_id",
        "viewport",
        "theme",
        "schema_channel",
        "fixture_state",
        "asset_path",
    } <= required_failure_fields

    state_by_scenario = contract["scenario_ui_states"]
    assert set(state_by_scenario) == set(scenarios)
    for row in matrix["matrix"]:
        state = state_by_scenario[row["scenario_id"]]
        profile = profiles[row["fixture_state"]]
        assert state["state_id"].startswith("shot-state-")
        assert state["primary_profile_id"] == row["fixture_state"]
        assert state["schema_channel"] == profile["schema_channel"]
        assert row["viewport"] in contract["viewports"]
        assert row["route"] == scenarios[row["scenario_id"]]["route"]
        assert row["theme"] == scenarios[row["scenario_id"]]["theme"]
        if "{profile_id}" not in row["route"]:
            assert "profile_id" not in state["route_parameters"]
        else:
            assert state["route_parameters"]["profile_id"] == row["fixture_state"]
        assert state["ui_state"]["surface"]
        assert state["wait_for_selectors"]
        if secondary := row.get("secondary_fixture_state"):
            secondary_profile = profiles[secondary]
            assert state["secondary_profile_id"] == secondary
            assert state["secondary_schema_channel"] == secondary_profile["schema_channel"]


def test_user_guide_screenshot_capture_command_and_assets_exist() -> None:
    matrix = _json(MATRIX)
    execution = matrix["capture_execution"]
    viewports = matrix["capture_state_contract"]["viewports"]

    assert execution["backlog_item"] == "BPM091-M5-02"
    assert execution["command"] == (
        "./.venv/bin/python documentation/tools/capture_user_guide_screenshots.py"
    )
    assert execution["sandbox"] == "requires immediate sandbox escalation"
    assert execution["writes_assets"] == "documentation/assets/screenshots/{locale}/"
    assert execution["writes_reports"] == "documentation/reports/screenshots/"

    for row in matrix["matrix"]:
        asset = REPOSITORY_ROOT / row["asset_path"]
        assert asset.is_file(), row["id"]
        assert asset.parent == DOCUMENTATION_ROOT / "assets/screenshots" / row["locale"]
        assert asset.name == row["filename"]
        expected_viewport = viewports[row["viewport"]]
        assert _png_size(asset) == (
            expected_viewport["width"],
            expected_viewport["height"],
        )
        assert asset.stat().st_size > 1024


def test_screenshot_capture_seeds_the_current_supported_schema_channels() -> None:
    capture_source = SCREENSHOT_CAPTURE.read_text(encoding="utf-8")

    assert '"schema_version": "release-153"' in capture_source
    assert '"schema_version": "esr-140.13"' in capture_source
    assert '"schema_version": "release-152"' not in capture_source
    assert '"schema_version": "esr-140.12"' not in capture_source


def test_user_guide_screenshot_assets_are_normalized_and_not_orphaned() -> None:
    matrix = _json(MATRIX)
    normalization = matrix["asset_normalization"]
    rows = matrix["matrix"]
    allowed_chunks = set(normalization["allowed_chunks"])
    filename_pattern = re.compile(normalization["filename_pattern"])
    max_bytes_by_viewport = normalization["max_bytes_by_viewport"]

    assert normalization["backlog_item"] == "BPM091-M5-03"
    assert normalization["status"] == "accepted"
    assert normalization["storage_root"] == "documentation/assets/screenshots/{locale}/"
    assert normalization["format"] == "png"
    assert normalization["metadata_policy"] == "no ancillary PNG metadata chunks"
    assert normalization["orphan_policy"].startswith("every PNG")
    assert normalization["cross_locale_policy"].startswith("same-scenario screenshots")

    expected_asset_references = Counter(REPOSITORY_ROOT / row["asset_path"] for row in rows)
    assert all(count == 1 for count in expected_asset_references.values())
    expected_assets = set(expected_asset_references)
    actual_assets = set((DOCUMENTATION_ROOT / "assets/screenshots").glob("*/*.png"))
    assert actual_assets == expected_assets

    digests_by_scenario: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for row in rows:
        asset = REPOSITORY_ROOT / row["asset_path"]
        assert filename_pattern.fullmatch(row["filename"])
        assert asset.suffix == ".png"
        assert set(_png_chunks(asset)) <= allowed_chunks
        assert asset.stat().st_size <= max_bytes_by_viewport[row["viewport"]]
        digest = hashlib.sha256(asset.read_bytes()).hexdigest()
        digests_by_scenario[row["scenario_id"]].append((row["locale"], digest))

    for scenario_id, locale_digests in digests_by_scenario.items():
        digests = {digest for _locale, digest in locale_digests}
        assert len(digests) == len(LOCALES), scenario_id


def test_user_guide_screenshots_are_integrated_into_localized_topics() -> None:
    matrix = _json(MATRIX)
    integration = matrix["topic_integration"]
    scenarios = {scenario["scenario_id"]: scenario for scenario in matrix["scenarios"]}
    english_copy: dict[str, tuple[str, str]] = {}

    assert integration["backlog_item"] == "BPM091-M5-04"
    assert integration["status"] == "accepted"
    assert integration["source_key_pattern"] == "screenshot.{scenario_id}"
    assert integration["source_figure_id_pattern"] == "screenshot-{scenario_id}"
    assert integration["published_asset_root"] == "{locale}/assets/screenshots/"
    assert integration["fallback_policy"].startswith("no localized topic")

    for row in matrix["matrix"]:
        scenario_id = row["scenario_id"]
        locale = row["locale"]
        filename = row["filename"]
        topic_id = row["topic_id"]
        expected_key = f"screenshot.{scenario_id}"
        expected_fig_id = f"screenshot-{scenario_id}"

        keys_root = ET.parse(DOCUMENTATION_ROOT / f"src/dita/{locale}/maps/keys.ditamap").getroot()
        keydefs = [
            keydef
            for keydef in keys_root.findall("keydef")
            if keydef.attrib.get("keys") == expected_key
        ]
        assert len(keydefs) == 1, row["id"]
        assert keydefs[0].attrib == {
            "keys": expected_key,
            "href": f"../../../../assets/screenshots/{locale}/{filename}",
            "format": "png",
        }

        topic_root = ET.parse(
            DOCUMENTATION_ROOT / f"src/dita/{locale}/user/{topic_id}.dita"
        ).getroot()
        figures = [
            figure
            for figure in topic_root.findall(".//fig")
            if figure.attrib.get("id") == expected_fig_id
        ]
        assert len(figures) == 1, row["id"]
        title = _xml_text(figures[0].find("title"))
        image = figures[0].find("image")
        alt = _xml_text(image.find("alt") if image is not None else None)
        assert title, row["id"]
        assert alt, row["id"]
        assert image is not None, row["id"]
        assert image.attrib["keyref"] == expected_key
        assert image.attrib["placement"] == "break"
        assert scenarios[scenario_id]["caption_key"] == row["caption_key"]
        assert scenarios[scenario_id]["alt_text_key"] == row["alt_text_key"]
        assert "English" not in title
        assert "English" not in alt

        if locale == "en":
            english_copy[scenario_id] = (title, alt)
        else:
            assert (title, alt) != english_copy.get(scenario_id), row["id"]
