#!/usr/bin/env python3
"""Add auto-save (resume where you left off) to a Lesson Challenge page.

Usage: python3 tools/add_autosave.py page.html [more.html ...]   (edits in place)

Works on tools/template.html and on any page built from the Oct 4, 2026
3-level layout. Safe to run twice: pages that already have auto-save are skipped.
Progress is saved in the student's own browser (localStorage), keyed by
student + lesson date, so each page keeps its own progress.
"""
import pathlib, sys

MARK = "rcps-challenge:"

CSS = """.linkbtn { font: inherit; font-size: 15px; background: none; border: none; color: var(--head); text-decoration: underline; cursor: pointer; padding: 6px; }
footer { text-align"""

WELCOME = """<div class="note hidden" id="welcomeBack"><b>Welcome back!</b> Your progress was saved, so you can pick up right where you left off.</div>

<!-- LEVEL 1: SUMMARY -->"""

L3_HINT = """<p class="hint">Your answers save automatically on this device as you type, so you can stop and come back later.</p>
    <div id="wqs"></div>"""

START_OVER = """<p style="text-align:center;margin:0 0 10px"><button class="linkbtn" id="startOver">Start over from the beginning</button></p>
<footer>"""

JS_START = "var round = 0, answered = 0, correct = 0, missed = [], missedIdx = [], order = [];"
JS_END = 'el("sendBtn").onclick'

