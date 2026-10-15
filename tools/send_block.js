// ---------- SEND LEVEL 3 ANSWERS (v2) ----------
// On GitHub Pages: sends directly to Web3Forms and only says "Sent!" once Web3Forms confirms.
// Inside a Claude link (artifact): opens the studio's send page on GitHub Pages, which does the
// same confirmed send. A "Copy my answers" backup is always shown.
var SEND_PAGE = "https://encinitaspiano.github.io/Lessons/send.html";
var blankWarned = false;

function buildAnswerText() {
  var answers = WRITTEN.map(function (q, i) { var t = el("w" + i); return t ? t.value.trim() : ""; });
  var text = "Student: " + STUDENT + "\nLesson: " + LESSON_LABEL + "\n\n";
  WRITTEN.forEach(function (q, i) {
    text += (i + 1) + ". " + q + "\n" + (answers[i] || "(no answer)") + "\n\n";
  });
  return {answers: answers, text: text};
}

function b64url(str) {
  var b = btoa(unescape(encodeURIComponent(str)));
  return b.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function copyBackup(text, intro) {
  el("sendMsg").innerHTML += '<p class="hint" style="margin-top:14px">' + intro + '</p>' +
    '<button class="btn alt" id="copyBtn" type="button">Copy my answers</button>' +
    '<div class="preview" id="answerPreview">' + esc(text) + '</div>';
  el("copyBtn").onclick = function () {
    var btn = this;
    function selectIt() {
      var r = document.createRange(); r.selectNodeContents(el("answerPreview"));
      var s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
      btn.textContent = "Selected - now tap Copy";
    }
    try {
      navigator.clipboard.writeText(text).then(function () { btn.textContent = "Copied! Now paste it in a text to Mr. Rod"; }, selectIt);
    } catch (err) { selectIt(); }
  };
}

el("sendBtn").onclick = function (ev) {
  var built = buildAnswerText();
  var blanks = [];
  built.answers.forEach(function (a, i) { if (!a) blanks.push(i + 1); });
  if (blanks.length && !blankWarned) {
    ev.preventDefault();
    blankWarned = true;
    el("sendMsg").innerHTML = '<div class="fb no">Question' + (blanks.length > 1 ? "s " : " ") + blanks.join(", ") +
      ' ' + (blanks.length > 1 ? "are" : "is") + ' still empty. Fill ' + (blanks.length > 1 ? "them" : "it") +
      ' in, or tap the send button again to send anyway.</div>';
    return;
  }
  var text = built.text;
  var payload = {
    s: STUDENT, d: LESSON_DATE, l: LESSON_LABEL, m: text
  };

  if (!WEB3FORMS_KEY) {
    ev.preventDefault();
    el("sendMsg").innerHTML = '<div class="note"><b>SAMPLE MODE:</b> in the real version, this is emailed to Mr. Rod. Here is exactly what he would receive:</div>' +
      '<div class="preview">' + esc(text) + '</div>';
    return;
  }

  var onGithub = /github\.io$/.test(location.hostname);
  if (onGithub) {
    ev.preventDefault();
    var btn = this;
    btn.style.pointerEvents = "none"; btn.style.opacity = ".5"; btn.textContent = "Sending...";
    el("sendMsg").innerHTML = "";
    fetch("https://api.web3forms.com/submit", {
      method: "POST",
      headers: {"Content-Type": "application/json", "Accept": "application/json"},
      body: JSON.stringify({
        access_key: WEB3FORMS_KEY,
        subject: "Level 3 answers - " + STUDENT + " - " + LESSON_DATE,
        from_name: STUDENT + " (Lesson Challenge)",
        student: STUDENT, lesson: LESSON_LABEL, message: text
      })
    }).then(function (r) { return r.json(); }).then(function (j) {
      if (!j || !j.success) throw new Error((j && j.message) || "not accepted");
      btn.textContent = "Sent!";
      el("sendMsg").innerHTML = '<div class="unlock"><div class="big">Sent!</div><p>Mr. Rod has your answers, ' + esc(STUDENT) +
        '. We will go over them together at your next lesson. Great work, and trust yourself!</p></div>';
    }).catch(function () {
      btn.style.pointerEvents = ""; btn.style.opacity = ""; btn.textContent = "Try sending again";
      el("sendMsg").innerHTML = '<div class="fb no">Hmm, that did not go through. Check your internet and try again.</div>';
      copyBackup(text, "<b>Still not working?</b> Copy your answers and text them to Mr. Rod.");
    });
    return;
  }

  // Inside a Claude link: let this tap open the send page in a new tab (no pop-up needed).
  this.href = SEND_PAGE + "#" + b64url(JSON.stringify(payload));
  el("sendMsg").innerHTML = '<div class="unlock"><div class="big">Almost done!</div><p>A new page just opened to send your answers. ' +
    'When it says <b>Sent!</b>, you are all done. Great work, ' + esc(STUDENT) + '!</p></div>';
  copyBackup(text, "<b>No new page, or it did not say Sent?</b> Copy your answers and text them to Mr. Rod.");
};
</script>
