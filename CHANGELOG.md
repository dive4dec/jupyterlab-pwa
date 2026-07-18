# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-07-18

### Fixed
- Add `shared-data` config file (`etc/jupyter_server_config.d/jupyterlab_pwa.json`) to wheel so the server extension is **auto-enabled** on `pip install`. Without this, the package installed but the extension never loaded.

## [0.1.0] - 2026-07-18

### Added
- PWA (Progressive Web App) support for JupyterLab via a server extension.
- **Handler wrapper (Option B)**: wraps `jupyterlab_server.handlers.LabHandler.get()`
  to inject `<link rel="manifest">`, `<script>navigator.serviceWorker.register()</script>`,
  apple-mobile-web-app meta tags, and theme-color into the rendered HTML before `</head>`.
  This survives JupyterLab updates because it wraps the live handler — no template
  override, no static file copy. JupyterLab renders its own current `index.html`
  with current JS bundle hashes and page_config; we inject PWA tags post-render.
- Tornado handlers serving `/pwa/manifest.json`, `/pwa/sw.js`, `/pwa/icon-{size}.png`,
  `/pwa/apple-touch-icon.png` on the user pod.
- Service worker with `Service-Worker-Allowed: /` header (modeled on code-server).
- CS1302 logo icons (192px, 512px, 180px apple-touch-icon).

### Design
- Modeled on code-server's PWA approach: manifest + SW served by app routes,
  PWA tags in HTML. Key difference: code-server bakes tags in HTML templates
  and registers SW via patched VSCode frontend; we inject tags post-render via
  handler wrapping (more robust across JupyterLab version upgrades) and register
  SW via injected `<script>`.
