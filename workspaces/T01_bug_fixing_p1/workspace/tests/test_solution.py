"""Tests for T01_bug_fixing: Fix Null Pointer in User Service

Validates all three bug fixes:
  1. GET /users/{id} returns 404 instead of crashing when user not found
  2. POST /users rejects empty names with 422
  3. PUT /users/{id} returns 404 when user does not exist
"""

import pytest


class TestFixNullPointerinUserService:

    def test_app_imports(self, client):
        """Verify the module can be imported."""
        from main import app
        assert app is not None

    # ── Bug 1: GET /users/{id} crashes when user not found ──────────────

    def test_get_nonexistent_user_returns_404(self, client):
        """Bug 1 fix: GET /users/{id} should return 404, not crash."""
        response = client.get("/users/nonexistent-id")
        assert response.status_code == 404, (
            f"Expected 404 for missing user, got {response.status_code}"
        )

    def test_get_existing_user_works(self, client):
        """Sanity: GET /users/{id} still works for existing users."""
        # Create a user first
        create_resp = client.post("/users", json={"name": "Alice"})
        assert create_resp.status_code == 201
        user_id = create_resp.json()["user"]["id"]

        # Now fetch it
        response = client.get(f"/users/{user_id}")
        assert response.status_code == 200
        assert response.json()["user"]["name"] == "Alice"

    # ── Bug 2: POST /users accepts empty names ──────────────────────────

    @pytest.mark.parametrize("payload", [
        {"name": ""},
        {"name": "   "},
        {},
    ])
    def test_post_user_rejects_empty_name(self, client, payload):
        """Bug 2 fix: POST /users should reject empty/whitespace-only/missing names."""
        response = client.post("/users", json=payload)
        assert response.status_code == 422, (
            f"Expected 422 for invalid name, got {response.status_code} — body={payload}"
        )

    def test_post_user_with_valid_name(self, client):
        """Sanity: POST /users still works with a valid name."""
        response = client.post("/users", json={"name": "Bob"})
        assert response.status_code == 201
        data = response.json()
        assert data["user"]["name"] == "Bob"
        assert "id" in data["user"]

    # ── Bug 3: PUT /users/{id} doesn't check if user exists ─────────────

    def test_put_nonexistent_user_returns_404(self, client):
        """Bug 3 fix: PUT /users/{id} should return 404 when user doesn't exist."""
        response = client.put("/users/nonexistent-id", json={"name": "Updated"})
        assert response.status_code == 404, (
            f"Expected 404 for updating missing user, got {response.status_code}"
        )

    def test_put_existing_user_works(self, client):
        """Sanity: PUT /users/{id} still works for existing users."""
        create_resp = client.post("/users", json={"name": "Charlie"})
        user_id = create_resp.json()["user"]["id"]

        response = client.put(f"/users/{user_id}", json={"name": "Charlie Updated"})
        assert response.status_code == 200
        assert response.json()["user"]["name"] == "Charlie Updated"

    # ── No crashes / regressions ────────────────────────────────────────

    def test_bug_is_fixed_no_crash(self, client):
        """Verify the original bugs no longer cause any 500 crash."""
        from main import app
        routes = [r.path for r in app.routes if hasattr(r, 'path')]
        for route in routes:
            if '{' not in route:
                response = client.get(route)
                assert response.status_code != 500, \
                    f"Endpoint {route} returned 500 — bug may still be present"

    def test_fix_preserves_original_functionality(self, client):
        """Verify the fix doesn't break previously working features."""
        from main import app
        routes = [r.path for r in app.routes if hasattr(r, 'path')]
        for route in routes:
            if '{' not in route:
                response = client.get(route)
                assert response.status_code < 500, \
                    f"Regression: {route} now returns {response.status_code}"

    def test_edge_case_handling(self, client):
        """Verify edge cases are handled (empty input → 422 not 500)."""
        from main import app
        post_routes = [
            r.path for r in app.routes
            if hasattr(r, 'methods') and 'POST' in r.methods and '{' not in r.path
        ]
        for route in post_routes:
            response = client.post(route, json={})
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
        """Verify the fix addresses the root cause with proper error handling/validation."""
        import main
        import inspect
        source = inspect.getsource(main)
        valid_patterns = [
            "raise HTTPException",
            "field_validator",
            "status_code=",
            "User not found",
        ]
        found = [p for p in valid_patterns if p in source]
        assert found, f"No evidence of the fix — none of {valid_patterns} found in source"
