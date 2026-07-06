from __future__ import annotations

import html
import json
import urllib.parse
from pathlib import Path
from typing import Final

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, Response

from app.core.config import get_settings
from app.core.locales import ACTIVE_CATALOG_LOCALES, resolve_active_catalog_locale_code
from app.documentation.manifest import DocumentationCatalog, load_documentation_catalog

router = APIRouter(include_in_schema=False)

DOCUMENTATION_HTML_CSP: Final[str] = (
    "default-src 'none'; "
    "script-src 'self'; "
    "script-src-attr 'none'; "
    "style-src 'self'; "
    "style-src-attr 'none'; "
    "img-src 'self'; "
    "font-src 'self'; "
    "connect-src 'self'; "
    "worker-src 'none'; "
    "child-src 'none'; "
    "frame-src 'none'; "
    "object-src 'none'; "
    "media-src 'none'; "
    "manifest-src 'none'; "
    "base-uri 'none'; "
    "form-action 'none'; "
    "frame-ancestors 'none'"
)
DOCUMENTATION_ASSET_CSP: Final[str] = (
    "default-src 'none'; "
    "base-uri 'none'; "
    "form-action 'none'; "
    "frame-ancestors 'none'"
)
DOCUMENTATION_CACHE_CONTROL: Final[str] = "no-cache, max-age=0, must-revalidate"
DOCUMENTATION_PERMISSIONS_POLICY: Final[str] = "geolocation=(), microphone=(), camera=()"
DOCUMENTATION_MIME_TYPES: Final[dict[str, str]] = {
    ".css": "text/css; charset=utf-8",
    ".gif": "image/gif",
    ".html": "text/html; charset=utf-8",
    ".ico": "image/x-icon",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".js": "text/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".png": "image/png",
    ".svg": "image/svg+xml",
    ".txt": "text/plain; charset=utf-8",
    ".woff2": "font/woff2",
}
DOCUMENTATION_LOCALE_QUERY_KEYS: Final[tuple[str, ...]] = ("locale", "lang")
DOCUMENTATION_LOCALE_COOKIE_KEYS: Final[tuple[str, ...]] = (
    "bpm_locale",
    "BPM_LOCALE",
    "locale",
    "lang",
)
DOCUMENTATION_STATUS_COPY: Final[dict[str, dict[str, tuple[str, str]]]] = {
    "en": {
        "missing": (
            "Documentation is not installed",
            "The product documentation artifact is not available in this environment yet. You can continue using Browser Policy Manager; install or build the documentation artifact, then reopen this page.",
        ),
        "stale": (
            "Documentation build does not match this BPM version",
            "The installed documentation was built for another BPM version. Rebuild or replace the documentation artifact for the current product version before publishing it.",
        ),
        "incompatible": (
            "Documentation build cannot be used",
            "The documentation manifest or target map is incomplete or incompatible. Rebuild the documentation artifact and verify manifest validation before release.",
        ),
        "incomplete": (
            "Documentation build is incomplete",
            "The documentation artifact exists, but required locale pages are missing. Rebuild the documentation artifact or reinstall the complete package.",
        ),
        "not_found": (
            "Documentation page was not found",
            "The requested documentation page or asset is not present in the installed artifact. Return to the documentation home page or rebuild the artifact if the link should exist.",
        ),
    },
    "ru": {
        "missing": (
            "Документация не установлена",
            "Артефакт продуктовой документации пока недоступен в этом окружении. Можно продолжать пользоваться Browser Policy Manager; установите или соберите артефакт документации и откройте эту страницу снова.",
        ),
        "stale": (
            "Сборка документации не соответствует версии BPM",
            "Установленная документация собрана для другой версии BPM. Перед публикацией пересоберите или замените артефакт документации для текущей версии продукта.",
        ),
        "incompatible": (
            "Сборку документации нельзя использовать",
            "Manifest документации или target-map неполные либо несовместимые. Пересоберите артефакт документации и проверьте валидацию manifest перед релизом.",
        ),
        "incomplete": (
            "Сборка документации неполная",
            "Артефакт документации существует, но обязательные страницы локалей отсутствуют. Пересоберите документацию или установите полный пакет.",
        ),
        "not_found": (
            "Страница документации не найдена",
            "Запрошенная страница или asset отсутствует в установленном артефакте. Вернитесь на главную страницу документации или пересоберите артефакт, если ссылка должна существовать.",
        ),
    },
    "de": {
        "missing": (
            "Dokumentation ist nicht installiert",
            "Das Produktdokumentationsartefakt ist in dieser Umgebung noch nicht verfügbar. Browser Policy Manager bleibt nutzbar; installieren oder bauen Sie das Dokumentationsartefakt und öffnen Sie diese Seite erneut.",
        ),
        "stale": (
            "Dokumentationsbuild passt nicht zu dieser BPM-Version",
            "Die installierte Dokumentation wurde für eine andere BPM-Version gebaut. Bauen oder ersetzen Sie das Artefakt für die aktuelle Produktversion vor der Veröffentlichung.",
        ),
        "incompatible": (
            "Dokumentationsbuild kann nicht verwendet werden",
            "Das Dokumentationsmanifest oder die Target-Map ist unvollständig oder inkompatibel. Bauen Sie das Artefakt neu und prüfen Sie die Manifestvalidierung vor dem Release.",
        ),
        "incomplete": (
            "Dokumentationsbuild ist unvollständig",
            "Das Dokumentationsartefakt existiert, aber erforderliche Lokalseiten fehlen. Bauen Sie die Dokumentation neu oder installieren Sie das vollständige Paket.",
        ),
        "not_found": (
            "Dokumentationsseite wurde nicht gefunden",
            "Die angeforderte Dokumentationsseite oder Ressource ist im installierten Artefakt nicht vorhanden. Kehren Sie zur Startseite zurück oder bauen Sie das Artefakt neu, wenn der Link existieren sollte.",
        ),
    },
    "zh-CN": {
        "missing": (
            "文档尚未安装",
            "此环境中还没有可用的产品文档构件。你仍可继续使用 Browser Policy Manager；请安装或构建文档构件，然后重新打开此页面。",
        ),
        "stale": (
            "文档构建与当前 BPM 版本不匹配",
            "已安装的文档是为其他 BPM 版本构建的。发布前请为当前产品版本重新构建或替换文档构件。",
        ),
        "incompatible": (
            "文档构建不可用",
            "文档 manifest 或 target-map 不完整或不兼容。请重新构建文档构件，并在发布前验证 manifest。",
        ),
        "incomplete": (
            "文档构建不完整",
            "文档构件存在，但缺少必需的本地化页面。请重新构建文档或安装完整包。",
        ),
        "not_found": (
            "未找到文档页面",
            "请求的文档页面或资源不在已安装的构件中。请返回文档首页；如果该链接应存在，请重新构建构件。",
        ),
    },
    "fr": {
        "missing": (
            "La documentation n’est pas installée",
            "L’artefact de documentation produit n’est pas encore disponible dans cet environnement. Vous pouvez continuer à utiliser Browser Policy Manager ; installez ou reconstruisez l’artefact, puis rouvrez cette page.",
        ),
        "stale": (
            "La documentation ne correspond pas à cette version de BPM",
            "La documentation installée a été construite pour une autre version de BPM. Reconstruisez ou remplacez l’artefact pour la version courante avant publication.",
        ),
        "incompatible": (
            "La documentation ne peut pas être utilisée",
            "Le manifest de documentation ou la target-map est incomplet ou incompatible. Reconstruisez l’artefact et vérifiez la validation du manifest avant la release.",
        ),
        "incomplete": (
            "La documentation est incomplète",
            "L’artefact de documentation existe, mais des pages de locale obligatoires manquent. Reconstruisez la documentation ou installez le paquet complet.",
        ),
        "not_found": (
            "Page de documentation introuvable",
            "La page ou la ressource demandée n’est pas présente dans l’artefact installé. Revenez à l’accueil de la documentation ou reconstruisez l’artefact si le lien devrait exister.",
        ),
    },
    "es-ES": {
        "missing": (
            "La documentación no está instalada",
            "El artefacto de documentación del producto aún no está disponible en este entorno. Puedes seguir usando Browser Policy Manager; instala o compila el artefacto de documentación y vuelve a abrir esta página.",
        ),
        "stale": (
            "La documentación no coincide con esta versión de BPM",
            "La documentación instalada se compiló para otra versión de BPM. Recompila o sustituye el artefacto para la versión actual del producto antes de publicarlo.",
        ),
        "incompatible": (
            "La documentación no se puede usar",
            "El manifest de documentación o el target-map está incompleto o es incompatible. Recompila el artefacto y verifica la validación del manifest antes del lanzamiento.",
        ),
        "incomplete": (
            "La documentación está incompleta",
            "El artefacto de documentación existe, pero faltan páginas obligatorias de las locales. Recompila la documentación o instala el paquete completo.",
        ),
        "not_found": (
            "No se encontró la página de documentación",
            "La página o el recurso solicitado no está en el artefacto instalado. Vuelve a la página inicial de la documentación o recompila el artefacto si el enlace debería existir.",
        ),
    },
}


