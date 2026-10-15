#!/usr/bin/env python3
"""Upgrade a Lesson Challenge page (or the template) to the v2 Level 3 send:
new studio-Gmail Web3Forms key, confirmed sending, and a copy-answers backup.

Usage: python3 tools/patch_send.py page.html [more.html ...]   (edits in place)
"""
import os, re, sys

KEY = "c0cd7e3f-d017-4281-b2e9-ece3a27592d6"
HERE = os.path.dirname(os.path.abspath(__file__))
BLOCK = open(os.path.join(HERE, "send_block.js")).read()
ANCHOR = ('<a class="btn" id="sendBtn" href="#" target="_blank" rel="noopener" '
          'style="text-align:center;text-decoration:none">Click here to send my answers</a>')


def patch(s):
    s, n = re.subn(r'var WEB3FORMS_KEY = "[^"]*";', 'var WEB3FORMS_KEY = "%s";' % KEY, s)
    assert n == 1, "key line"
    if 'id="sendBtn" href=' not in s:
        s, n = re.subn(r'<button class="btn" id="sendBtn">[^<]*</button>', ANCHOR, s)
        assert n == 1, "send button"
    hdr = s.find("// ---------- SEND LEVEL 3 ANSWERS")
    start = hdr if hdr != -1 else s.index('el("sendBtn").onclick')
    end = s.index("</script>", start) + len("</script>")
    return s[:start] + BLOCK.rstrip("\n") + s[end:]


if __name__ == "__main__":
    for f in sys.argv[1:]:
        src = open(f).read()
        out = patch(src)
        open(f, "w").write(out)
        print("patched", f)
