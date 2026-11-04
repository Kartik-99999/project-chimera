/* Demo step slider: progressive enhancement over #demoStepList.
 * The inspector repaints the step list on every scenario switch, so this
 * watches the host and rebuilds the sliding window whenever fresh,
 * unwrapped .insp-step rows appear. Zero dependencies, no auto-motion.
 * Vertical page scroll is never hijacked (touch-action: pan-y plus
 * horizontal/vertical swipe disambiguation). Every panel stays reachable
 * by buttons, named dots, and arrow keys; reduced-motion users get an
 * instant change via CSS (see .sa-track).
 */
(function () {
  'use strict';

  function stepName(step, k) {
    var a = step.querySelector('.insp-step-action');
    var t = a ? a.textContent.replace(/\s+/g, ' ').trim() : '';
    if (!t) t = 'step ' + (k + 1);
    return t.length > 48 ? t.slice(0, 47) + '…' : t;
  }

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }

  function build(host) {
    var fresh = [];
    for (var c = 0; c < host.children.length; c += 1) {
      var kid = host.children[c];
      if (kid.classList && kid.classList.contains('insp-step')) fresh.push(kid);
    }
    if (!fresh.length) return false; // loading / error / already wrapped: leave it
    var n = fresh.length;

    host.classList.add('sa-view');
    var region = host.closest('.insp-col');
    if (region && !region.hasAttribute('data-sa-region')) {
      region.setAttribute('data-sa-region', '1');
      region.setAttribute('role', 'region');
      region.setAttribute('aria-roledescription', 'carousel');
      region.setAttribute('aria-label', 'Recorded execution steps');
    }

    var track = el('div', 'sa-track');
    var names = fresh.map(function (s, k) {
      s.classList.add('sa-step');
      s.setAttribute('role', 'tabpanel');
      var name = stepName(s, k);
      s.setAttribute('aria-label', 'Step ' + (k + 1) + ' of ' + n + ': ' + name);
      track.appendChild(s);
      return name;
    });
    host.appendChild(track);

    var controls = host.parentNode.querySelector(':scope > .sa-controls');
    var prev, next, dotsBox, count;
    if (!controls) {
      controls = el('div', 'sa-controls');
      prev = el('button', 'sa-nav', '←');
      prev.type = 'button';
      prev.setAttribute('aria-label', 'Previous step');
      dotsBox = el('div', 'sa-dots');
      dotsBox.setAttribute('role', 'tablist');
      dotsBox.setAttribute('aria-label', 'Execution steps');
      next = el('button', 'sa-nav', '→');
      next.type = 'button';
      next.setAttribute('aria-label', 'Next step');
      count = el('span', 'sa-count');
      count.setAttribute('aria-live', 'polite');
      controls.appendChild(prev);
      controls.appendChild(dotsBox);
      controls.appendChild(next);
      controls.appendChild(count);
      host.parentNode.insertBefore(controls, host.nextSibling);
    } else {
      prev = controls.querySelector('.sa-nav:first-child');
      dotsBox = controls.querySelector('.sa-dots');
      next = controls.querySelectorAll('.sa-nav')[1];
      count = controls.querySelector('.sa-count');
      dotsBox.innerHTML = '';
    }

    var state = host._sa || (host._sa = {});
    state.index = 0;
    state.total = n;
    var dots = names.map(function (name, k) {
      var d = el('button', 'sa-dot');
      d.type = 'button';
      d.setAttribute('role', 'tab');
      d.setAttribute('aria-label', 'Go to step ' + (k + 1) + ': ' + name);
      d.appendChild(el('i'));
      d.addEventListener('click', function () { go(k); });
      dotsBox.appendChild(d);
      return d;
    });

    var showNav = n > 1;
    prev.style.display = showNav ? '' : 'none';
    next.style.display = showNav ? '' : 'none';
    dotsBox.style.display = showNav ? '' : 'none';

    function go(k) {
      state.index = ((k % n) + n) % n;
      track.style.transform = 'translateX(-' + state.index * 100 + '%)';
      fresh.forEach(function (s, k2) {
        s.setAttribute('aria-hidden', k2 === state.index ? 'false' : 'true');
      });
      dots.forEach(function (d, k2) {
        d.setAttribute('aria-selected', k2 === state.index ? 'true' : 'false');
        d.tabIndex = k2 === state.index ? 0 : -1;
      });
      count.textContent = (state.index + 1) + ' / ' + n;
    }
    state.go = go;

    prev.onclick = function () { go(state.index - 1); };
    next.onclick = function () { go(state.index + 1); };

    if (!host._saWired) {
      host._saWired = true;
      if (region) {
        region.addEventListener('keydown', function (e) {
          var st = host._sa;
          if (!st || !st.go || st.total < 2) return;
          var k = null;
          if (e.key === 'ArrowRight' || e.key === 'ArrowDown') k = st.index + 1;
          else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') k = st.index - 1;
          else if (e.key === 'Home') k = 0;
          else if (e.key === 'End') k = st.total - 1;
          else return;
          e.preventDefault();
          st.go(k);
          var dotsNow = host.parentNode.querySelectorAll(':scope > .sa-controls .sa-dot');
          if (document.activeElement && document.activeElement.classList
              && document.activeElement.classList.contains('sa-dot') && dotsNow[st.index]) {
            dotsNow[st.index].focus();
          }
        });
      }
      var sx = 0, sy = 0, dx = 0, dy = 0, live = false;
      host.addEventListener('pointerdown', function (e) {
        live = true; sx = e.clientX; sy = e.clientY; dx = 0; dy = 0;
      });
      host.addEventListener('pointermove', function (e) {
        if (!live) return; dx = e.clientX - sx; dy = e.clientY - sy;
      });
      host.addEventListener('pointerup', function () {
        if (!live) return; live = false;
        var st = host._sa;
        if (!st || !st.go) return;
        if (Math.abs(dx) > 48 && Math.abs(dx) > Math.abs(dy) * 1.4) {
          st.go(st.index + (dx < 0 ? 1 : -1));
        }
      });
      host.addEventListener('pointercancel', function () { live = false; });
    }

    go(0);
    return true;
  }

  function init() {
    var host = document.getElementById('demoStepList');
    if (!host) return;
    build(host);
    if (window.MutationObserver) {
      var obs = new MutationObserver(function () { build(host); });
      obs.observe(host, { childList: true });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