def _settings_site_root() -> Path:
    settings = get_settings()
    site_root = Path(settings.DOCUMENTATION_SITE_DIR)
    if not site_root.is_absolute():
        site_root = settings.ROOT_DIR / site_root
    return site_root


def _headers(*, html: bool, status_code: int) -> dict[str, str]:
    headers = {
        "Content-Security-Policy": DOCUMENTATION_HTML_CSP if html else DOCUMENTATION_ASSET_CSP,
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "0",
        "Permissions-Policy": DOCUMENTATION_PERMISSIONS_POLICY,
        "Cross-Origin-Resource-Policy": "same-origin",
        "Cache-Control": DOCUMENTATION_CACHE_CONTROL,
    }
    if html or status_code >= 400:
        headers["Cross-Origin-Opener-Policy"] = "same-origin"
    return headers


def _plain_response(status_code: int, message: str) -> Response:
    return Response(
        content=f"{message}\n",
        status_code=status_code,
        media_type="text/plain; charset=utf-8",
        headers=_headers(html=False, status_code=status_code),
    )


def _status_locale(request: Request | None, requested_locale: str | None = None) -> str:
    supported = tuple(ACTIVE_CATALOG_LOCALES)
    if requested_locale:
        return resolve_active_catalog_locale_code(requested_locale, supported)
    if request is not None:
        for key in DOCUMENTATION_LOCALE_QUERY_KEYS:
            query_locale = request.query_params.get(key)
            if query_locale:
                return resolve_active_catalog_locale_code(query_locale, supported)
        for key in DOCUMENTATION_LOCALE_COOKIE_KEYS:
            cookie_locale = request.cookies.get(key)
            if cookie_locale:
                return resolve_active_catalog_locale_code(cookie_locale, supported)
        header = request.headers.get("accept-language", "")
        if header:
            return resolve_active_catalog_locale_code(header.split(",", maxsplit=1)[0], supported)
    return get_settings().DEFAULT_LOCALE


