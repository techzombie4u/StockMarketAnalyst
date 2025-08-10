
"""
Parallel execution utilities with bounded thread pool and batching
"""

import asyncio
import threading
import concurrent.futures
import multiprocessing
from typing import List, Callable, Any, Optional, Dict, Iterator
import logging
import time

from .telemetry import telemetry
from ..config.feature_flags import feature_flags

logger = logging.getLogger(__name__)

class BoundedExecutor:
    def __init__(self, max_workers: Optional[int] = None):
        if max_workers is None:
            # Conservative worker count
            cpu_count = multiprocessing.cpu_count()
            max_workers = min(8, cpu_count)
            
        self.max_workers = max_workers
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        logger.info(f"Initialized BoundedExecutor with {max_workers} workers")
        
    def submit(self, fn: Callable, *args, **kwargs) -> concurrent.futures.Future:
        """Submit task to executor"""
        telemetry.increment('thread_pool_submissions')
        return self.executor.submit(fn, *args, **kwargs)
        
    def map(self, fn: Callable, iterable: List[Any], timeout: Optional[float] = None) -> Iterator[Any]:
        """Map function over iterable with bounded parallelism"""
        telemetry.increment('thread_pool_maps')
        return self.executor.map(fn, iterable, timeout=timeout)
        
    def shutdown(self, wait: bool = True):
        """Shutdown executor"""
        self.executor.shutdown(wait=wait)

class BatchProcessor:
    def __init__(self, batch_size: int = 5, stagger_delay: float = 0.1):
        self.batch_size = batch_size
        self.stagger_delay = stagger_delay
        
    def create_batches(self, items: List[Any]) -> List[List[Any]]:
        """Split items into batches"""
        batches = []
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batches.append(batch)
        return batches
        
    async def process_batches_async(self, items: List[Any], 
                                   process_fn: Callable[[List[Any]], Any]) -> List[Any]:
        """Process batches asynchronously with staggering"""
        batches = self.create_batches(items)
        results = []
        
        for i, batch in enumerate(batches):
            if i > 0:
                await asyncio.sleep(self.stagger_delay)
                
            batch_result = await asyncio.get_event_loop().run_in_executor(
                None, process_fn, batch
            )
            results.extend(batch_result if isinstance(batch_result, list) else [batch_result])
            
        return results
        
    def process_batches_sync(self, items: List[Any], 
                           process_fn: Callable[[List[Any]], Any]) -> List[Any]:
        """Process batches synchronously with staggering"""
        batches = self.create_batches(items)
        results = []
        
        for i, batch in enumerate(batches):
            if i > 0:
                time.sleep(self.stagger_delay)
                
            batch_result = process_fn(batch)
            results.extend(batch_result if isinstance(batch_result, list) else [batch_result])
            
        return results

class TimeframeController:
    def __init__(self):
        self.active_timeframes = set()
        self.lock = threading.Lock()
        
    def can_process_timeframe(self, timeframe: str) -> bool:
        """Check if timeframe can be processed based on feature flags"""
        with self.lock:
            # Always allow current UI timeframe
            if len(self.active_timeframes) == 0:
                return True
                
            # Check concurrent timeframe setting
            if feature_flags.is_enabled('enable_all_timeframes_concurrent'):
                return len(self.active_timeframes) < 2  # Max 2 concurrent
            else:
                return False  # Only one at a time
                
    def start_processing(self, timeframe: str) -> bool:
        """Mark timeframe as being processed"""
        with self.lock:
            if self.can_process_timeframe(timeframe):
                self.active_timeframes.add(timeframe)
                telemetry.set_gauge('active_timeframes', len(self.active_timeframes))
                return True
            return False
            
    def finish_processing(self, timeframe: str):
        """Mark timeframe as finished processing"""
        with self.lock:
            self.active_timeframes.discard(timeframe)
            telemetry.set_gauge('active_timeframes', len(self.active_timeframes))

class ParallelManager:
    def __init__(self):
        self.executor = BoundedExecutor()
        self.batch_processor = BatchProcessor()
        self.timeframe_controller = TimeframeController()
        
    async def process_symbols_parallel(self, symbols: List[str], 
                                     process_fn: Callable[[str], Any],
                                     timeframe: str = 'current') -> Dict[str, Any]:
        """Process symbols in parallel with timeframe control"""
        if not self.timeframe_controller.start_processing(timeframe):
            logger.warning(f"Timeframe {timeframe} queued - concurrent limit reached")
            return {}
            
        try:
            # Use batch processing for large symbol lists
            if len(symbols) > 10:
                logger.info(f"Processing {len(symbols)} symbols in batches for {timeframe}")
                
                def batch_fn(symbol_batch):
                    return [process_fn(symbol) for symbol in symbol_batch]
                    
                results = await self.batch_processor.process_batches_async(symbols, batch_fn)
                return dict(zip(symbols, results))
            else:
                # Direct parallel processing for smaller lists
                loop = asyncio.get_event_loop()
                tasks = [
                    loop.run_in_executor(self.executor.executor, process_fn, symbol)
                    for symbol in symbols
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                return dict(zip(symbols, results))
                
        finally:
            self.timeframe_controller.finish_processing(timeframe)
            
    def shutdown(self):
        """Shutdown parallel manager"""
        self.executor.shutdown()

# Global parallel manager
parallel_manager = ParallelManager()
