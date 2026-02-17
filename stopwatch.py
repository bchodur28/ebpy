import time
import functools

def timer_dec(base_fn):
    def enhanced_fn(*args, **kwargs):
        start = time.perf_counter()
        result = base_fn(*args, **kwargs)
        end = time.perf_counter()
        print(f"{base_fn.__name__} runtime: {end - start:.6} seconds")
        return result
    return enhanced_fn