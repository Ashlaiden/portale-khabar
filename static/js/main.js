/*
 * Front-end behaviour for Portale Khabar.
 *
 * Kept dependency-free (vanilla JS) on purpose. Two features:
 *
 *   1. Like / Dislike buttons -> POST to /like/<id>/ and update the counters
 *      without a page reload. Gracefully degrades: if JS is off, the button
 *      is a normal form submit.
 *
 *   2. Comment form -> submit via fetch and show a success/error toast.
 *
 * The CSRF token is read from a <meta> tag injected by base.html.
 */

(function () {
  'use strict';

  // -- CSRF helper --------------------------------------------------------
  function getCSRFToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
  }

  // -- Tiny toast notification -------------------------------------------
  function showToast(message, type) {
    type = type || 'success';
    let host = document.getElementById('toast-host');
    if (!host) {
      host = document.createElement('div');
      host.id = 'toast-host';
      host.className = 'fixed bottom-5 left-5 z-[100] flex flex-col gap-2';
      document.body.appendChild(host);
    }
    const el = document.createElement('div');
    const color =
      type === 'error'
        ? 'bg-red-500/90 border-red-400'
        : 'bg-emerald-500/90 border-emerald-400';
    el.className =
      'glass border ' + color + ' text-white px-4 py-2 rounded-xl shadow-glass animate-fade-in text-sm';
    el.textContent = message;
    host.appendChild(el);
    setTimeout(function () {
      el.style.transition = 'opacity .4s ease';
      el.style.opacity = '0';
      setTimeout(function () { el.remove(); }, 400);
    }, 3500);
  }

  // -- Like / Dislike -----------------------------------------------------
  function setupLikeButtons() {
    const container = document.querySelector('[data-article-id]');
    if (!container) return;
    const articleId = container.getAttribute('data-article-id');

    document.querySelectorAll('[data-vote]').forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        const value = btn.getAttribute('data-vote'); // 'like' | 'dislike'
        fetch('/like/' + articleId + '/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCSRFToken(),
            'X-Requested-With': 'XMLHttpRequest',
          },
          body: 'value=' + encodeURIComponent(value),
        })
          .then(function (r) { return r.json(); })
          .then(function (data) {
            if (!data.ok) {
              showToast(data.error || 'خطا در ثبت رای.', 'error');
              return;
            }
            updateVoteUI(data);
          })
          .catch(function () {
            showToast('ارتباط با سرور برقرار نشد.', 'error');
          });
      });
    });
  }

  function updateVoteUI(data) {
    const likeBtn = document.querySelector('[data-vote="like"]');
    const dislikeBtn = document.querySelector('[data-vote="dislike"]');
    const likeCount = document.getElementById('like-count');
    const dislikeCount = document.getElementById('dislike-count');

    if (likeCount) likeCount.textContent = data.likes;
    if (dislikeCount) dislikeCount.textContent = data.dislikes;

    // Highlight the currently-active button.
    if (likeBtn) likeBtn.classList.toggle('btn-primary', data.value === 1);
    if (likeBtn) likeBtn.classList.toggle('btn-ghost', data.value !== 1);
    if (dislikeBtn) dislikeBtn.classList.toggle('btn-primary', data.value === -1);
    if (dislikeBtn) dislikeBtn.classList.toggle('btn-ghost', data.value !== -1);
  }

  // -- Comment form (AJAX) ------------------------------------------------
  function setupCommentForm() {
    const form = document.getElementById('comment-form');
    if (!form) return;
    const msgBox = document.getElementById('comment-msg');
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      const fd = new FormData(form);
      fetch(form.action, {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCSRFToken(),
          'X-Requested-With': 'XMLHttpRequest',
        },
        body: fd,
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data.ok) {
            form.reset();
            if (msgBox) {
              msgBox.textContent = data.message || 'نظر شما ثبت شد و پس از تأیید مدیر نمایش داده می‌شود.';
              msgBox.className = 'rounded-xl px-4 py-3 text-sm mb-3 border bg-emerald-500/15 border-emerald-500/30 text-emerald-300';
            }
            setTimeout(function () {
              if (msgBox) msgBox.className = 'hidden rounded-xl px-4 py-3 text-sm mb-3 transition-all';
            }, 8000);
          } else {
            if (msgBox) {
              msgBox.textContent = data.error || 'خطا در ثبت نظر.';
              msgBox.className = 'rounded-xl px-4 py-3 text-sm mb-3 border bg-red-500/15 border-red-500/30 text-red-300';
            }
          }
        })
        .catch(function () {
          form.removeEventListener('submit', arguments.callee, false);
          form.submit();
        });
    });
  }
  // function setupCommentForm() {
  //   const form = document.getElementById('comment-form');
  //   if (!form) return;
  //   form.addEventListener('submit', function (e) {
  //     e.preventDefault();
  //     const fd = new FormData(form);
  //     fetch(form.action, {
  //       method: 'POST',
  //       headers: {
  //         'X-CSRFToken': getCSRFToken(),
  //         'X-Requested-With': 'XMLHttpRequest',
  //       },
  //       body: fd,
  //     })
  //       .then(function (r) { return r.json(); })
  //       .then(function (data) {
  //         if (data.ok) {
  //           showToast(data.message || 'نظر شما ثبت شد.');
  //           form.reset();
  //         } else {
  //           showToast(data.error || 'خطا در ثبت نظر.', 'error');
  //         }
  //       })
  //       .catch(function () {
  //         // Fall back to a normal submit if fetch fails for any reason.
  //         form.removeEventListener('submit', arguments.callee, false);
  //         form.submit();
  //       });
  //   });
  // }

  // -- Mobile nav toggle --------------------------------------------------
  function setupMobileNav() {
    const toggle = document.getElementById('nav-toggle');
    const menu = document.getElementById('mobile-menu');
    if (!toggle || !menu) return;
    toggle.addEventListener('click', function () {
      menu.classList.toggle('hidden');
    });
  }

  // -- Desktop search toggle ----------------------------------------------
  function setupDesktopSearch() {
    const btn = document.getElementById('nav-search-toggle');
    const box = document.getElementById('desktop-search');
    if (!btn || !box) return;
    btn.addEventListener('click', function () {
      box.classList.toggle('hidden');
      if (!box.classList.contains('hidden')) {
        const input = box.querySelector('input');
        if (input) input.focus();
      }
    });
  }

  // -- Boot ---------------------------------------------------------------
  document.addEventListener('DOMContentLoaded', function () {
    setupLikeButtons();
    setupCommentForm();
    setupMobileNav();
    setupDesktopSearch();
  });
})();
