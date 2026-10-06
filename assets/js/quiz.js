(function () {
  "use strict";

  var root = document.querySelector(".quiz");
  var dataEl = document.getElementById("quiz-data");
  if (!root || !dataEl) return;

  var data = JSON.parse(dataEl.textContent);
  var total = data.questions.length;
  var views = {};
  root.querySelectorAll("[data-view]").forEach(function (el) { views[el.getAttribute("data-view")] = el; });
  var stepEl = root.querySelector("[data-step]");
  var barEl = root.querySelector("[data-bar]");
  var qEl = root.querySelector("[data-q]");
  var optsEl = root.querySelector("[data-opts]");
  var panels = root.querySelectorAll("[data-result]");
  var step = 0;
  var answers = [];
  var locked = false;

  function track(name, props) {
    try {
      if (window.plausible) window.plausible(name, { props: props });
      if (window.gtag) window.gtag("event", name, props);
      if (window.fbq) window.fbq("trackCustom", name, props);
    } catch (e) {}
  }

  function show(name) {
    Object.keys(views).forEach(function (k) { views[k].hidden = k !== name; });
    window.scrollTo(0, 0);
  }

  function renderQuestion() {
    var q = data.questions[step];
    stepEl.textContent = (step + 1) + " of " + total;
    barEl.style.width = (step / total) * 100 + "%";
    qEl.textContent = q.q;
    optsEl.innerHTML = "";
    q.options.forEach(function (o, i) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "opt" + (answers[step] === i ? " picked" : "");
      b.style.setProperty("--d", i * 0.06 + "s");
      var letter = document.createElement("i");
      letter.textContent = String.fromCharCode(65 + i);
      var label = document.createElement("span");
      label.textContent = o.text;
      b.appendChild(letter);
      b.appendChild(label);
      b.addEventListener("click", function () { pick(i, b); });
      optsEl.appendChild(b);
    });
    qEl.focus({ preventScroll: true });
  }

  function pick(i, b) {
    if (locked) return;
    locked = true;
    answers[step] = i;
    b.classList.add("picked");
    setTimeout(function () {
      locked = false;
      if (step + 1 < total) {
        step += 1;
        renderQuestion();
      } else {
        finish();
      }
    }, 300);
  }

  function winner() {
    var sc = {};
    data.order.forEach(function (k) { sc[k] = 0; });
    answers.forEach(function (a, qi) {
      var s = data.questions[qi].options[a].scores;
      Object.keys(s).forEach(function (k) { sc[k] = (sc[k] || 0) + s[k]; });
    });
    var best = data.order[0];
    data.order.forEach(function (k) { if (sc[k] > sc[best]) best = k; });
    return best;
  }

  function showResult(slug) {
    var found = false;
    panels.forEach(function (p) {
      var on = p.getAttribute("data-result") === slug;
      p.hidden = !on;
      if (on) found = true;
    });
    if (!found) return false;
    var title = root.querySelector('[data-result="' + slug + '"]').getAttribute("data-title");
    var head = root.querySelector(".quiz-join .crew h2");
    if (head && title) {
      head.textContent = "Your match is " + title + ". ";
      var em = document.createElement("span");
      em.className = "serif";
      em.textContent = "Get the bonus chapters free.";
      head.appendChild(em);
    }
    show("result");
    try { history.replaceState(null, "", "#" + slug); } catch (e) {}
    return true;
  }

  function finish() {
    var slug = winner();
    barEl.style.width = "100%";
    track("Quiz Completed", { result: slug });
    try { localStorage.setItem("ac_quiz", slug); } catch (e) {}
    showResult(slug);
  }

  root.querySelector("[data-start]").addEventListener("click", function () {
    step = 0;
    answers = [];
    show("question");
    renderQuestion();
    track("Quiz Started", {});
  });

  root.querySelector("[data-back]").addEventListener("click", function () {
    if (step > 0) {
      step -= 1;
      renderQuestion();
    } else {
      show("intro");
    }
  });

  root.querySelectorAll("[data-retake]").forEach(function (b) {
    b.addEventListener("click", function () {
      try { history.replaceState(null, "", location.pathname + location.search); } catch (e) {}
      show("intro");
    });
  });

  root.querySelectorAll("[data-share]").forEach(function (b) {
    var label = b.textContent;
    b.addEventListener("click", function () {
      var slug = b.getAttribute("data-share");
      var url = location.href.split("#")[0] + "#" + slug;
      var text = "I took Ashley Claudy's quiz. Which kind of trouble are you?";
      track("Quiz Share", { result: slug });
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

  function fromHash() {
    var hash = location.hash.replace("#", "");
    if (hash) showResult(hash);
  }
  window.addEventListener("hashchange", fromHash);
  fromHash();
})();
