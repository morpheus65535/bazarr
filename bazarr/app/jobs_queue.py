# coding=utf-8

import logging
import importlib
import inspect
import os
import time

from time import sleep
from datetime import datetime
from collections import deque
from typing import Union

from app.event_handler import event_stream

bazarr_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


class Job:
    """
    Represents a job with details necessary for its identification and execution.

    This class encapsulates information about a job, including its unique identifier,
    name, and the module or function it executes. It can also include optional
    arguments and keyword arguments for job execution. The status of the job is also
    tracked.

    :ivar job_id: Unique identifier of the job.
    :type job_id: int
    :ivar job_name: Descriptive name of the job.
    :type job_name: str
    :ivar module: Name of the module where the job function resides.
    :type module: str
    :ivar func: The name of the function to execute the job.
    :type func: str
    :ivar args: Positional arguments for the function, it defaults to None.
    :type args: list, optional
    :ivar kwargs: Keyword arguments for the function, it defaults to None.
    :type kwargs: dict, optional
    :ivar status: Current status of the job, initialized to 'pending'.
    :type status: str
    :ivar last_run_time: Last time the job was run, initialized to None.
    :type last_run_time: datetime
    :ivar is_progress: Indicates whether the job is a progress job, defaults to False.
    :type is_progress: bool
    :ivar progress_value: Actual value of the job's progress, initialized to 0.
    :type progress_value: int
    :ivar progress_max: Maximum value of the job's progress, initialized to 0.
    :type progress_max: int
    :ivar progress_message: Message shown for this job's progress, initialized to an empty string.
    :type progress_message: str
    :ivar job_returned_value: Value returned by the job function, initialized to None.
    :type job_returned_value: Any
    """
    def __init__(self, job_id: int, job_name: str, module: str, func: str, args: list = None, kwargs: dict = None,
                 is_progress=False, progress_max: int = 0, job_returned_value=None,):
        self.job_id = job_id
        self.job_name = job_name
        self.module = module
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.status = 'pending'
        self.last_run_time = datetime.now()
        self.is_progress = is_progress
        self.progress_value = 0
        self.progress_max = progress_max
        self.progress_message = ""
        self.job_returned_value = job_returned_value


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
        self.jobs_running_queue = deque(maxlen=1)
        self.jobs_failed_queue = deque(maxlen=10)
        self.jobs_completed_queue = deque(maxlen=10)
        self.current_job_id = 0

    def feed_jobs_pending_queue(self, job_name, module, func, args: list = None, kwargs: dict = None,
                                is_progress=False, progress_max: int = 0,):
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
        :param is_progress: Indicates whether the job is a progress job, defaults to False.
        :type is_progress: bool
        :param progress_max: Maximum value of the job's progress, initialized to 0.
        :type progress_max: int
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
                kwargs=kwargs,
                is_progress=is_progress,
                progress_max=progress_max,)
        )
        logging.debug(f"Task {job_name} ({new_job_id}) added to queue")
        event_stream(type='jobs', action='update', payload={"job_id": new_job_id, "progress_value": None,
                                                            "status": "pending"})

        return new_job_id

    def list_jobs_from_queue(self, job_id: int = None, status: str = None):
        """
        List jobs from a specific queue or all queues based on filters.

        This method retrieves job details from various job queues based on provided
        criteria. It can filter jobs by their `job_id` and/or their `status`. If no
        `job_id` or `status` is provided, it returns details of all jobs across
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
            return sorted([vars(job) for job in queues], key=lambda x: x['last_run_time'], reverse=True)
    
    def get_job_status(self, job_id: int):
        """
        Retrieves the status of a job by its ID from a queue. If the job exists and has a
        status field, it returns its value. Otherwise, it returns "Unknown job".

        :param job_id: ID of the job to retrieve status for
        :type job_id: int
        :return: The status of the job if available, otherwise "Unknown job"
        :rtype: str
        """
        job = self.list_jobs_from_queue(job_id=job_id)
        if job and 'status' in job[0]:
            return job[0]['status']
        else:
            return "Unknown job"

    def get_job_returned_value(self, job_id: int):
        """
        Fetches the returned value of a job from the queue provided its unique identifier.

        This function retrieves the job details from the queue using the provided job
        identifier. If the job exists and contains a 'job_returned_value' key, the
        function returns the corresponding value. Otherwise, it defaults to returning
        None.

        :param job_id: The unique identifier of the job to fetch the returned value for.
        :type job_id: int
        :return: The returned value of the job if it exists, otherwise None.
        :rtype: Any
        """
        job = self.list_jobs_from_queue(job_id=job_id)
        if job and 'job_returned_value' in job[0]:
            return job[0]['job_returned_value']
        else:
            return None

    def update_job_progress(self, job_id: int, progress_value: Union[int, str, None] = None,
                            progress_max: Union[int, None] = None, progress_message: str = ""):
        """
        Updates the progress value and message for a specific job within the running jobs queue. The function
        iterates through a queue of running jobs, identifies the matching job by its ID, and updates its progress
        value and message. Afterward, triggers an event stream for the updated job.

        :param job_id: The unique identifier of the job to be updated.
        :type job_id: int
        :param progress_value: The new progress value to be set for the job. If 'max' is provided, progress_value will
        equal progress_max.
        :type progress_value: int or str or None
        :param progress_max: Maximum value of the job's progress.
        :type progress_max: int or None
        :param progress_message: An optional message providing additional details about the current progress.
        :type progress_message: str
        :return: Returns True if the job's progress was successfully updated, otherwise False.
        :rtype: bool
        """
        for job in self.jobs_running_queue:
            if job.job_id == job_id:
                payload = self._build_progress_payload(job, progress_value, progress_max, progress_message)
                event_stream(type='jobs', action='update', payload=payload)
                return True
        return False

    @staticmethod
    def _build_progress_payload(job, progress_value: Union[int, str, None],
                                progress_max: Union[int, None], progress_message: str):
        """
        Builds the payload dictionary for job progress updates and updates job attributes.

        :param job: The job instance to update.
        :param progress_value: The new progress value to be set for the job.
        :type progress_value: int or str or None
        :param progress_max: Maximum value of the job's progress.
        :type progress_max: int or None
        :param progress_message: An optional message providing additional details about the current progress.
        :type progress_message: str
        :return: Dictionary containing the payload for the event stream.
        :rtype: dict
        """
        payload = {"job_id": job.job_id, "status": job.status}
        progress_max_updated = False

        if progress_value:
            if progress_value == 'max':
                progress_value = job.progress_max or 1
                job.progress_value = job.progress_max = progress_value
                progress_max_updated = True
            else:
                job.progress_value = progress_value
        payload["progress_value"] = job.progress_value

        if progress_max and not progress_max_updated:
            job.progress_max = progress_max
        payload["progress_max"] = job.progress_max

        if progress_message:
            job.progress_message = progress_message
        payload["progress_message"] = job.progress_message

        return payload

    def update_job_progress_status(self, job_id: int, is_progress: bool = False) -> bool:
        """
        Updates the is_progress attribute for a specific job.

        :param job_id: The unique identifier of the job to be updated.
        :type job_id: int
        :param is_progress: The new value for is_progress attribute.
        :type is_progress: bool
        :return: Returns True if the job's progress status was successfully updated, otherwise False.
        :rtype: bool
        """
        for job in self.jobs_running_queue:
            if job.job_id == job_id:
                job.is_progress = is_progress
                event_stream(type='jobs', action='update', payload={"job_id": job.job_id})
                return True
        return False

    def add_job_from_function(self, job_name: str, is_progress: bool, progress_max: int = 0):
        """
        Adds a job to the pending queue using the details of the calling function. The job is then executed, and the
        method waits until the job is completed or has failed.

        :param job_name: Name of the job to be added.
        :type job_name: str
        :param is_progress: Flag indicating whether the progress of the job should be tracked.
        :type is_progress: bool
        :param progress_max: Maximum progress value for the job, default is 0.
        :type progress_max: int
        :return: ID of the added job.
        :rtype: Any
        """
        # Get the current frame
        current_frame = inspect.currentframe()

        # Get the frame of the caller (parent function)
        # The caller's frame is at index 1 in the stack
        caller_frame = current_frame.f_back

        # Get the code object of the caller
        caller_code = caller_frame.f_code

        # Get the name of the parent function
        parent_function_name = caller_code.co_name

        # Get the file path of the parent function
        relative_parent_function_path = os.path.relpath(caller_code.co_filename, start=bazarr_dir)
        parent_function_path = os.path.splitext(relative_parent_function_path)[0].replace(os.sep, '.')

        # Get the function signature of the caller
        caller_signature = inspect.signature(inspect.getmodule(caller_code).__dict__[caller_code.co_name])
        # Get the local variables within the caller's frame
        caller_locals = caller_frame.f_locals

        bound_arguments = caller_signature.bind(**caller_locals)
        arguments = bound_arguments.arguments

        # Clean up the frame objects to prevent reference cycles
        del current_frame, caller_frame, caller_code, caller_signature, caller_locals, bound_arguments

        # Feed the job to the pending queue
        job_id = self.feed_jobs_pending_queue(job_name=job_name, module=parent_function_path, func=parent_function_name,
                                              kwargs=arguments, is_progress=is_progress, progress_max=progress_max)

        # Wait for the job to complete or fail
        while jobs_queue.get_job_status(job_id=job_id) in ['pending', 'running']:
            time.sleep(0.1)

        return job_id

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
            if job.job_id == job_id and job.status == 'pending':
                try:
                    self.jobs_pending_queue.remove(job)
                except ValueError:
                    return False
                else:
                    logging.debug(f"Task {job.job_name} ({job.job_id}) removed from queue")
                    event_stream(type='jobs', action='delete', payload={"job_id": job.job_id})
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
                    sleep(0.1)
                    continue
                except (KeyboardInterrupt, SystemExit):
                    break
                except Exception as e:
                    logging.exception(f"Exception raised while running job: {e}")
                else:
                    try:
                        job.status = 'running'
                        job.last_run_time = datetime.now()
                        if 'job_id' not in job.kwargs or not job.kwargs['job_id']:
                            job.kwargs['job_id'] = job.job_id
                        self.jobs_running_queue.append(job)

                        # sending event to update the status of progress jobs
                        payload = {"job_id": job.job_id, "status": job.status}
                        if job.is_progress:
                            payload["progress_value"] = None
                            payload["progress_max"] = job.progress_max
                            payload["progress_message"] = job.progress_message
                        event_stream(type='jobs', action='update', payload=payload)

                        logging.debug(f"Running job {job.job_name} (id {job.job_id}): "
                                      f"{job.module}.{job.func}({job.args}, {job.kwargs})")
                        job.job_returned_value = (getattr(importlib.import_module(job.module), job.func)
                                                  (*job.args, **job.kwargs))
                    except Exception as e:
                        logging.exception(f"Exception raised while running function: {e}")
                        job.status = 'failed'
                        job.last_run_time = datetime.now()
                        self.jobs_failed_queue.append(job)
                    else:
                        job.status = 'completed'
                        job.last_run_time = datetime.now()
                        self.jobs_completed_queue.append(job)
                    finally:
                        if job in self.jobs_running_queue:
                            self.jobs_running_queue.remove(job)
                        try:
                            # Send a complete event payload with status and progress_value
                            # progress_value being None forces frontend to fetch a full job payload
                            payload = {
                                "job_id": job.job_id,
                                "status": job.status,  # 'completed' or 'failed'
                                "progress_value": None  # Trigger frontend API call to update the whole job payload
                            }
                            event_stream(type='jobs', action='update', payload=payload)
                        except Exception as e:
                            logging.exception(f"Exception raised while sending event: {e}")
            else:
                sleep(0.1)


jobs_queue = JobsQueue()
