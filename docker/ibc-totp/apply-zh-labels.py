#!/usr/bin/env python3
"""Post-process IBC sources after ibc-patch-totp: zh-CN Gateway labels and buttons.

Java sources must stay US-ASCII (IBC ant build); use \\u escapes for Chinese strings.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

JAVA = Path("src/ibcalpha/ibc/SecondFactorAuthenticationDialogHandler.java")

# zh-CN UI strings as Java unicode escapes (ASCII-safe source file)
_ZH_LABEL_APP = "\\u79fb\\u52a8\\u9a8c\\u8bc1\\u5e94\\u7528\\u7a0b\\u5e8f"
_ZH_LABEL_APP_CODE = "\\u79fb\\u52a8\\u9a8c\\u8bc1\\u5e94\\u7528\\u7a0b\\u5e8f\\u4ee3\\u7801"
_ZH_BTN_OK = "\\u786e\\u5b9a"
_ZH_BTN_ACTIVATE = "\\u6fc0\\u6d3b"

_TOTP_RETURN_RE = re.compile(
    r"(return\s+SwingUtils\.findLabel\(window,\s*\"Enter Mobile Authenticator\"\)\s*!=\s*null\s*\|\|\s*"
    r"\n\s*SwingUtils\.findLabel\(window,\s*\"Authenticator app code\"\)\s*!=\s*null)\s*;",
    re.MULTILINE,
)

_OK_BUTTON_RE = re.compile(
    r"(\s*)Utils\.logToConsole\(\"Clicked OK button\"\);\s*"
    r"\n\s*\}\s*else\s*\{\s*"
    r"\n\s*Utils\.logError\(\"Could not click OK button\"\);\s*"
    r"\n\s*\}",
    re.MULTILINE,
)


def _patch_ok_button(text: str) -> str:
    m = _OK_BUTTON_RE.search(text)
    if not m:
        raise ValueError("OK button anchor not found")
    lead, inner = m.group(1), m.group(1) + "    "
    block = (
        f'{lead}Utils.logToConsole("Clicked OK button");\n'
        + f"{lead}"
        + "} else if (SwingUtils.clickButton(window, \""
        + _ZH_BTN_OK
        + "\")) {\n"
        + f'{inner}Utils.logToConsole("Clicked OK button (zh)");\n'
        + f"{lead}"
        + "} else if (SwingUtils.clickButton(window, \""
        + _ZH_BTN_ACTIVATE
        + "\")) {\n"
        + f'{inner}Utils.logToConsole("Clicked activate button (zh)");\n'
        + f"{lead}"
        + "} else {\n"
        + f'{inner}Utils.logError("Could not click OK button");\n'
        + f"{lead}"
        + "}"
    )
    return text[: m.start()] + block + text[m.end() :]


def main() -> int:
    path = JAVA
    if not path.is_file():
        print(f"apply-zh-labels: missing {path}", file=sys.stderr)
        return 1

    text = path.read_text(encoding="utf-8")
    if _ZH_LABEL_APP in text:
        print("apply-zh-labels: zh labels already present")
        return 0

    if not _TOTP_RETURN_RE.search(text):
        print("apply-zh-labels: TOTP prompt anchor not found", file=sys.stderr)
        return 1

    text = _TOTP_RETURN_RE.sub(
        lambda m: (
            m.group(1)
            + ' ||\n               SwingUtils.findLabel(window, "Mobile Authenticator app code") != null'
            + f' ||\n               SwingUtils.findLabel(window, "{_ZH_LABEL_APP}") != null'
            + f' ||\n               SwingUtils.findLabel(window, "{_ZH_LABEL_APP_CODE}") != null;'
        ),
        text,
        count=1,
    )

    try:
        text = _patch_ok_button(text)
    except ValueError:
        print("apply-zh-labels: OK button anchor not found", file=sys.stderr)
        return 1

    path.write_text(text, encoding="ascii", errors="strict", newline="\n")
    print("apply-zh-labels: done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
