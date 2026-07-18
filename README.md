# jupyterlab-pwa

Progressive Web App (PWA) support for JupyterLab.

Makes JupyterLab installable (Chrome/Edge "Install app" button, iOS "Add to
Home Screen") by serving a web app manifest, a service worker with a fetch
handler, and injecting PWA tags into JupyterLab's HTML — all from the user
server. No JupyterHub config or ingress changes required.

## Install

```bash
pip install jupyterlab-pwa
```

The server extension auto-loads via the `_jupyter_server_extension_points`
entry point. No manual configuration needed.

## How it works

Three pieces, all served by the user pod:

1. **Manifest** (`/pwa/manifest.json`) — web app manifest with name, icons,
   `start_url`, `scope`, `display: standalone`.
2. **Service worker** (`/pwa/sw.js`) — minimal SW with `install`, `activate`,
   and `fetch` event listeners (enough for Chrome's installability criterion).
3. **HTML injection** — wraps JupyterLab's `LabHandler.get()` to inject
   `<link rel="manifest">` and `<script>navigator.serviceWorker.register()</script>`
   into the rendered HTML, before `</head>`.

This matches how code-server handles PWA — all logic lives in the application,
served by its own routes, tags in its own HTML.
