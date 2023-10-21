const CAHE_NAME='my-pwa-cache-v1';
const cacheUrls = [
    '/',
    '/static/icon.png', // certifique-se de incluir os recursos que 
    '/static/other-resource.js',
    '/static/other-resource.css',
    // adicione outros recursos estaticos que dejesa em cache
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                return cache.addALL(cacheUrls);
            })
    );
});    

self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request)
        .then((response) => {
            return response || fetch(event.request);
        })
    );
});
