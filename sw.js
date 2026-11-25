// Réseau d'abord (pour avoir toujours la dernière version), copie locale si pas de réseau.
const CACHE = 'app-v1'; // v2 : on redemande toujours la page au serveur (sinon le navigateur garde l'ancienne jusqu'à 10 min)
self.addEventListener('install', e => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET' || new URL(e.request.url).origin !== location.origin) return;
  const fresh = e.request.mode === 'navigate' || /\.(html|js|webmanifest)$|\/$/.test(new URL(e.request.url).pathname);
  e.respondWith(fetch(e.request, fresh ? { cache: 'no-cache' } : undefined).then(r => {
    const copy = r.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); return r;
  }).catch(() => caches.match(e.request)));
});
