self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open('weather-app-cache').then((cache) => {
      return cache.addAll([
        '/',
        '/static/manifest.json',
        '/static/dark_mode.jpg'
      ]);
    })
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request);
    })
  );
});
