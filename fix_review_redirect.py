from pathlib import Path

p = Path("docs/review.html")

s = p.read_text(encoding="utf-8")

old = """
    const params = new URLSearchParams(window.location.search);
    const returnApp =
      params.get("returnApp") ||
      sessionStorage.getItem("DJUNGO_APP_SLUG");

    if (returnApp) {
      window.location.href =
        `index.html?app=${encodeURIComponent(returnApp)}&_=${Date.now()}`;
    } else {
      window.location.href = "app_ready.html";
    }
"""

new = """
    const params = new URLSearchParams(window.location.search);
    const returnApp = params.get("returnApp");
    const finalSessionId = data.session_id || sessionId;

    if (returnApp) {
      window.location.href =
        `index.html?app=${encodeURIComponent(returnApp)}&_=${Date.now()}`;
    } else {
      window.location.href =
        `app_ready.html?session_id=${encodeURIComponent(finalSessionId)}`;
    }
"""

if old not in s:
    print("BLOCK NOT FOUND")
    raise SystemExit(1)

s = s.replace(old, new, 1)

p.write_text(s, encoding="utf-8")

print("PATCH APPLIED")