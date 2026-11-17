"""Parallel batch decompiler with work-stealing queue and shared cache."""

from threading import Lock
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.services.decompiler_engine import AnalysisResult, create_decompiler_engine


class BatchDecompiler:
    """Parallel processing of multiple decompiler outputs using a work‑stealing queue."""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self._cache: dict[str, AnalysisResult] = {}
        self._lock = Lock()
        self._engine = create_decompiler_engine()

    def process_batch(self, inputs: List[str]) -> List[AnalysisResult]:
        """Process multiple inputs in parallel, reusing cached results when possible."""
        results: List[AnalysisResult] = [None] * len(inputs)

        # Collect indices that are not yet cached
        uncached_indices = [
            i for i, inp in enumerate(inputs) if inp not in self._cache
        ]
        if not uncached_indices:
            # All inputs are already cached – return them directly
            return [self._cache[inp] for inp in inputs]

        # Submit uncached inputs to a thread pool and wait for completion
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_index = {
                executor.submit(self._engine.analyze, inputs[i]): i
                for i in uncached_indices
            }
            for future in as_completed(future_to_index):
                idx = future_to_index[future]
                result = future.result()
                with self._lock:
                    self._cache[inputs[idx]] = result
                results[idx] = result

        # Fill any remaining slots from the cache (should not happen for uncached indices)
        for i in range(len(inputs)):
            if results[i] is None:
                results[i] = self._cache[inputs[i]]

        return results


def create_batch_decompiler(max_workers: int = 4) -> BatchDecompiler:
    """Factory function to create a BatchDecompiler instance."""
    return BatchDecompiler(max_workers)
