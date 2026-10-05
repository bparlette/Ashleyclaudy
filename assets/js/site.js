/* Ashley Claudy — interactions (arlo-redesign). Vanilla, no frameworks. */
(function () {
  "use strict";

  var MODAL_KEY = "ac_join_modal_seen";
  var JOINED_KEY = "ac_joined";
  var MODAL_COOLDOWN_DAYS = 14;
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function store(key, value) {
    try {
      if (value === undefined) return window.localStorage.getItem(key);
      window.localStorage.setItem(key, value);
    } catch (e) { return null; }
    return null;
  }

  function track(name, props) {
    try {
      if (window.plausible) window.plausible(name, { props: props });
      if (window.gtag) window.gtag("event", name, props);
      if (window.fbq) window.fbq("trackCustom", name, props);
    } catch (e) {}
  }

  /* ---------- toast ---------- */
  var toastEl = null, toastTimer = null;
  function toast(msg) {
    if (!toastEl) {
      toastEl = document.createElement("div");
      toastEl.className = "toast";
      toastEl.setAttribute("role", "status");
      document.body.appendChild(toastEl);
    }
    toastEl.textContent = msg;
    toastEl.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toastEl.classList.remove("show"); }, 2200);
  }

  /* ---------- header scroll state ---------- */
  var head = document.querySelector(".site-head");
  function onScrollHead() {
    if (head) head.classList.toggle("scrolled", window.scrollY > 24);
  }
  window.addEventListener("scroll", onScrollHead, { passive: true });
  onScrollHead();

  /* ---------- mobile menu ---------- */
  var menuBtn = document.querySelector("[data-menu-btn]");
  if (menuBtn) {
    menuBtn.addEventListener("click", function () {
      var open = document.body.classList.toggle("menu-open");
      menuBtn.setAttribute("aria-expanded", open ? "true" : "false");
    });
    document.querySelectorAll(".menu-overlay a").forEach(function (a) {
      a.addEventListener("click", function () {
        document.body.classList.remove("menu-open");
        menuBtn.setAttribute("aria-expanded", "false");
      });
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") {
        document.body.classList.remove("menu-open");
        menuBtn.setAttribute("aria-expanded", "false");
      }
    });
  }

  /* ---------- reveal on scroll ---------- */
  var revealEls = document.querySelectorAll(".reveal");
  function revealAll() {
    revealEls.forEach(function (el) { el.classList.add("in"); });
  }
  if (revealEls.length && "IntersectionObserver" in window && !reduceMotion) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) {
          en.target.classList.add("in");
          io.unobserve(en.target);
        }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -6% 0px" });
    revealEls.forEach(function (el) { io.observe(el); });
    // Safety net: never leave content invisible (e.g. IO quirks, print, screenshots).
    setTimeout(revealAll, 3500);
  } else {
    revealAll();
  }

  /* ---------- hero parallax (transform only) ---------- */
  var heroBg = document.querySelector(".hero-bg img");
  if (heroBg && !reduceMotion) {
    var ticking = false;
    window.addEventListener("scroll", function () {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(function () {
        var y = Math.min(window.scrollY, window.innerHeight);
        heroBg.style.transform = "scale(1.06) translateY(" + (y * 0.12) + "px)";
        ticking = false;
      });
    }, { passive: true });
  }

  /* ---------- count-up stats ---------- */
  function parseFigure(text) {
    var m = text.replace(/,/g, "").match(/^([\d.]+)(.*)$/);
    return m ? { num: parseFloat(m[1]), suffix: m[2] } : null;
  }
  document.querySelectorAll("[data-countup]").forEach(function (el) {
    var parsed = parseFigure(el.textContent.trim());
    if (!parsed || reduceMotion || !("IntersectionObserver" in window)) return;
    var target = parsed.num, suffix = parsed.suffix;
    var decimals = String(parsed.num).indexOf(".") > -1 ? 1 : 0;
    var cio = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        cio.disconnect();
        var start = null, dur = 1400;
        function frame(t) {
          if (!start) start = t;
          var p = Math.min((t - start) / dur, 1);
          var eased = 1 - Math.pow(1 - p, 3);
          var val = target * eased;
          el.textContent = (decimals ? val.toFixed(1) : Math.round(val).toLocaleString("en-US")) + suffix;
          if (p < 1) requestAnimationFrame(frame);
        }
        requestAnimationFrame(frame);
      });
    }, { threshold: 0.4 });
    cio.observe(el);
  });

  /* ---------- sticky buy bar ---------- */
  var buybar = document.querySelector("[data-buybar]");
  var heroSentinel = document.querySelector("[data-buybar-sentinel]");
  if (buybar && heroSentinel && "IntersectionObserver" in window) {
    new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        buybar.classList.toggle("show", !en.isIntersecting);
      });
    }, { rootMargin: "-8% 0px 0px 0px" }).observe(heroSentinel);
  }

  /* ---------- share (Web Share API + clipboard fallback) ---------- */
  document.querySelectorAll("[data-share]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var title = btn.getAttribute("data-share-title") || document.title;
      var text = btn.getAttribute("data-share-text") || "";
      var url = btn.getAttribute("data-share-url") || window.location.href;
      track("Share", { title: title });
      function copied() { toast("Link copied — paste it anywhere"); }
      if (navigator.share) {
        navigator.share({ title: title, text: text, url: url }).catch(function () {});
      } else if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(copied, function () { toast("Copy this link: " + url); });
      } else {
        toast("Copy this link: " + url);
      }
    });
  });

  /* ---------- reading-order accordion ---------- */
  document.querySelectorAll("[data-acc]").forEach(function (item) {
    var headBtn = item.querySelector("[data-acc-head]");
    var panel = item.querySelector("[data-acc-panel]");
    if (!headBtn || !panel) return;
    headBtn.addEventListener("click", function () {
      var isOpen = item.classList.contains("open");
      document.querySelectorAll("[data-acc].open").forEach(function (other) {
        other.classList.remove("open");
        other.querySelector("[data-acc-panel]").style.maxHeight = null;
        other.querySelector("[data-acc-head]").setAttribute("aria-expanded", "false");
      });
      if (!isOpen) {
        item.classList.add("open");
        panel.style.maxHeight = panel.scrollHeight + "px";
        headBtn.setAttribute("aria-expanded", "true");
      }
    });
  });
  // Open the first accordion item by default on the home page.
  var firstAcc = document.querySelector("[data-acc]");
  if (firstAcc && firstAcc.hasAttribute("data-acc-open")) {
    firstAcc.querySelector("[data-acc-head]").click();
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

    setTimeout(function () { openModal("timer"); }, 45000);
    window.addEventListener("scroll", function onScroll() {
      var depth = (window.scrollY + window.innerHeight) / document.documentElement.scrollHeight;
      if (depth > 0.75) {
        window.removeEventListener("scroll", onScroll);
        openModal("scroll");
      }
    }, { passive: true });

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
