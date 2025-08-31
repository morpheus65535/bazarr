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
        self.status = 'pending'


class JobsQueue:
    def __init__(self):
        self.jobs_pending_queue = deque()
        self.jobs_running_queue = deque()
        self.jobs_failed_queue = deque(maxlen=10)
        self.jobs_completed_queue = deque(maxlen=10)
        self.current_job_id = 0

    def feed_jobs_pending_queue(self, job_name, module, func, args: list = None, kwargs: dict = None):
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}

        new_job_id = self.current_job_id = self.current_job_id + 1
        self.jobs_pending_queue.append(
            Job(job_id=new_job_id,
                job_name=job_name,
                module=module,
                func=func,
                args=args,
                kwargs=kwargs,)
        )
        logging.debug(f"Task {job_name} ({new_job_id}) added to queue")
        event_stream(type='jobs', action='update', payload=new_job_id)

    def list_jobs_from_queue(self, job_id=None, status=None):
        queues = self.jobs_pending_queue + self.jobs_running_queue + self.jobs_failed_queue + self.jobs_completed_queue
        if status:
            try:
                queues = self.__dict__[f'jobs_{status}_queue']
            except KeyError:
                return []

        if job_id:
            return [vars(job) for job in queues if job.job_id == job_id]
        else:
            return [vars(job) for job in queues]
    
    def remove_job_from_pending_queue(self, job_id):
        for job in self.jobs_pending_queue:
            if job.job_id == job_id:
                try:
                    self.jobs_pending_queue.remove(job)
                except ValueError:
                    return False
                else:
                    logging.debug(f"Task {job.job_name} ({job.job_id}) removed from queue")
                    event_stream(type='jobs', action='delete', payload=job.job_id)
                    return True
        return False

    def consume_jobs_pending_queue(self):
        while True:
            if self.jobs_pending_queue:
                try:
                    job = self.jobs_pending_queue.popleft()
                except IndexError:
                    pass
                except (KeyboardInterrupt, SystemExit):
                    break
                except Exception as e:
                    logging.exception(f"Exception raised while running job: {e}")
                else:
                    try:
                        job.status = 'running'
                        self.jobs_running_queue.append(job)
                        logging.debug(f"Running job {job.job_name} (id {job.job_id}): "
                                      f"{job.module}.{job.func}({job.args}, {job.kwargs})")
                        func_to_call = getattr(importlib.import_module(job.module), job.func)
                        func_to_call(*job.args, **job.kwargs)
                    except Exception as e:
                        logging.exception(f"Exception raised while running function: {e}")
                        job.status = 'failed'
                        self.jobs_failed_queue.append(job)
                    else:
                        event_stream(type='jobs', action='update', payload=job.job_id)
                        job.status = 'completed'
                        self.jobs_completed_queue.append(job)
                    finally:
                        self.jobs_running_queue.remove(job)
            else:
                sleep(0.1)


jobs_queue = JobsQueue()
