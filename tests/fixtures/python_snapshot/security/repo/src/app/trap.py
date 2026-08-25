from pathlib import Path

Path("TARGET_CODE_EXECUTED").write_text("unsafe")
raise RuntimeError("target code must not execute")

SECRET = "do-not-publish"


class SafeShape:
    pass
