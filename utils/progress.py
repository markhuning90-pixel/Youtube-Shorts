from threading import Event, Thread
from time import perf_counter


def start_step(step_number, total_steps, message):
    print(f"[{step_number}/{total_steps}] {message}...", flush=True)
    return perf_counter()


def finish_step(step_number, total_steps, start_time):
    duration = perf_counter() - start_time
    print(
        f"[{step_number}/{total_steps}] OK nach {duration:.1f} Sekunden",
        flush=True,
    )


def fail_step(step_number, total_steps, start_time, error):
    duration = perf_counter() - start_time
    print(
        f"[{step_number}/{total_steps}] FEHLER nach {duration:.1f} Sekunden: {error}",
        flush=True,
    )


def run_with_progress(step_number, total_steps, message, function, *args, **kwargs):
    start_time = start_step(step_number, total_steps, message)
    completed = Event()

    def show_heartbeat():
        while not completed.wait(20):
            print("Wird noch verarbeitet...", flush=True)

    heartbeat = Thread(target=show_heartbeat, daemon=True)
    heartbeat.start()

    try:
        result = function(*args, **kwargs)
    except Exception as error:
        fail_step(step_number, total_steps, start_time, error)
        raise
    finally:
        completed.set()
        heartbeat.join()

    if result is None:
        fail_step(
            step_number,
            total_steps,
            start_time,
            "Der Schritt konnte nicht abgeschlossen werden.",
        )
        return None

    finish_step(step_number, total_steps, start_time)
    return result
