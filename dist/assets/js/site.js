(function () {
  "use strict";

  var MODAL_KEY = "ac_join_modal_seen";
  var JOINED_KEY = "ac_joined";
  var MODAL_COOLDOWN_DAYS = 14;

  function store(key, value) {
    try {
      if (value === undefined) return window.localStorage.getItem(key);
      window.localStorage.setItem(key, value);
    } catch (e) {
      return null;
    }
    return null;
  }

  function track(name, props) {
    try {
      if (window.plausible) window.plausible(name, { props: props });
      if (window.gtag) window.gtag("event", name, props);
      if (window.fbq) window.fbq("trackCustom", name, props);
    } catch (e) {}
  }

  /* ---------- release countdown ---------- */
  function pad(n) { return n < 10 ? "0" + n : String(n); }
  document.querySelectorAll("[data-countdown]").forEach(function (board) {
    var target = new Date(board.getAttribute("data-countdown")).getTime();
    var cells = {
      d: board.querySelector("[data-unit=d]"),
      h: board.querySelector("[data-unit=h]"),
      m: board.querySelector("[data-unit=m]"),
      s: board.querySelector("[data-unit=s]")
    };
    var out = document.querySelector(board.getAttribute("data-countdown-done") || "#none");
    function tick() {
      var left = Math.max(0, target - Date.now());
      if (left === 0) {
        board.hidden = true;
        if (out) out.hidden = false;
        return false;
      }
      var s = Math.floor(left / 1000);
      cells.d.textContent = String(Math.floor(s / 86400));
      cells.h.textContent = pad(Math.floor((s % 86400) / 3600));
      cells.m.textContent = pad(Math.floor((s % 3600) / 60));
      cells.s.textContent = pad(s % 60);
      return true;
    }
    if (tick()) {
      var id = setInterval(function () { if (!tick()) clearInterval(id); }, 1000);
    }
  });

  /* ---------- newsletter forms ---------- */
  var EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

  document.querySelectorAll("form[data-signup]").forEach(function (form) {
    var errorEl = form.querySelector(".signup-error");
    var doneEl = form.parentNode.querySelector(".signup-done");
    var action = form.getAttribute("data-action");
    var fallback = form.getAttribute("data-fallback");

    function showDone() {
      form.hidden = true;
      if (doneEl) doneEl.hidden = false;
      store(JOINED_KEY, "1");
    }

    form.addEventListener("submit", function (e) {
      var email = form.querySelector("input[type=email]");
      if (!EMAIL_RE.test((email.value || "").trim())) {
        e.preventDefault();
        if (errorEl) {
          errorEl.textContent = "Enter a full email address, like name@example.com.";
          errorEl.hidden = false;
        }
        email.focus();
        return;
      }
      if (errorEl) errorEl.hidden = true;
      track("Newsletter Signup", { form: form.getAttribute("data-signup") });

      if (action) {
        // Posts to MailerLite through a hidden iframe so the reader never leaves the page.
        form.action = action;
        form.target = "ml-frame";
        setTimeout(showDone, 600);
        return;
      }
      e.preventDefault();
      window.location.href = fallback;
    });
  });

  /* ---------- join modal ---------- */
  var modal = document.getElementById("join-modal");
  if (modal && typeof modal.showModal === "function") {
    var seen = parseInt(store(MODAL_KEY) || "0", 10);
    var cooled = !seen || Date.now() - seen > MODAL_COOLDOWN_DAYS * 86400000;
    var shown = false;

    function openModal(reason) {
      if (shown || store(JOINED_KEY) === "1" || !cooled) return;
      if (document.querySelector("dialog[open]")) return;
      shown = true;
      store(MODAL_KEY, String(Date.now()));
      modal.showModal();
      track("Join Modal Shown", { reason: reason });
    }

    setTimeout(function () { openModal("timer"); }, 40000);
    window.addEventListener("scroll", function onScroll() {
      var depth = (window.scrollY + window.innerHeight) / document.documentElement.scrollHeight;
      if (depth > 0.7) {
        window.removeEventListener("scroll", onScroll);
        openModal("scroll");
      }
    }, { passive: true });
    document.addEventListener("mouseout", function (e) {
      if (!e.relatedTarget && e.clientY <= 0) openModal("exit");
    });

    modal.addEventListener("click", function (e) {
      if (e.target === modal || e.target.closest("[data-close]")) modal.close();
    });
  }

  document.querySelectorAll("[data-open-join]").forEach(function (btn) {
    btn.addEventListener("click", function (e) {
      if (!modal || typeof modal.showModal !== "function") return;
      e.preventDefault();
      modal.showModal();
    });
  });

  /* ---------- outbound click tracking ---------- */
  document.addEventListener("click", function (e) {
    var link = e.target.closest("a[data-track]");
    if (!link) return;
    track("Retailer Click", {
      book: link.getAttribute("data-book") || "",
      store: link.getAttribute("data-track")
    });
  });

  /* ---------- copy contact email ---------- */
  document.querySelectorAll("[data-copy]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var text = btn.getAttribute("data-copy");
      var label = btn.textContent;
      function done(msg) {
        btn.textContent = msg;
        setTimeout(function () { btn.textContent = label; }, 1800);
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function () { done("Copied"); }, function () { done("Select and copy"); });
      } else {
        done("Select and copy");
      }
    });
  });
})();
