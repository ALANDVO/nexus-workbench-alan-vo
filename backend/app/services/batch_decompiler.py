"""Parallel batch decompiler with work-stealing queue and shared cache."""

from collections import deque
from threading import Lock
from typing import List, Deque

from concurrent.futures import ThreadPoolExecutor, as_completed

from app.services.decompiler_engine import AnalysisResult, create_decompiler_engine


class WorkStealingQueue:
    """Simple work-stealing queue shared across workers."""

    def __init__(self, initial_tasks: List[int]):
        self._queue: Deque[int] = deque(initial_tasks)
        self._lock = Lock()
        self._stolen: List[int] = []

    def pop(self) -> int | None:
        """Pop a task from the front ( victim thread takes from front)."""
        with self._lock:
            if self._queue:
                return self._queue.popleft()
            return None

    def steal(self) -> int | None:
        """Steal a task from the end (other thread takes from end)."""
        with self._lock:
            if self._queue:
                return self._queue.pop()
            return None

    def add_stolen(self, task_id: int) -> None:
        """Track a stolen task."""
        with self._lock:
            self._stolen.append(task_id)

    def remaining(self) -> int:
        """Return number of tasks still in the queue."""
        with self._lock:
            return len(self._queue)


class BatchDecompiler:
    """Parallel processing of multiple decompiler outputs using a work‑stealing queue."""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self._cache: dict[str, AnalysisResult] = {}
        self._cache_lock = Lock()
        self._engine = create_decompiler_engine()

    def process_batch(self, inputs: List[str]) -> List[AnalysisResult]:
        """Process multiple inputs in parallel, reusing cached results when possible.

        Uses a work-stealing queue to balance load across workers.
        """
        results: List[AnalysisResult] = [None] * len(inputs)

        # Collect indices that are not yet cached
        uncached_indices = [
            i for i, inp in enumerate(inputs) if inp not in self._cache
        ]
        if not uncached_indices:
            # All inputs are already cached – return them directly
            with self._cache_lock:
                return [self._cache[inp] for inp in inputs]

        # Initialize work-stealing queue with uncached task indices
        task_queue = WorkStealingQueue(uncached_indices)

        # Track which results belong to which input index
        result_holders: List[AnalysisResult | None] = [None] * len(inputs)

        def worker() -> None:
            """Worker loop: repeatedly steal/pop tasks and process them."""
            while True:
                # Try to pop first (own task), then steal from others
                idx = task_queue.pop()
                if idx is None:
                    idx = task_queue.steal()
                if idx is None:
                    break  # No more work

                with self._cache_lock:
                    if inputs[idx] in self._cache:
                        # Another worker already cached this; just use it
                        result_holders[idx] = self._cache[inputs[idx]]
                        continue

                # Process the input through the decompiler engine
                result = self._engine.analyze(inputs[idx])

                with self._cache_lock:
                    # Double-check cache in case another worker finished simultaneously
                    if inputs[idx] not in self._cache:
                        self._cache[inputs[idx]] = result
                    result_holders[idx] = result

        # Launch workers
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(worker) for _ in range(self.max_workers)]
            for future in as_completed(futures):
                future.result()

        # Fill results array
        for i, holder in enumerate(result_holders):
            if holder is not None:
                results[i] = holder
            elif inputs[i] in self._cache:
                results[i] = self._cache[inputs[i]]

        return results


def create_batch_decompiler(max_workers: int = 4) -> BatchDecompiler:
    """Factory function to create a BatchDecompiler instance."""
    return BatchDecompiler(max_workers)

def benchmark_scaling(max_workers_list: list[int], inputs_per_worker: int = 50) -> dict[int, float]:
    """Benchmark linear scaling across different worker counts.

    Args:
        max_workers_list: List of worker counts to test.
        inputs_per_worker: Number of identical inputs per worker.

    Returns:
        Dict mapping worker count to elapsed time in seconds.
    """
    from time import perf_counter
    from app.services.decompiler_engine import create_decompiler_engine

    # Generate identical inputs for clean scaling measurement
    engine = create_decompiler_engine()
    base_input = "void foo() {}\n" * 10  # 10 lines of simple function
    inputs = [base_input] * (len(max_workers_list) * inputs_per_worker)

    results: dict[int, float] = {}
    for workers in max_workers_list:
        batch = BatchDecompiler(max_workers=workers)
        start = perf_counter()
        batch.process_batch(inputs[: workers * inputs_per_worker])
        elapsed = perf_counter() - start
        results[workers] = elapsed
        print(f"  Workers={workers}: {elapsed:.3f}s")

    return results
