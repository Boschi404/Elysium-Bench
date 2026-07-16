"""Tests for T03_api_development: Create Task/TODO API"""

import pytest


class TestCreateTask_TODOAPI:

    def test_app_imports(self, client):
        """Verify the FastAPI app can be imported and has routes."""
        from main import app
        assert app is not None
        routes = [r.path for r in app.routes if hasattr(r, 'path')]
        assert len(routes) > 0, "No routes registered in the app"

    def test_endpoint_returns_valid_json(self, client):
        """Verify endpoints return valid JSON responses."""
        # Try the most basic endpoint — adjust based on task
        routes = [r.path for r in client.app.routes if hasattr(r, 'path') and '{' not in r.path]
        if routes:
            response = client.get(routes[0])
            assert response.status_code in (200, 201, 404, 405), \
                f"Unexpected status: {response.status_code}"

    def test_input_validation_present(self, client):
        """Verify the app has input validation (Pydantic models or manual checks)."""
        from main import app
        # Check for Pydantic models in the module
        import main
        has_models = any(
            hasattr(getattr(main, name, None), '__fields__') or
            hasattr(getattr(main, name, None), 'model_fields')
            for name in dir(main)
        )
        assert has_models, "No Pydantic models found — input validation is required"

    def test_error_handling(self, client):
        """Verify the app returns proper error responses, not 500 crashes."""
        # Try a non-existent endpoint
        response = client.get("/nonexistent_endpoint_12345")
        assert response.status_code != 500, \
            "App crashed on unknown endpoint — expected 404, got 500"

    def test_content_type_json(self, client):
        """Verify responses have Content-Type: application/json."""
        routes = [r.path for r in client.app.routes if hasattr(r, 'path') and '{' not in r.path]
        if routes:
            response = client.get(routes[0])
            if response.status_code < 500:
                ct = response.headers.get("content-type", "")
                assert "application/json" in ct, \
                    f"Expected JSON response, got: {ct}"

    def test_no_stubs_or_todos(self):
        """Verify no stub/TODO code in main.py."""
        import inspect
        import main

        source = inspect.getsource(main)
        assert "TODO" not in source, "Main module contains TODO — implement fully"
        assert "raise NotImplementedError" not in source, \
            "Main module contains NotImplementedError — implement fully"

    def test_type_hints_present(self):
        """Verify functions have type hints."""
        import inspect
        import main

        functions = inspect.getmembers(main, inspect.isfunction)
        if functions:
            for name, fn in functions:
                if name.startswith('_'):
                    continue
                hints = inspect.signature(fn)
                has_return = hints.return_annotation is not inspect.Parameter.empty
                has_params = all(
                    p.annotation is not inspect.Parameter.empty
                    for p in hints.parameters.values()
                    if p.name != 'self'
                )
                # At least one function should have type hints
                if has_return or has_params:
                    break
            else:
                if functions:
                    pytest.fail("No functions have type hints — required for code quality")