def _status_page_response(
    status_code: int,
    reason: str,
    *,
    request: Request | None = None,
    locale: str | None = None,
) -> Response:
    active_locale = _status_locale(request, locale)
    title, body = DOCUMENTATION_STATUS_COPY.get(active_locale, DOCUMENTATION_STATUS_COPY["en"]).get(
        reason,
        DOCUMENTATION_STATUS_COPY["en"]["incompatible"],
    )
    home_label = {
        "en": "Open BPM Profile Library",
        "ru": "Открыть библиотеку профилей BPM",
        "de": "BPM-Profilbibliothek öffnen",
        "zh-CN": "打开 BPM 配置档案库",
        "fr": "Ouvrir la bibliothèque de profils BPM",
        "es-ES": "Abrir la biblioteca de perfiles de BPM",
    }.get(active_locale, "Open BPM Profile Library")
    content = (
        "<!doctype html>"
        f"<html lang=\"{html.escape(active_locale)}\">"
        "<head>"
        "<meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        f"<title>{html.escape(title)}</title>"
        "</head>"
        "<body>"
        "<a href=\"#bpm-docs-status-main\">Skip to documentation status</a>"
        "<header>"
        "<nav aria-label=\"Documentation status\">"
        f"<a href=\"/profiles\">{html.escape(home_label)}</a>"
        "</nav>"
        "</header>"
        "<main id=\"bpm-docs-status-main\" tabindex=\"-1\" aria-labelledby=\"bpm-docs-status-title\">"
        f"<p>Browser Policy Manager · /help/ · HTTP {status_code}</p>"
        f"<h1 id=\"bpm-docs-status-title\">{html.escape(title)}</h1>"
        "<section role=\"status\" aria-live=\"polite\">"
        f"<p>{html.escape(body)}</p>"
        "</section>"
        "</main>"
        "</body>"
        "</html>"
    )
    return Response(
        content=content,
        status_code=status_code,
        media_type="text/html; charset=utf-8",
        headers=_headers(html=True, status_code=status_code),
    )


def _redirect_response(target: str) -> Response:
    response = RedirectResponse(
        url=target,
        status_code=307,
        headers=_headers(html=False, status_code=307),
    )
    return response


