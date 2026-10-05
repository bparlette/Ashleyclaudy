(function () {
  "use strict";

  var root = document.documentElement;
  var MODAL_KEY = "ac_join_modal_seen";
  var JOINED_KEY = "ac_joined";
  var MODAL_COOLDOWN_DAYS = 14;
  var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var finePointer = window.matchMedia && window.matchMedia("(hover: hover) and (pointer: fine)").matches;

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

  if (store(JOINED_KEY) === "1") root.classList.add("joined");

  /* ---------- header turns solid after the hero ---------- */
  var head = document.querySelector(".site-head");
  if (head) {
    var onScroll = function () { head.classList.toggle("scrolled", window.scrollY > 24); };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  var menu = document.querySelector(".menu");
  if (menu) {
    menu.addEventListener("click", function (e) {
      if (e.target.closest(".menu-panel a")) menu.removeAttribute("open");
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") menu.removeAttribute("open");
    });
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

  document.querySelectorAll("[data-days-until]").forEach(function (el) {
    var days = Math.floor((new Date(el.getAttribute("data-days-until")).getTime() - Date.now()) / 86400000);
    if (days > 0) el.textContent = String(days);
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
      root.classList.add("joined");
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

  /* ---------- desktop-only exit popup (never on phones) ---------- */
  var modal = document.getElementById("join-modal");
  if (modal && finePointer && typeof modal.showModal === "function") {
    var seen = parseInt(store(MODAL_KEY) || "0", 10);
    var cooled = !seen || Date.now() - seen > MODAL_COOLDOWN_DAYS * 86400000;
    var shown = false;

    var openModal = function (reason) {
      if (shown || store(JOINED_KEY) === "1" || !cooled) return;
      if (document.querySelector("dialog[open]") || document.getElementById("join") && isVisible(document.getElementById("join"))) return;
      shown = true;
      store(MODAL_KEY, String(Date.now()));
      modal.showModal();
      track("Join Modal Shown", { reason: reason });
    };
    var isVisible = function (el) {
      var r = el.getBoundingClientRect();
      return r.top < window.innerHeight && r.bottom > 0;
    };

    setTimeout(function () { openModal("timer"); }, 60000);
    document.addEventListener("mouseout", function (e) {
      if (!e.relatedTarget && e.clientY <= 0) openModal("exit");
    });
    modal.addEventListener("click", function (e) {
      if (e.target === modal || e.target.closest("[data-close]")) modal.close();
    });
  }

  /* ---------- sticky buy bar (phones) ---------- */
  var dock = document.querySelector(".dock");
  if (dock && "IntersectionObserver" in window) {
    var watched = document.querySelectorAll("[data-dock-watch]");
    var visible = new Set();
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) visible.add(en.target); else visible.delete(en.target);
      });
      dock.classList.toggle("on", visible.size === 0);
    }, { rootMargin: "0px 0px -72px 0px" });
    watched.forEach(function (el) { io.observe(el); });
  }

  /* ---------- scroll reveal ---------- */
  var revealEls = document.querySelectorAll(".reveal");
  if (revealEls.length) {
    if ("IntersectionObserver" in window && !reduceMotion) {
      var rio = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) {
            en.target.classList.add("in");
            rio.unobserve(en.target);
          }
        });
      }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
      revealEls.forEach(function (el) { rio.observe(el); });
      setTimeout(function () { revealEls.forEach(function (el) { el.classList.add("in"); }); }, 6000);
    } else {
      revealEls.forEach(function (el) { el.classList.add("in"); });
    }
  }

  /* ---------- cover tilt (mouse only) ---------- */
  if (finePointer && !reduceMotion) {
    document.querySelectorAll("[data-tilt]").forEach(function (el) {
      var raf = 0;
      el.addEventListener("pointermove", function (e) {
        var b = el.getBoundingClientRect();
        var px = (e.clientX - b.left) / b.width - 0.5;
        var py = (e.clientY - b.top) / b.height - 0.5;
        cancelAnimationFrame(raf);
        raf = requestAnimationFrame(function () {
          el.style.setProperty("--ry", (px * 12).toFixed(2) + "deg");
          el.style.setProperty("--rx", (-py * 12).toFixed(2) + "deg");
        });
      });
      el.addEventListener("pointerleave", function () {
        cancelAnimationFrame(raf);
        el.style.setProperty("--ry", "0deg");
        el.style.setProperty("--rx", "0deg");
      });
    });
  }

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