JS = r"""var round = 0, answered = 0, correct = 0, missed = [], missedIdx = [], order = [], optOrder = [], picks = {};

// ---------- AUTO-SAVE: progress is kept in this browser so students can come back later ----------
var SAVE_KEY = "rcps-challenge:" + STUDENT + ":" + LESSON_DATE;
var S = {stage: 1, round: 0, order: [], optOrder: [], picks: {}, next: null, stamp: "", l3: false, written: []};
var restoring = false, restoreNext = null;

function save() {
  if (restoring) return;
  S.round = round; S.order = order; S.optOrder = optOrder; S.picks = picks;
  try { localStorage.setItem(SAVE_KEY, JSON.stringify(S)); } catch (err) {}
}
function loadSaved() {
  try { var raw = localStorage.getItem(SAVE_KEY); return raw ? JSON.parse(raw) : null; } catch (err) { return null; }
}
function clearSaved() {
  try { localStorage.removeItem(SAVE_KEY); } catch (err) {}
}
// ---------------------------------------------------------------------------------------------

function showL2() {
  el("level2").classList.remove("hidden");
  el("lv1").className = "lv done";
  el("lv2").className = "lv on";
  el("startL2").style.display = "none";
}

el("startL2").onclick = function () {
  showL2();
  S.stage = 2;
  startRound(QUESTIONS.map(function (_, i) { return i; }));
  el("level2").scrollIntoView({behavior: "smooth"});
};

function startRound(list, savedOpts) {
  round++; answered = 0; correct = 0; missed = []; missedIdx = []; picks = {};
  S.next = null;
  order = savedOpts ? list.slice() : shuffle(list);
  optOrder = [];
  var html = "";
  order.forEach(function (qi, n) {
    var Q = QUESTIONS[qi];
    var perm = savedOpts ? savedOpts[n] : shuffle(Q.o.map(function (_, i) { return i; }));
    optOrder.push(perm);
    html += '<div class="q" id="q' + n + '"><p class="qtext"><span class="qnum">' + (n + 1) + '.</span> ' + esc(Q.q) + '</p>';
    perm.forEach(function (oi, k) {
      html += '<div class="opt" data-k="' + k + '" data-ok="' + (oi === Q.a ? 1 : 0) + '"><button class="letter" data-n="' + n + '" aria-label="Choose ' + "ABCD"[k] + '">' + "ABCD"[k] + '</button><span class="otext">' + esc(Q.o[oi]) + '</span></div>';
    });
    html += '<div class="fbwrap"></div></div>';
  });
  el("qs").innerHTML = html;
  el("result").innerHTML = "";
  updateProgress();
  var btns = document.querySelectorAll("#qs .letter");
  for (var i = 0; i < btns.length; i++) btns[i].onclick = function () { pick.call(this.parentNode, +this.getAttribute("data-n")); };
  save();
}

function pick(n) {
  var box = el("q" + n);
  var Q = QUESTIONS[order[n]];
  var ok = this.getAttribute("data-ok") === "1";
  picks[n] = +this.getAttribute("data-k");
  var all = box.querySelectorAll(".opt");
  for (var i = 0; i < all.length; i++) {
    all[i].querySelector(".letter").disabled = true;
    if (all[i].getAttribute("data-ok") === "1") {
      all[i].classList.add("right");
      var t1 = all[i].querySelector(".otext"); t1.innerHTML = '<span class="tag">CORRECT &gt;</span>' + t1.innerHTML;
    }
  }
  if (!ok) {
    this.classList.add("wrong");
    var t2 = this.querySelector(".otext"); t2.innerHTML = '<span class="tag">YOUR ANSWER &gt;</span>' + t2.innerHTML;
    missed.push(n + 1);
    box.classList.add("miss");
    missedIdx.push(order[n]);
  } else {
    correct++;
    box.classList.add("got");
  }
  answered++;
  box.querySelector(".fbwrap").innerHTML =
    '<div class="fb' + (ok ? '' : ' no') + '"><p class="verdict">' + (ok ? 'You got it!' : 'Missed. The right answer is marked CORRECT.') + '</p>' + esc(Q.e) + '</div>';
  updateProgress();
  save();
  if (answered === order.length) finishRound();
}

function updateProgress() {
  el("progress").textContent = "Round " + round + ": " + answered + " of " + order.length + " answered, " + correct + " correct";
}

function nextList() {
  var all = QUESTIONS.map(function (_, i) { return i; });
  if (missedIdx.length >= 3) return {list: all, msg: "You missed " + missedIdx.length + ", so next round is the <b>whole quiz</b> again."};
  var extra = missedIdx.length === 1 ? 2 : 4;
  var known = shuffle(all.filter(function (i) { return missedIdx.indexOf(i) < 0; })).slice(0, extra);
  var n = missedIdx.length + extra;
  return {list: missedIdx.concat(known), msg: "You missed " + missedIdx.length + ", so next round is <b>" + n + " questions</b>: the " + (missedIdx.length === 1 ? "one" : "two") + " you missed plus " + extra + " you already knew."};
}

function finishRound() {
  var total = order.length;
  if (correct === total) {
    unlock();
    return;
  }
  var nx = (restoring && restoreNext) ? restoreNext : nextList();
  S.next = nx;
  save();
  el("result").innerHTML =
    '<div class="note"><p class="score">Score: ' + correct + ' / ' + total + '</p>' +
    '<p><b>Missed:</b></p><ul class="misslist">' + missed.map(function (m) { return '<li>' + m + '. ' + esc(QUESTIONS[order[m - 1]].q) + '</li>'; }).join("") + '</ul>' +
    '<p>' + nx.msg + ' Read the reminders above first. The order will be mixed up, so you have to really know it. Get them all right to unlock Level 3.</p></div>' +
    '<button class="btn" id="retry">Start next round</button>';
  el("retry").onclick = function () { startRound(nx.list); el("level2").scrollIntoView({behavior: "smooth"}); };
}

function unlock() {
  var stamp = S.stamp;
  if (!stamp) {
    var now = new Date();
    stamp = now.toLocaleDateString(undefined, {weekday: "short", month: "short", day: "numeric"}) + " at " +
            now.toLocaleTimeString(undefined, {hour: "numeric", minute: "2-digit"});
  }
  S.stamp = stamp;
  S.stage = 3;
  save();
  el("result").innerHTML =
    '<div class="unlock"><div class="big">100%!<br>LEVEL 3 UNLOCKED</div>' +
    '<p style="font-size:19px;margin:10px 0 4px"><b>' + esc(STUDENT) + '</b>, lesson of ' + esc(LESSON_LABEL) + '</p>' +
    '<div class="stamp">Unlocked ' + esc(stamp) + ' (round ' + round + ')</div>' +
    '<p style="margin-top:12px"><b>Take a screenshot of this box and text it to Mr. Rod.</b></p></div>' +
    '<button class="btn" id="goL3">Start Level 3</button>';
  el("lv2").className = "lv done";
  el("lv3").className = "lv on";
  el("goL3").onclick = openL3;
  if (!restoring) el("result").scrollIntoView({behavior: "smooth"});
}

function openL3() {
  el("lockedBox").style.display = "none";
  el("l3body").classList.remove("hidden");
  S.l3 = true;
  if (!S.written) S.written = [];
  var html = "";
  WRITTEN.forEach(function (q, i) {
    html += '<label class="wq" for="w' + i + '">' + (i + 1) + '. ' + esc(q) + '</label>' +
            '<textarea id="w' + i + '" data-i="' + i + '" placeholder="Type or speak your answer here..."></textarea>';
  });
  el("wqs").innerHTML = html;
  WRITTEN.forEach(function (q, i) {
    var ta = el("w" + i);
    ta.value = S.written[i] || "";
    ta.oninput = function () { S.written[+this.getAttribute("data-i")] = this.value; save(); };
  });
  save();
  if (!restoring) el("level3").scrollIntoView({behavior: "smooth"});
}

el("startOver").onclick = function () {
  if (!confirm("This clears your quiz answers and anything you typed in Level 3 on this device. Start over from the beginning?")) return;
  clearSaved();
  window.scrollTo(0, 0);
  location.reload();
};

(function restoreProgress() {
  var saved = loadSaved();
  if (!saved || !(saved.stage >= 2)) return;
  restoring = true;
  try {
    S = saved;
    S.written = S.written || [];
    restoreNext = saved.next || null;
    showL2();
    var ok = saved.order && saved.order.length && saved.optOrder && saved.optOrder.length === saved.order.length &&
      saved.order.every(function (qi, n) {
        return QUESTIONS[qi] && saved.optOrder[n].length === QUESTIONS[qi].o.length;
      });
    if (ok) {
      round = (saved.round || 1) - 1;
      startRound(saved.order, saved.optOrder);
      Object.keys(saved.picks || {}).map(Number).sort(function (a, b) { return a - b; }).forEach(function (n) {
        var box = el("q" + n); if (!box) return;
        var opt = box.querySelectorAll(".opt")[saved.picks[n]];
        if (opt && !opt.querySelector(".letter").disabled) pick.call(opt, n);
      });
    } else {
      round = 0;
      startRound(QUESTIONS.map(function (_, i) { return i; }));
    }
    if (saved.l3 && S.stage === 3) openL3();
    el("welcomeBack").classList.remove("hidden");
  } catch (err) {
    restoring = false;
    clearSaved();
    location.reload();
    return;
  }
  restoring = false;
  save();
})();

"""


def patch(text):
    if MARK in text:
        return None
    a = text.index(JS_START)
    b = text.index(JS_END)
    text = text[:a] + JS + text[b:]
    for old, new in [("footer { text-align", CSS),
                      ("<!-- LEVEL 1: SUMMARY -->", WELCOME),
                      ('<div id="wqs"></div>', L3_HINT),
                      ("<footer>", START_OVER)]:
        assert text.count(old) == 1, old
        text = text.replace(old, new)
    text.encode("ascii")
    return text


if __name__ == "__main__":
    for p in sys.argv[1:]:
        path = pathlib.Path(p)
        out = patch(path.read_text())
        if out is None:
            print("already has auto-save:", p)
        else:
            path.write_text(out)
            print("patched:", p)
