// MonteBuild: ссылки при просмотре с компьютера, слайдер «до/после», заявка в WhatsApp
(function () {
  // 1) Если сайт открыт как файл (file://), переписываем ссылки, чтобы меню работало и без хостинга
  if (location.protocol === 'file:') {
    var s = document.querySelector('script[src$="assets/site.js"]');
    var root = s.src.replace(/assets\/site\.js.*$/, '');
    document.querySelectorAll('a[href^="/"]').forEach(function (a) {
      var h = a.getAttribute('href');
      if (h.indexOf('//') === 0) return;
      var hash = '', i = h.indexOf('#');
      if (i > -1) { hash = h.slice(i); h = h.slice(0, i); }
      h = h.replace(/^\//, '');
      if (h === '' || h.slice(-1) === '/') h += 'index.html';
      a.setAttribute('href', root + h + hash);
    });
  }

  // 2) Слайдер «до/после»: тянется пальцем, мышью и стрелками клавиатуры
  document.querySelectorAll('[data-ba]').forEach(function (ba) {
    var handle = ba.querySelector('.ba-handle'), pos = 50, drag = false;
    function set(p) {
      pos = Math.max(0, Math.min(100, p));
      ba.style.setProperty('--pos', pos + '%');
      handle.setAttribute('aria-valuenow', Math.round(pos));
    }
    function fromEvent(e) {
      var r = ba.getBoundingClientRect();
      set((e.clientX - r.left) / r.width * 100);
    }
    ba.addEventListener('pointerdown', function (e) {
      drag = true; try { ba.setPointerCapture(e.pointerId); } catch (x) {} fromEvent(e);
    });
    ba.addEventListener('pointermove', function (e) { if (drag) fromEvent(e); });
    ba.addEventListener('pointerup', function () { drag = false; });
    ba.addEventListener('pointercancel', function () { drag = false; });
    handle.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowLeft') { set(pos - 5); e.preventDefault(); }
      if (e.key === 'ArrowRight') { set(pos + 5); e.preventDefault(); }
    });
  });

  // 3) Форма заявки -> WhatsApp
  document.querySelectorAll('.lead-form').forEach(function (f) {
    f.addEventListener('submit', function (e) {
      e.preventDefault();
      var d = new FormData(f);
      var t = 'Здравствуйте! Заявка с сайта MonteBuild.\nИмя: ' + d.get('name') + '\nТелефон: ' + d.get('phone') +
        (d.get('service') ? '\nУслуга: ' + d.get('service') : '') + (d.get('msg') ? '\nДетали: ' + d.get('msg') : '');
      window.open('https://wa.me/' + f.dataset.wa + '?text=' + encodeURIComponent(t), '_blank', 'noopener');
    });
  });
})();
