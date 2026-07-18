// Minimal service worker for PWA installability.
// Chrome requires a fetch handler to recognize the app as installable.
// Modeled on code-server's serviceWorker.ts.
self.addEventListener("install", () => {
  console.debug("[jupyterlab-pwa] service worker installed");
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
  console.debug("[jupyterlab-pwa] service worker activated");
});

self.addEventListener("fetch", () => {
  // Without this empty fetch handler we won't be recognized as a PWA.
});
