(function () {
  var root = document.querySelector('[data-auto-refresh]');
  if (!root) {
    return;
  }

  var seconds = parseInt(root.getAttribute('data-auto-refresh'), 10);
  if (!seconds || seconds < 30) {
    return;
  }

  var info = document.createElement('p');
  info.className = 'muted refresh-counter';
  root.appendChild(info);

  var remaining = seconds;
  function paint() {
    info.textContent = 'Próxima atualização automática em ' + remaining + 's';
  }

  paint();
  setInterval(function () {
    remaining -= 1;
    if (remaining <= 0) {
      window.location.reload();
      return;
    }
    paint();
  }, 1000);
})();
