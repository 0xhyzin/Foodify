"""Swagger UI setup and the request snippet presentation plugin."""

import json
from html import escape
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse

BEARER_SCHEME_NAME = "BearerAuth"
BEARER_DESCRIPTION = "JWT access token."
API_DESCRIPTION = "واجهة Foodify لحساب العميل والعناوين والجلسات."

# The display plugin uses the component API of this pinned Swagger UI version.
_SWAGGER_UI_VERSION = "5.34.0"
_SWAGGER_CDN = f"https://cdn.jsdelivr.net/npm/swagger-ui-dist@{_SWAGGER_UI_VERSION}"
_PLUGIN_FILE = Path(__file__).with_name("swagger_ui.js")


def configure_swagger_docs(app: FastAPI) -> None:
    """Serve the Swagger UI and its display-only plugin when docs are enabled."""
    if app.openapi_url is None:
        return

    @app.get("/docs", include_in_schema=False, response_class=HTMLResponse)
    def swagger_docs(request: Request) -> HTMLResponse:
        root_path = request.scope.get("root_path", "").rstrip("/")
        openapi_url = json.dumps(f"{root_path}{app.openapi_url}").replace("<", "\\u003c")
        plugin_url = escape(f"{root_path}/docs/swagger-ui.js", quote=True)
        title = escape(f"{app.title} - Swagger UI")
        return HTMLResponse(
            f"""<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link rel="stylesheet" href="{_SWAGGER_CDN}/swagger-ui.css">
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="{_SWAGGER_CDN}/swagger-ui-bundle.js"></script>
  <script src="{plugin_url}"></script>
  <script>
    window.ui = SwaggerUIBundle({{
      url: {openapi_url},
      dom_id: "#swagger-ui",
      layout: "BaseLayout",
      deepLinking: true,
      requestSnippetsEnabled: false,
      validatorUrl: null,
      presets: [SwaggerUIBundle.presets.apis],
      plugins: [window.FoodifySwaggerCurlPlugin]
    }});
  </script>
</body>
</html>"""
        )

    @app.get("/docs/swagger-ui.js", include_in_schema=False, response_class=FileResponse)
    def swagger_ui_asset() -> FileResponse:
        return FileResponse(_PLUGIN_FILE, media_type="application/javascript")
