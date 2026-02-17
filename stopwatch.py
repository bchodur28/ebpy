import time
from datetime import datetime, timedelta

def timer_dec(base_fn):
    def enhanced_fn(*args, **kwargs):
        start_timer = time.time()
        result = base_fn(*args, **kwargs)
        end_timer = time.time()
        print(f"The total runtime for this function: {end_timer - start_timer}")
        return result
    return enhanced_fn