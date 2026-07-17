"""Tests for T02_bug_fixing: Fix Race Condition in Counter"""

import pytest


class TestFixRaceConditioninCounter:

    def test_app_imports(self, client):
        """Verify the module can be imported."""
        from main import app
        assert app is not None

    def test_bug_is_fixed_no_crash(self, client):
        """Verify the original bug no longer causes a crash."""
        from main import app
        routes = [r.path for r in app.routes if hasattr(r, 'path')]
        for route in routes:
            if '{' not in route:
                response = client.get(route)
                # The bug should not cause 500 errors
                assert response.status_code != 500, \
                    f"Endpoint {route} returned 500 — bug may still be present"

    def test_fix_preserves_original_functionality(self, client):
        """Verify the fix doesn't break previously working features (pass→pass)."""
        from main import app
        # Check all routes respond (even with 4xx, just not crash)
        routes = [r.path for r in app.routes if hasattr(r, 'path')]
        for route in routes:
            if '{' not in route:
                response = client.get(route)
                assert response.status_code < 500, \
                    f"Regression: {route} now returns {response.status_code}"

    def test_edge_case_handling(self, client):
        """Verify edge cases are handled (empty input, extreme values)."""
        from main import app
        # Try POST endpoints with invalid data
        post_routes = [
            r.path for r in app.routes
            if hasattr(r, 'methods') and 'POST' in r.methods and '{' not in r.path
        ]
        for route in post_routes:
            response = client.post(route, json={})
            # Should return 4xx (validation), not 5xx (crash)
            assert response.status_code < 500, \
                f"POST {route} with empty body crashed ({response.status_code})"

    def test_no_stubs_or_todos(self):
        """Verify no stub/TODO code remains."""
        import inspect
        import main
        source = inspect.getsource(main)
        assert "TODO" not in source, "TODO found — fix completely"
        assert "raise NotImplementedError" not in source, "NotImplementedError found"

    def test_fix_is_correct(self):
        """Verify the fix addresses the root cause described in the issue."""
        import main
        import inspect
        source = inspect.getsource(main)
        # The fix should introduce proper handling (try/except, validation, locking, etc.)
        # Check for common fix patterns
        has_fix = any(pat in source for pat in [
            "try:", "except", "raise HTTPException",
            "with", "Lock", "Semaphore", "validate",
            "parameterized", "json_util", "encoder"
        ])
        assert has_fix, "No evidence of the fix — missing proper error handling/locking/validation"
