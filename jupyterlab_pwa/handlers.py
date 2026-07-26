"""PWA handlers and LabHandler wrapper for JupyterLab.

Architecture (Option B — handler wrapper):
  - Serves manifest.json, sw.js, and icons via Tornado handlers on the user pod.
  - Wraps jupyterlab_server.handlers.LabHandler.get() to inject PWA tags
    (<link rel="manifest">, <script>SW register</script>) into the rendered
    HTML string, before </head>. This survives JupyterLab updates because
    it wraps the live handler — the JS bundle hash, page_config, and template
    structure are all handled by JupyterLab itself.

Modeled on code-server's PWA approach:
  - Manifest served by app route (/pwa/manifest.json)
  - SW served by app route (/pwa/sw.js) with Service-Worker-Allowed header
  - PWA tags in HTML (code-server bakes them in templates; we inject them
    post-render via handler wrapping — same end result, more robust)
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from tornado.web import RequestHandler, authenticated

HERE = Path(__file__).parent


class PWAManifestHandler(RequestHandler):
    """Serve the web app manifest JSON."""

    def get(self):
        self.set_header("Content-Type", "application/manifest+json")
        base_url = self.settings.get("base_url", "/")
        # Build icon URLs relative to the user server's base_url
        manifest = {
            "name": "JupyterLab",
            "short_name": "JupyterLab",
            "description": "JupyterLab Progressive Web App",
            "start_url": base_url + "lab",
            "scope": base_url,
            "display": "standalone",
            "orientation": "any",
            "background_color": "#ffffff",
            "theme_color": "#f37726",
            "icons": [
                {
                    "src": base_url + "pwa/icon-192.png",
                    "sizes": "192x192",
                    "type": "image/png",
                    "purpose": "any maskable",
                },
                {
                    "src": base_url + "pwa/icon-512.png",
                    "sizes": "512x512",
                    "type": "image/png",
                    "purpose": "any maskable",
                },
            ],
        }
        self.write(json.dumps(manifest, indent=2))


class PWAIconHandler(RequestHandler):
    """Serve PWA PNG icons from package data."""

    def get(self, size: str):
        path = HERE / "icons" / f"icon-{size}.png"
        if not path.exists():
            raise FileNotFoundError(f"Icon {size} not found: {path}")
        self.set_header("Content-Type", "image/png")
        self.set_header("Cache-Control", "public, max-age=86400")
        with open(path, "rb") as f:
            self.write(f.read())


class PWAAppleTouchIconHandler(RequestHandler):
    """Serve the Apple touch icon (180x180)."""

    def get(self):
        path = HERE / "icons" / "apple-touch-icon.png"
        if not path.exists():
            raise FileNotFoundError(f"Apple touch icon not found: {path}")
        self.set_header("Content-Type", "image/png")
        self.set_header("Cache-Control", "public, max-age=86400")
        with open(path, "rb") as f:
            self.write(f.read())


class PWAServiceWorkerHandler(RequestHandler):
    """Serve the service worker JavaScript.

    The Service-Worker-Allowed header lets the SW register with a scope
    broader than its own path (matching code-server's approach).
    """

    def get(self):
        sw_path = HERE / "sw.js"
        self.set_header("Content-Type", "application/javascript")
        self.set_header("Service-Worker-Allowed", "/")
        self.set_header("Cache-Control", "no-cache")
        with open(sw_path, "r") as f:
            self.write(f.read())


def _build_pwa_tags(base_url: str) -> str:
    """Build the PWA HTML tags to inject before </head>."""
    sw_url = base_url + "pwa/sw.js"
    manifest_url = base_url + "pwa/manifest.json"
    return (
        '<link rel="manifest" href="' + manifest_url + '">\n'
        '  <meta name="mobile-web-app-capable" content="yes">\n'
        '  <meta name="apple-mobile-web-app-capable" content="yes">\n'
        '  <meta name="apple-mobile-web-app-status-bar-style" content="default">\n'
        '  <meta name="apple-mobile-web-app-title" content="JupyterLab">\n'
        '  <meta name="theme-color" content="#f37726">\n'
        '  <link rel="apple-touch-icon" href="' + base_url + 'pwa/apple-touch-icon.png">\n'
        '  <script>\n'
        "    if ('serviceWorker' in navigator) {\n"
        "      navigator.serviceWorker.register('" + sw_url + "').catch(function(e){\n"
        "        console.warn('[jupyterlab-pwa] SW registration failed:', e);\n"
        "      });\n"
        "    }\n"
        "  </script>\n"
        "  "
    )


def wrap_lab_handler(serverapp):
    """Wrap LabHandler.get() to inject PWA tags into rendered HTML.

    This is Option B: instead of overriding the HTML template (fragile —
    breaks when JupyterLab updates JS bundle hashes), we wrap the live
    handler. JupyterLab renders its own current index.html with current
    page_config, and we inject PWA tags into the output string before </head>.
    """
    try:
        from jupyterlab_server.handlers import LabHandler
    except ImportError:
        serverapp.log.warning(
            "[jupyterlab-pwa] jupyterlab_server not found — PWA tags will not be injected. "
            "Ensure JupyterLab is installed."
        )
        return

    original_get = LabHandler.get

    def patched_get(self, mode=None, workspace=None, tree=None):
        # Call the original handler to render the HTML
        original_get(self, mode, workspace, tree)

        # Inject PWA tags into the rendered output
        # self._write_buffer holds the rendered HTML from self.write()
        base_url = self.settings.get("base_url", "/")
        pwa_tags = _build_pwa_tags(base_url)

        # Access the write buffer — Tornado stores written data as bytes in _write_buffer
        write_buffer = getattr(self, "_write_buffer", None)
        if write_buffer:
            html = write_buffer[-1]
            if isinstance(html, bytes):
                html = html.decode("utf-8", errors="replace")
            # Inject before </head> (skip redirects/error pages that don't have it)
            if "</head>" in html:
                html = html.replace("</head>", pwa_tags + "</head>", 1)
                write_buffer[-1] = html.encode("utf-8")

    LabHandler.get = patched_get
    serverapp.log.info("[jupyterlab-pwa] LabHandler.get() wrapped for PWA tag injection")


def _setup_pwa(serverapp):
    """Register PWA handlers and wrap LabHandler on server startup."""
    from jupyter_server.utils import url_path_join

    base_url = serverapp.web_app.settings["base_url"]

    # Register PWA routes
    handlers = [
        (url_path_join(base_url, "pwa/manifest.json"), PWAManifestHandler),
        (url_path_join(base_url, "pwa/icon-([0-9]+).png"), PWAIconHandler),
        (url_path_join(base_url, "pwa/apple-touch-icon.png"), PWAAppleTouchIconHandler),
        (url_path_join(base_url, "pwa/sw.js"), PWAServiceWorkerHandler),
    ]
    serverapp.web_app.add_handlers(".*$", handlers)
    serverapp.log.info(f"[jupyterlab-pwa] PWA routes registered at {base_url}pwa/")

    # Wrap LabHandler to inject PWA tags
    wrap_lab_handler(serverapp)