def _catalog(site_root: Path) -> DocumentationCatalog | None:
    return load_documentation_catalog(site_root)


def _available_locales(catalog: DocumentationCatalog | None) -> set[str] | None:
    return set(catalog.locales) if catalog is not None else None


def _default_locale(catalog: DocumentationCatalog | None, locales: set[str]) -> str:
    configured_default = get_settings().DEFAULT_LOCALE
    if configured_default in locales:
        return configured_default
    if catalog is not None:
        manifest_default = catalog.default_locale
        if manifest_default in locales:
            return manifest_default
    return sorted(locales)[0] if locales else get_settings().DEFAULT_LOCALE


def _canonical_locale(locale: str, locales: set[str], default_locale: str) -> str:
    if locale in locales:
        return locale
    resolved = resolve_active_catalog_locale_code(locale, tuple(locales))
    return resolved if resolved in locales else default_locale


def _active_locale_from_request(
    request: Request,
    *,
    locales: set[str],
    default_locale: str,
) -> str:
    for key in DOCUMENTATION_LOCALE_QUERY_KEYS:
        requested = request.query_params.get(key)
        if requested:
            return _canonical_locale(requested, locales, default_locale)

    for key in DOCUMENTATION_LOCALE_COOKIE_KEYS:
        requested = request.cookies.get(key)
        if requested:
            return _canonical_locale(requested, locales, default_locale)

    weighted_locales: list[tuple[float, str]] = []
    for raw_part in request.headers.get("accept-language", "").split(","):
        part = raw_part.strip()
        if not part:
            continue
        language, _, params = part.partition(";")
        weight = 1.0
        for raw_param in params.split(";"):
            param = raw_param.strip()
            if not param.startswith("q="):
                continue
            try:
                weight = float(param[2:])
            except ValueError:
                weight = 0.0
        if weight <= 0:
            continue
        weighted_locales.append((weight, _canonical_locale(language, locales, default_locale)))
    if weighted_locales:
        weighted_locales.sort(key=lambda item: item[0], reverse=True)
        return weighted_locales[0][1]

    return default_locale


def _site_is_available(site_root: Path) -> bool:
    catalog = _catalog(site_root)
    locales = _available_locales(catalog)
    return bool(locales and all((site_root / locale / "index.html").is_file() for locale in locales))


def _artifact_problem(site_root: Path) -> str | None:
    manifest_path = site_root / "manifest.json"
    if not manifest_path.is_file():
        return "missing"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "incompatible"
    artifact = manifest.get("artifact")
    bpm_version = artifact.get("bpm_version") if isinstance(artifact, dict) else None
    if isinstance(bpm_version, str) and bpm_version and bpm_version != get_settings().APP_VERSION:
        return "stale"
    locales = manifest.get("locales")
    if isinstance(locales, list) and locales and all(isinstance(locale, str) for locale in locales):
        if not all((site_root / locale / "index.html").is_file() for locale in locales):
            return "incomplete"

    catalog = _catalog(site_root)
    if catalog is None:
        return "incompatible"
    if not catalog.locales:
        return "incomplete"
    if not all((site_root / locale / "index.html").is_file() for locale in catalog.locales):
        return "incomplete"
    return None


def _safe_relative_path(raw_path: str) -> Path | None:
    decoded = urllib.parse.unquote(raw_path).replace("\\", "/")
    if "\x00" in decoded or decoded.startswith("/"):
        return None
    parts = [part for part in decoded.split("/") if part not in {"", "."}]
    if any(part == ".." for part in parts):
        return None
    if not parts or raw_path.endswith("/"):
        parts.append("index.html")
    return Path(*parts)


def _resolve_packaged_file(site_root: Path, relative_path: Path) -> Path | None:
    root = site_root.resolve()
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    if not candidate.is_file():
        return None
    return candidate


def _serve_packaged_path(relative_path: str) -> Response:
    site_root = _settings_site_root()
    problem = _artifact_problem(site_root)
    if problem is not None:
        return _plain_response(503, "Documentation artifact is not installed")

    safe_path = _safe_relative_path(relative_path)
    if safe_path is None:
        return _plain_response(404, "Documentation asset not found")

    media_type = DOCUMENTATION_MIME_TYPES.get(safe_path.suffix.lower())
    if media_type is None:
        return _plain_response(404, "Documentation asset not found")

    packaged_file = _resolve_packaged_file(site_root, safe_path)
    if packaged_file is None:
        return _plain_response(404, "Documentation asset not found")

    return Response(
        content=packaged_file.read_bytes(),
        media_type=media_type,
        headers=_headers(html=safe_path.suffix.lower() == ".html", status_code=200),
    )


