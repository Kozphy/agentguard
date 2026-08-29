from pathlib import Path

import pytest

from agentguard.repair_loop import RepairLoopError, _extract_diff, _validate_patch


def test_extract_diff_from_fenced_response() -> None:
    response = """Here is the change:\n```diff\ndiff --git a/src/app.py b/src/app.py\n--- a/src/app.py\n+++ b/src/app.py\n@@ -1 +1 @@\n-old\n+new\n```\n"""

    patch = _extract_diff(response)

    assert patch.startswith("diff --git a/src/app.py b/src/app.py")
    assert "+new" in patch


def test_validate_patch_rejects_file_outside_allowlist() -> None:
    patch = """diff --git a/src/app.py b/src/app.py\n--- a/src/app.py\n+++ b/src/app.py\n@@ -1 +1 @@\n-old\n+new\n"""

    with pytest.raises(RepairLoopError, match="outside the allowlist"):
        _validate_patch(patch, {Path("src/other.py")})


def test_validate_patch_rejects_new_files() -> None:
    patch = """diff --git a/new.py b/new.py\nnew file mode 100644\n--- /dev/null\n+++ b/new.py\n@@ -0,0 +1 @@\n+print('new')\n"""

    with pytest.raises(RepairLoopError, match="Creating new files"):
        _validate_patch(patch, {Path("new.py")})


def test_validate_patch_accepts_allowlisted_existing_file() -> None:
    patch = """diff --git a/src/app.py b/src/app.py\n--- a/src/app.py\n+++ b/src/app.py\n@@ -1 +1 @@\n-old\n+new\n"""

    _validate_patch(patch, {Path("src/app.py")})
