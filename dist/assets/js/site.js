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
    props = props || {};
    try {
      if (window.__acStore) props.region = window.__acStore;
      if (window.__acUtm && window.__acUtm.source) props.src = window.__acUtm.source;
    } catch (e) {}
    try {
      if (window.plausible) window.plausible(name, { props: props });
      if (window.gtag) window.gtag("event", name, props);
      if (window.fbq) window.fbq("trackCustom", name, props);
    } catch (e) {}
  }

  if (store(JOINED_KEY) === "1") root.classList.add("joined");

  /* ---------- campaign source (utm_*) remembered for attribution ---------- */
  var utm = (function () {
    var out = {};
    try {
      var q = new URLSearchParams(window.location.search);
      var src = q.get("utm_source");
      if (src) {
        out = { source: src.toLowerCase(), medium: q.get("utm_medium") || "", campaign: q.get("utm_campaign") || "" };
        store("ac_utm", JSON.stringify(out));
      } else {
        out = JSON.parse(store("ac_utm") || "{}") || {};
      }
    } catch (e) { out = {}; }
    return out;
  })();
  window.__acUtm = utm;

  function fillHidden(form) {
    function put(name, val) {
      var el = form.querySelector('input[name="' + name + '"]');
      if (el && val) el.value = val;
    }
    put("fields[quiz_result]", store("ac_quiz") || "");
    put("fields[utm_source]", utm.source || "");
    put("fields[utm_medium]", utm.medium || "");
    put("fields[utm_campaign]", utm.campaign || "");
  }

  /* ---------- send readers to their own Amazon store, with the right tracking ID ---------- */
  var AMZ = window.AC_AMZ || { tags: {}, tracking: {} };
  var REGION_MAP = { GB: "co.uk", IE: "co.uk", CA: "ca", AU: "com.au", NZ: "com.au", DE: "de", AT: "de", FR: "fr", ES: "es", IT: "it", NL: "nl", IN: "in", JP: "co.jp", MX: "com.mx", BR: "com.br" };
  function detectStore() {
    var langs = navigator.languages && navigator.languages.length ? navigator.languages : [navigator.language || ""];
    for (var i = 0; i < langs.length; i++) {
      var m = /[-_]([A-Za-z]{2})$/.exec(langs[i]);
      if (m) {
        var c = m[1].toUpperCase();
        if (c === "US") return "com";
        if (REGION_MAP[c]) return REGION_MAP[c];
      }
    }
    var tz = "";
    try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone || ""; } catch (e) {}
    if (/^Europe\/(London|Dublin)$/.test(tz)) return "co.uk";
    if (/^America\/(Toronto|Vancouver|Edmonton|Winnipeg|Halifax|St_Johns|Regina)$/.test(tz)) return "ca";
    if (/^(Australia\/|Pacific\/Auckland)/.test(tz)) return "com.au";
    return "com";
  }
  function amzHref(a, domain) {
    var asin = a.getAttribute("data-asin");
    var path = a.getAttribute("data-kind") === "review" ? "/review/create-review?asin=" + asin : "/dp/" + asin;
    var tag = (AMZ.tags || {})[domain] || "";
    if (domain === "com" && utm.source && (AMZ.tracking || {})[utm.source]) tag = AMZ.tracking[utm.source];
    var url = "https://www.amazon." + domain + path;
    if (tag) url += (url.indexOf("?") > -1 ? "&" : "?") + "tag=" + encodeURIComponent(tag);
    return url;
  }
  var amzStore = store("ac_amz") || detectStore();
  function applyStore(domain) {
    amzStore = domain;
    window.__acStore = domain;
    document.querySelectorAll("a[data-asin]").forEach(function (a) {
      a.href = amzHref(a, domain);
      a.setAttribute("data-store", domain);
    });
  }
  applyStore(amzStore);
  var amzSelect = document.querySelector("[data-amz-select]");
  if (amzSelect) {
    amzSelect.value = amzStore;
    amzSelect.addEventListener("change", function () {
      store("ac_amz", amzSelect.value);
      applyStore(amzSelect.value);
    });
  }

  /* ---------- analytics consent (only when Google Analytics or Meta Pixel is switched on) ---------- */
  if (window.AC_CONSENT) {
    var banner = document.querySelector("[data-consent-banner]");
    var loadConsented = function () {
      document.querySelectorAll('script[type="text/plain"][data-consent]').forEach(function (old) {
        var n = document.createElement("script");
        if (old.getAttribute("src")) { n.src = old.getAttribute("src"); n.async = false; } else { n.text = old.text; }
        document.head.appendChild(n);
        old.parentNode.removeChild(old);
      });
    };
    var choice = store("ac_consent");
    if (choice === "yes") loadConsented();
    else if (!choice && banner) banner.hidden = false;
    if (banner) {
      banner.addEventListener("click", function (e) {
        var b = e.target.closest("[data-consent]");
        if (!b) return;
        store("ac_consent", b.getAttribute("data-consent"));
        banner.hidden = true;
        if (b.getAttribute("data-consent") === "yes") loadConsented();
      });
    }
  }

  /* ---------- sale-day banner ---------- */
  document.querySelectorAll("[data-promo]").forEach(function (bar) {
    try { if (window.sessionStorage.getItem("ac_promo_x") === "1") { bar.hidden = true; return; } } catch (e) {}
    var ends = Date.parse(bar.getAttribute("data-ends") || "");
    var clockEl = bar.querySelector("[data-promo-clock]");
    var close = bar.querySelector("[data-promo-close]");
    if (close) close.addEventListener("click", function () {
      bar.hidden = true;
      try { window.sessionStorage.setItem("ac_promo_x", "1"); } catch (e) {}
    });
    if (!ends || !clockEl) return;
    function tick() {
      var left = ends - Date.now();
      if (left <= 0) { bar.hidden = true; return false; }
      var s = Math.floor(left / 1000), d = Math.floor(s / 86400);
      var hms = pad(Math.floor((s % 86400) / 3600)) + ":" + pad(Math.floor((s % 3600) / 60)) + ":" + pad(s % 60);
      clockEl.textContent = "Ends in " + (d > 0 ? d + "d " : "") + hms;
      return true;
    }
    if (tick()) { var t = setInterval(function () { if (!tick()) clearInterval(t); }, 1000); }
  });

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
      fillHidden(form);
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

  /* ---------- click-to-load embeds (social posts, playlists): nothing third-party loads until tapped ---------- */
  document.querySelectorAll(".post").forEach(function (post) {
    var btn = post.querySelector(".post-play");
    if (!btn) return;
    btn.addEventListener("click", function () {
      var f = document.createElement("iframe");
      f.src = post.getAttribute("data-embed");
      f.title = "Social post";
      f.loading = "lazy";
      f.setAttribute("allow", "autoplay; encrypted-media; fullscreen; clipboard-write");
      f.setAttribute("allowfullscreen", "");
      post.replaceChild(f, btn);
      track("Social Post Played", {});
    });
  });

  document.querySelectorAll(".playlist").forEach(function (box) {
    var btn = box.querySelector("[data-playlist]");
    if (!btn) return;
    btn.addEventListener("click", function () {
      var f = document.createElement("iframe");
      f.src = box.getAttribute("data-embed");
      f.title = "Playlist";
      f.setAttribute("allow", "autoplay; clipboard-write; encrypted-media; fullscreen");
      box.appendChild(f);
      btn.hidden = true;
      track("Playlist Played", {});
    });
  });

  /* ---------- trailer video: plays on its own (muted) when scrolled into view, pauses when it leaves ---------- */
  var calm = reduceMotion || (navigator.connection && navigator.connection.saveData);
  document.querySelectorAll("[data-trailer]").forEach(function (wrap) {
    var v = wrap.querySelector("video");
    var btn = wrap.querySelector(".trailer-btn");
    if (!v || !btn) return;
    var userPaused = !!calm;
    var counted = false;
    v.muted = true;

    function play(manual) {
      var p = v.play();
      if (p && p.then) {
        p.then(function () {
          if (!counted) {
            counted = true;
            track(manual ? "Trailer Play" : "Trailer Autoplay", { book: wrap.getAttribute("data-book") });
          }
        }).catch(function () {});
      }
    }

    btn.addEventListener("click", function () {
      if (v.paused) { userPaused = false; play(true); }
      else { userPaused = true; v.pause(); }
    });
    v.addEventListener("play", function () { wrap.classList.add("playing"); });
    v.addEventListener("pause", function () { wrap.classList.remove("playing"); });

    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.intersectionRatio >= 0.5 && v.paused && !userPaused) play(false);
          else if (en.intersectionRatio < 0.25 && !v.paused) v.pause();
        });
      }, { threshold: [0, 0.25, 0.5, 0.75] }).observe(wrap);
    }
  });

  /* ---------- audio sample player ---------- */
  function clock(sec) {
    if (!isFinite(sec)) return "0:00";
    var m = Math.floor(sec / 60), s = Math.floor(sec % 60);
    return m + ":" + (s < 10 ? "0" + s : s);
  }
  var players = [];
  document.querySelectorAll("[data-audio]").forEach(function (box) {
    var a = box.querySelector("audio");
    var btn = box.querySelector(".audio-btn");
    var range = box.querySelector(".audio-range");
    var time = box.querySelector(".audio-time");
    if (!a || !btn) return;
    var playIcon = btn.innerHTML;
    var pauseIcon = '<svg class="ico" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 5h4v14H7zM13 5h4v14h-4z" fill="currentColor"/></svg>';
    players.push(a);
    btn.addEventListener("click", function () {
      if (a.paused) {
        players.forEach(function (o) { if (o !== a) o.pause(); });
        a.play().then(function () { track("Audio Sample Play", { book: box.getAttribute("data-book") }); }).catch(function () {});
      } else {
        a.pause();
      }
    });
    a.addEventListener("play", function () { btn.innerHTML = pauseIcon; btn.setAttribute("aria-label", "Pause audio sample"); });
    a.addEventListener("pause", function () { btn.innerHTML = playIcon; btn.setAttribute("aria-label", "Play audio sample"); });
    a.addEventListener("loadedmetadata", function () { range.disabled = false; time.textContent = clock(a.duration); });
    a.addEventListener("timeupdate", function () {
      if (a.duration) range.value = String((a.currentTime / a.duration) * 100);
      time.textContent = clock(a.currentTime);
    });
    a.addEventListener("ended", function () { range.value = "0"; time.textContent = clock(a.duration); });
    range.addEventListener("input", function () { if (a.duration) a.currentTime = (parseFloat(range.value) / 100) * a.duration; });
    a.load();
  });

  /* ---------- quiz match on the home page ---------- */
  var matched = store("ac_quiz");
  if (matched) {
    document.querySelectorAll("[data-match-book]").forEach(function (a) {
      if (a.getAttribute("data-match-book") === matched) a.hidden = false;
    });
  }

  /* ---------- forms that open the reader's own email app (review copy, ARC, reactions) ---------- */
  document.querySelectorAll("form[data-mailto]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var lines = [];
      var book = "";
      Array.prototype.forEach.call(form.elements, function (el) {
        if (!el.name || el.type === "submit" || el.type === "hidden") return;
        if ((el.type === "checkbox" || el.type === "radio") && !el.checked) return;
        var v = (el.value || "").trim();
        if (!v) return;
        if (el.name === "book") book = v;
        var label = el.getAttribute("data-label") || el.name;
        lines.push(el.type === "checkbox" ? "- " + label : label + ": " + v);
      });
      var subject = (form.getAttribute("data-subject") || "Message from ashleyclaudy.com").replace("{book}", book);
      var body = "Hi Ashley,\n\n" + (form.getAttribute("data-intro") || "") + "\n\n" + lines.join("\n") + "\n\nThanks!";
      track("Email Form", { form: subject.split(":")[0] });
      var note = form.querySelector(".req-note");
      if (note) note.hidden = false;
      var href = "mailto:" + form.getAttribute("data-mailto") + "?subject=" + encodeURIComponent(subject) + "&body=" + encodeURIComponent(body);
      (window.__acMail || function (h) { window.location.href = h; })(href);
    });
  });

  /* ---------- share a link ---------- */
  document.querySelectorAll("[data-share-link]").forEach(function (b) {
    var label = b.textContent;
    b.addEventListener("click", function () {
      var url = b.getAttribute("data-share-link");
      var text = b.getAttribute("data-share-text") || "";
      track("Share", { url: url });
      if (navigator.share) {
        navigator.share({ title: document.title, text: text, url: url }).catch(function () {});
      } else if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(function () {
          b.textContent = "Link copied";
          setTimeout(function () { b.textContent = label; }, 1800);
        }, function () {});
      }
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
