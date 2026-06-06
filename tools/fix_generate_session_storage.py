from pathlib import Path
import shutil

TARGET = Path("docs/generate.html")

FUNC = r'''
function replaceActiveSession(data) {
  const sessionId = data.session_id || "";
  const builderState = data.builder_state || null;

  if (!sessionId || !builderState) {
    throw new Error("Parser response missing session_id or builder_state");
  }

  localStorage.removeItem("DJUNGO_SESSION_ID");
  sessionStorage.removeItem("DJUNGO_SESSION_ID");
  localStorage.removeItem("DJUNGO_BUILDER_STATE");

  localStorage.setItem("DJUNGO_SESSION_ID", sessionId);
  sessionStorage.setItem("DJUNGO_SESSION_ID", sessionId);
  localStorage.setItem("DJUNGO_BUILDER_STATE", JSON.stringify(builderState));

  const project = builderState.project || {};

  if (project.sheetName) {
    sessionStorage.setItem("DJUNGO_SHEET_NAME", project.sheetName);
  }

  if (project.projectSlug) {
    sessionStorage.setItem("DJUNGO_APP_SLUG", project.projectSlug);
    localStorage.setItem("DJUNGO_LAST_APP", project.projectSlug);
  }
}
'''

def main():
    if not TARGET.exists():
        raise SystemExit(f"Missing file: {TARGET}")

    shutil.copy2(TARGET, TARGET.with_suffix(".html.bak"))

    text = TARGET.read_text(encoding="utf-8")

    if "function replaceActiveSession(data)" not in text:
        marker = '  parserBtn.addEventListener("click", async () => {'
        text = text.replace(marker, FUNC + "\n\n" + marker)

    text = text.replace(
        '''      localStorage.setItem("DJUNGO_SESSION_ID", currentSessionId);
      localStorage.setItem("DJUNGO_BUILDER_STATE", JSON.stringify(currentBuilderState));''',
        '''      replaceActiveSession(data);'''
    )

    text = text.replace(
        '''    localStorage.setItem("DJUNGO_SESSION_ID", currentSessionId || "");
    localStorage.setItem("DJUNGO_BUILDER_STATE", JSON.stringify(currentBuilderState));''',
        '''    replaceActiveSession({
      session_id: currentSessionId,
      builder_state: currentBuilderState
    });'''
    )

    TARGET.write_text(text, encoding="utf-8")
    print("OK patched", TARGET)

if __name__ == "__main__":
    main()