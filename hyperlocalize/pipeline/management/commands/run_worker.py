import time

from django.core.management.base import BaseCommand

from hyperlocalize.pipeline import jobs


class Command(BaseCommand):
    help = "Run a job worker for one lane (ADR 0003): default, synthesis, or all."

    def add_arguments(self, parser):
        parser.add_argument("--lane", choices=["default", "synthesis", "all"], default="all")
        parser.add_argument("--drain", action="store_true", help="Run until the queue is empty, then exit.")
        parser.add_argument("--poll", type=float, default=1.0, help="Seconds to wait when the queue is empty.")

    def handle(self, *args, lane, drain, poll, **options):
        lanes = ["default", "synthesis"] if lane == "all" else [lane]
        if drain:
            done = jobs.drain(lanes)
            self.stdout.write(f"Ran {len(done)} job(s).")
            return
        self.stdout.write(f"Worker started for lane(s): {', '.join(lanes)}. Ctrl+C to stop.")
        last_recovery = 0.0
        try:
            while True:
                if time.monotonic() - last_recovery > 60:
                    jobs.recover_stale()
                    last_recovery = time.monotonic()
                job = jobs.work_once(lanes)
                if job is None:
                    time.sleep(poll)
                else:
                    self.stdout.write(f"{job.type} #{job.pk}: {job.status}")
        except KeyboardInterrupt:
            self.stdout.write("Worker stopped.")
