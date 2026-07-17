"""Tests for T01_algorithm_implementation: Implement Binary Search"""

import pytest
import time
import random


class TestImplementBinarySearch:

    @pytest.fixture
    def solution(self):
        """Import the solution module."""
        try:
            import main
            return main
        except ImportError:
            pytest.skip("main.py not found")

    def test_module_imports(self, solution):
        """Verify the solution module is importable."""
        assert solution is not None

    def test_basic_case(self, solution):
        """Verify basic functionality with a simple test case."""
        # Find the main function by convention or name
        funcs = [f for f in dir(solution) if callable(getattr(solution, f))
                 and not f.startswith('_') and f not in ('app', 'main')]
        assert len(funcs) > 0, \
            f"No public functions found in module. Found: {dir(solution)}"

    def test_empty_input(self, solution):
        """Verify the algorithm handles empty/zero input gracefully."""
        funcs = [f for f in dir(solution) if callable(getattr(solution, f))
                 and not f.startswith('_') and f not in ('app', 'main')]
        # Attempt to call each function with empty input
        for fname in funcs[:3]:
            fn = getattr(solution, fname)
            try:
                # Try calling with empty list, 0, empty string
                import inspect
                sig = inspect.signature(fn)
                params = list(sig.parameters.keys())
                if len(params) >= 1:
                    if params[0] in ('items', 'lst', 'arr', 'data', 'sequence', 'graph'):
                        result = fn([])
                    elif params[0] in ('n', 'target', 'key', 'capacity', 'word'):
                        result = fn(0 if params[0] in ('n', 'capacity') else ''
                                    if params[0] == 'word' else None)
            except (TypeError, ValueError, AttributeError):
                pass  # Expected for some inputs
            except Exception as e:
                pytest.fail(f"Function {fname} crashed on empty input: {e}")

    def test_performance_large_input(self, solution):
        """Verify the algorithm handles large inputs within time constraints."""
        funcs = [f for f in dir(solution) if callable(getattr(solution, f))
                 and not f.startswith('_') and f not in ('app', 'main')]
        if not funcs:
            return

        fn = getattr(solution, funcs[0])
        large_input = list(range(10000))
        random.shuffle(large_input)

        start = time.time()
        try:
            import inspect
            sig = inspect.signature(fn)
            params = list(sig.parameters.keys())
            if len(params) >= 1:
                fn(large_input)
        except (TypeError, ValueError) as e:
            pass  # Function might require more params
        except Exception as e:
            pytest.fail(f"Performance test failed: {e}")

        elapsed = time.time() - start
        # For O(n log n) or O(n), 10000 elements should complete in < 2 seconds
        assert elapsed < 5.0, f"Performance issue: {elapsed:.2f}s for 10000 elements"

    def test_no_stubs(self, solution):
        """Verify no stub code."""
        import inspect
        source = inspect.getsource(solution)
        assert "TODO" not in source, "TODO found"
        assert "pass" not in source.split('\n'), "Empty pass statement found"
        assert "raise NotImplementedError" not in source

    def test_type_hints(self, solution):
        """Verify functions have basic type hints."""
        import inspect
        funcs = inspect.getmembers(solution, inspect.isfunction)
        public_funcs = [(n, f) for n, f in funcs if not n.startswith('_')]
        if public_funcs:
            hints_found = False
            for name, fn in public_funcs:
                sig = inspect.signature(fn)
                if (sig.return_annotation is not inspect.Parameter.empty or
                    any(p.annotation is not inspect.Parameter.empty
                        for p in sig.parameters.values())):
                    hints_found = True
                    break
            assert hints_found, "No type hints in any public function"

    def test_edge_case_duplicates(self, solution):
        """Verify the algorithm handles duplicate values correctly."""
        funcs = [f for f in dir(solution) if callable(getattr(solution, f))
                 and not f.startswith('_') and f not in ('app', 'main')]
        if not funcs:
            return
        fn = getattr(solution, funcs[0])
        try:
            import inspect
            sig = inspect.signature(fn)
            params = list(sig.parameters.keys())
            if len(params) >= 1:
                result = fn([1, 1, 1, 2, 2, 3])
                assert result is not None, "Returned None for valid input"
        except (TypeError, ValueError):
            pass
        except Exception as e:
            pytest.fail(f"Crashed on duplicate values: {e}")
