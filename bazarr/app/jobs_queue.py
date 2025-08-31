# coding=utf-8

import logging
import importlib

from time import sleep
from collections import deque

from app.event_handler import event_stream


class Job:
    def __init__(self, job_id, job_name, module, func, args: list = None, kwargs: dict = None):
        self.job_id = job_id
        self.job_name = job_name
        self.module = module
        self.func = func
        self.args = args
        self.kwargs = kwargs


class JobsQueue:
    def __init__(self):
        self.jobs_queue = deque()
        self.current_job_id = 0

    def feed_jobs_queue(self, job_name, module, func, args: list = None, kwargs: dict = None):
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}

        self.current_job_id += 1
        self.jobs_queue.append(
            Job(job_id=self.current_job_id,
                job_name=job_name,
                module=module,
                func=func,
                args=args,
                kwargs=kwargs,)
        )
        logging.debug(f"Task {job_name} ({self.current_job_id}) added to queue")
        event_stream(type='jobs')

    def list_jobs_from_queue(self):
        return [vars(job) for job in self.jobs_queue]
    
    def remove_job_from_queue(self, job_id):
        for job in self.jobs_queue:
            if job.job_id == job_id:
                try:
                    self.jobs_queue.remove(job)
                except ValueError:
                    return False
                else:
                    logging.debug(f"Task {job.job_name} ({job.job_id}) removed from queue")
                    event_stream(type='jobs')
                    return True
        return False

    def consume_jobs_queue(self):
        while True:
            if self.jobs_queue:
                try:
                    job = self.jobs_queue.popleft()
                except IndexError:
                    pass
                except (KeyboardInterrupt, SystemExit):
                    break
                except Exception as e:
                    logging.exception(f"Exception raised while running job: {e}")
                    continue
                else:
                    try:
                        logging.debug(f"Running job {job.job_name} (id {job.job_id}): "
                                      f"{job.module}.{job.func}({job.args}, {job.kwargs})")
                        event_stream(type='jobs')
                        func_to_call = getattr(importlib.import_module(job.module), job.func)
                        func_to_call(*job.args, **job.kwargs)
                    except Exception as e:
                        logging.exception(f"Exception raised while running function: {e}")
            else:
                sleep(0.1)


jobs_queue = JobsQueue()
