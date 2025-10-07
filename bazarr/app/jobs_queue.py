# coding=utf-8

import logging
import importlib

from time import sleep
from collections import deque

from app.event_handler import event_stream


class Job:
    """
    Represents a job with details necessary for its identification and execution.

    This class encapsulates information about a job, including its unique identifier,
    name, and the module or function it executes. It can also include optional
    arguments and keyword arguments for job execution. Status of the job is also
    tracked.

    :ivar job_id: Unique identifier of the job.
    :type job_id: int
    :ivar job_name: Descriptive name of the job.
    :type job_name: str
    :ivar module: Name of the module where the job function resides.
    :type module: str
    :ivar func: The name of the function to execute the job.
    :type func: str
    :ivar args: Positional arguments for the function, defaults to None.
    :type args: list, optional
    :ivar kwargs: Keyword arguments for the function, defaults to None.
    :type kwargs: dict, optional
    :ivar status: Current status of the job, initialized to 'pending'.
    :type status: str
    """
    def __init__(self, job_id: int, job_name: str, module: str, func: str, args: list = None, kwargs: dict = None):
        self.job_id = job_id
        self.job_name = job_name
        self.module = module
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.status = 'pending'


class JobsQueue:
    """
    Manages a queue of jobs, tracks their states, and processes them.

    This class is designed to handle a queue of jobs, enabling submission, tracking,
    and execution of tasks. Jobs are categorized into different queues (`pending`,
    `running`, `failed`, and `completed`) based on their current status. It provides
    methods to add, list, remove, and consume jobs in a controlled manner.

    :ivar jobs_pending_queue: Queue containing jobs that are pending execution.
    :type jobs_pending_queue: deque
    :ivar jobs_running_queue: Queue containing jobs that are currently being executed.
    :type jobs_running_queue: deque
    :ivar jobs_failed_queue: Queue containing jobs that failed during execution. It maintains a
        maximum size of 10 entries.
    :type jobs_failed_queue: deque
    :ivar jobs_completed_queue: Queue containing jobs that were executed successfully. It maintains
        a maximum size of 10 entries.
    :type jobs_completed_queue: deque
    :ivar current_job_id: Identifier of the latest job, incremented with each new job added to the queue.
    :type current_job_id: int
    """
    def __init__(self):
        self.jobs_pending_queue = deque()
        self.jobs_running_queue = deque()
        self.jobs_failed_queue = deque(maxlen=10)
        self.jobs_completed_queue = deque(maxlen=10)
        self.current_job_id = 0

    def feed_jobs_pending_queue(self, job_name, module, func, args: list = None, kwargs: dict = None):
        """
        Adds a new job to the pending jobs queue with specified details and triggers an event
        to notify about the queue update. Each job is uniquely identified by a job ID,
        which is automatically incremented for each new job. Logging is performed to
        record the job addition.

        :param job_name: Name of the job to be added to the queue.
        :type job_name: str
        :param module: Module under which the job's function resides (ex: sonarr.sync.series).
        :type module: str
        :param func: Function name that represents the job (ex: update_series).
        :type func: str
        :param args: List of positional arguments to be passed to the function.
        :type args: list
        :param kwargs: Dictionary of keyword arguments to be passed to the function.
        :type kwargs: dict
        :return: The unique job ID assigned to the newly queued job.
        :rtype: int
        """
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

        return new_job_id

    def list_jobs_from_queue(self, job_id: int = None, status: str = None):
        """
        List jobs from a specific queue or all queues based on filters.

        This method retrieves job details from various job queues based on provided
        criteria. It can filter jobs by their `job_id` and/or their `status`. If no
        `job_id` or `status` are provided, it returns details of all jobs across
        all queues.

        :param job_id: Optional; The unique ID of the job to filter the results.
        :type job_id: int
        :param status: Optional; The status of jobs to filter the results. Expected
            values are 'pending', 'running', 'failed', or 'completed'.
        :type status: str
        :return: A list of dictionaries with job details that match the given filters.
            If no matches are found, an empty list is returned.
        :rtype: list[dict]
        """
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
    
    def remove_job_from_pending_queue(self, job_id: int):
        """
        Removes a job from the pending queue based on the provided job ID.

        This method iterates over the jobs in the pending queue and identifies the
        job that matches the given job ID. If the job exists in the queue, it is
        removed, and a debug message is logged. Additionally, an event is streamed
        to indicate the deletion action. If the job is not found, the method returns
        False.

        :param job_id: The ID of the job to be removed.
        :type job_id: int
        :return: A boolean indicating whether the removal was successful. Returns
                 True if the job was removed, otherwise False.
        :rtype: bool
        """
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
        """
        Consume and execute jobs from the jobs pending queue until the queue is empty or interrupted. This
        method handles job status updates, execution tracking, and proper queuing through consuming,
        running, failing, or completing jobs.

        Errors during job execution are logged appropriately, and the queue management ensures that jobs
        are completely handled before removal from the running queue. The method supports interruption
        via keyboard signals and ensures system stability during unexpected exceptions.

        :raises SystemExit: If a termination request (via SystemExit) occurs, the method halts execution.
        """
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
                        getattr(importlib.import_module(job.module), job.func)(*job.args, **job.kwargs)
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