def _topic_public_paths(catalog: DocumentationCatalog) -> dict[str, dict[str, object]]:
    guides = catalog.manifest.get("guides")
    topics = catalog.manifest.get("topics")
    if not isinstance(guides, dict) or not isinstance(topics, dict):
        return {}

    public_paths: dict[str, dict[str, object]] = {}
    for topic in topics.values():
        if not isinstance(topic, dict):
            continue
        guide_id = topic.get("guide_id")
        guide = guides.get(guide_id) if isinstance(guide_id, str) else None
        if not isinstance(guide, dict):
            continue
        guide_root = guide.get("url_root")
        url_path = topic.get("url_path")
        if isinstance(guide_root, str) and isinstance(url_path, str):
            public_paths[f"{guide_root}/{url_path}"] = topic
    return public_paths


def _canonical_topic_redirect(
    *,
    locale: str,
    catalog: DocumentationCatalog,
    public_path: str,
) -> Response | None:
    public_path = public_path.strip("/")
    if not public_path:
        return None

    aliases = catalog.manifest.get("aliases")
    if isinstance(aliases, dict):
        alias = aliases.get(public_path)
        if isinstance(alias, dict):
            canonical_path = alias.get("canonical_url_path")
            if isinstance(canonical_path, str):
                anchor = alias.get("anchor_id")
                fragment = f"#{anchor}" if isinstance(anchor, str) and anchor else ""
                return _redirect_response(f"/help/{locale}/{canonical_path}/{fragment}")

    topic = _topic_public_paths(catalog).get(public_path)
    if not isinstance(topic, dict):
        return None
    outputs = topic.get("output")
    if not isinstance(outputs, dict):
        return None
    output = outputs.get(locale)
    if not isinstance(output, str):
        return None
    return _redirect_response(f"/help/{output}")


@router.get("/help")
async def documentation_root_without_slash() -> Response:
    return _redirect_response("/help/")


@router.get("/help/")
async def documentation_root(request: Request) -> Response:
    site_root = _settings_site_root()
    catalog = _catalog(site_root)
    locales = _available_locales(catalog)
    problem = _artifact_problem(site_root)
    if problem is not None or catalog is None or locales is None:
        return _status_page_response(503, problem or "incompatible", request=request)
    default_locale = _default_locale(catalog, locales)
    locale = _active_locale_from_request(request, locales=locales, default_locale=default_locale)
    return _redirect_response(f"/help/{locale}/")


@router.get("/help/manifest.json")
async def documentation_manifest() -> Response:
    return _serve_packaged_path("manifest.json")


@router.get("/help/ui-target-map.json")
async def documentation_ui_target_map() -> Response:
    return _serve_packaged_path("ui-target-map.json")


@router.get("/help/search/{asset_path:path}")
async def documentation_search_asset(asset_path: str) -> Response:
    return _serve_packaged_path(f"search/{asset_path}")


@router.get("/help/{locale}")
async def documentation_locale_without_slash(locale: str) -> Response:
    return _redirect_response(f"/help/{locale}/")


@router.get("/help/{locale}/{asset_path:path}")
async def documentation_locale_asset(request: Request, locale: str, asset_path: str = "") -> Response:
    site_root = _settings_site_root()
    catalog = _catalog(site_root)
    locales = _available_locales(catalog)
    problem = _artifact_problem(site_root)
    if problem is not None or catalog is None or locales is None:
        return _status_page_response(503, problem or "incompatible", request=request, locale=locale)
    if locale not in locales:
        fallback_locale = _default_locale(catalog, locales)
        suffix = f"{asset_path}" if asset_path else ""
        return _redirect_response(f"/help/{fallback_locale}/{suffix}")
    public_route = asset_path.rstrip("/")
    if not Path(public_route).suffix:
        if asset_path and not asset_path.endswith("/"):
            return _redirect_response(f"/help/{locale}/{public_route}/")
        redirect = _canonical_topic_redirect(
            locale=locale,
            catalog=catalog,
            public_path=public_route,
        )
        if redirect is not None:
            return redirect
    response = _serve_packaged_path(f"{locale}/{asset_path}")
    if response.status_code == 404 and (not asset_path or asset_path.endswith(".html")):
        return _status_page_response(404, "not_found", request=request, locale=locale)
    return response
