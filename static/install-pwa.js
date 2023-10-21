let deferredPromot;

window.addEventListener('beforeinstallpromot', (e) =>{
    //evitar que o prompt padrão seja exibido
    e.preventDefault();
    // armazenar o evento para mostrar o prompt mais tarde
    deferredPrompt = e;
    //exibir um botão ou outra UI para iniciar a instalação
    // aqui você pode exibir um botão "instalar App" e vincular a deferr
});