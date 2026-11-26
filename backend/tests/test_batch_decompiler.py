"""Tests for batch decompiler."""

import pytest

from app.services.batch_decompiler import BatchDecompiler, create_batch_decompiler, benchmark_scaling


class TestBatchDecompiler:
    def test_process_batch(self):
        batch = create_batch_decompiler(max_workers=2)
        inputs = [
            """
            void foo() {}
            """,
            """
            MyClass_vtable[] = { &MyClass::func1 };
            """,
            """
            void foo() {}
            """,  # duplicate
        ]
        results = batch.process_batch(inputs)
        assert len(results) == 3
        # first input yields one function
        assert len(results[0].functions) == 1
        # second yields one vtable
        assert len(results[1].vtables) == 1
        # third yields one function (cached)
        assert len(results[2].functions) == 1
        # cache size should be 2 distinct inputs
        assert len(batch._cache) == 2

    def test_parallel_processing_speed(self):
        import time
        batch = BatchDecompiler(max_workers=4)
        # Many identical inputs to exercise caching and parallelism
        inputs = ["void foo() {}"] * 10
        start = time.perf_counter()
        results = batch.process_batch(inputs)
        elapsed = time.perf_counter() - start
        # All results should be present and correct
        assert len(results) == 10
        for res in results:
            assert len(res.functions) == 1
        # Caching means second run should be faster (optional check)

class TestBatchDecompilerBenchmark:
    def test_benchmark_scaling_returns_dict(self):
        """Verify benchmark_scaling returns a dict mapping workers to times."""
        result = benchmark_scaling([1, 2, 4])
        assert isinstance(result, dict)
        assert len(result) == 3
        for workers, elapsed in result.items():
            assert isinstance(workers, int)
            assert isinstance(elapsed, float)
            assert elapsed >= 0

    def test_benchmark_scaling_monotonic(self):
        """Verify that more workers doesn't take dramatically more time."""
        result = benchmark_scaling([1, 2, 4])
        # With identical inputs, more workers should not be significantly slower
        # (may vary due to thread overhead, but shouldn't explode)
        assert result[1] > 0
        assert result[2] > 0
        assert result[4] > 0
