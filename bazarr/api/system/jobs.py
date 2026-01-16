# coding=utf-8

import logging

from flask_restx import Resource, Namespace, reqparse, fields, marshal

from app.jobs_queue import jobs_queue

from ..utils import authenticate

api_ns_system_jobs = Namespace('System Jobs', description='List or delete jobs from the queue')


@api_ns_system_jobs.route('system/jobs')
class SystemJobs(Resource):
    get_response_model = api_ns_system_jobs.model('SystemJobsGetResponse', {
        'job_id': fields.Integer(),
        'job_name': fields.String(),
        'status': fields.String(),
        'last_run_time': fields.String(),
        'is_progress': fields.Boolean(),
        'is_signalr': fields.Boolean(),
        'progress_value': fields.Integer(),
        'progress_max': fields.Integer(),
        'progress_message': fields.String(),
    })

    get_request_parser = reqparse.RequestParser()
    get_request_parser.add_argument('id', type=int, required=False, help='Job ID to return', default=None)
    get_request_parser.add_argument('status', type=str, required=False, help='Job status to return', default=None,
                                    choices=['pending', 'running', 'failed', 'completed'])

    @authenticate
    @api_ns_system_jobs.doc(parser=get_request_parser)
    @api_ns_system_jobs.response(204, 'Success')
    @api_ns_system_jobs.response(401, 'Not Authenticated')
    def get(self):
        """List jobs from the queue"""
        args = self.get_request_parser.parse_args()
        job_id = args.get('id')
        status = args.get('status')
        return marshal(jobs_queue.list_jobs_from_queue(job_id=job_id, status=status), self.get_response_model,
                       envelope='data')

    patch_request_parser = reqparse.RequestParser()
    patch_request_parser.add_argument('queueName', type=str, required=True, help='Jobs queue name to empty',
                                      choices=['pending', 'failed', 'completed'])

    @authenticate
    @api_ns_system_jobs.doc(parser=patch_request_parser)
    @api_ns_system_jobs.response(204, 'Success')
    @api_ns_system_jobs.response(400, 'Jobs queue name not provided')
    @api_ns_system_jobs.response(401, 'Not Authenticated')
    def patch(self):
        """Empty a specific jobs queue"""
        args = self.patch_request_parser.parse_args()
        queue_name = args.get('queueName')
        if queue_name:
            jobs_queue.empty_jobs_queue(queue_name=queue_name)
            return '', 204
        else:
            return 'Jobs queue name not provided', 400

    delete_request_parser = reqparse.RequestParser()
    delete_request_parser.add_argument('id', type=int, required=True, help='Job ID to delete from queue')

    @authenticate
    @api_ns_system_jobs.doc(parser=delete_request_parser)
    @api_ns_system_jobs.response(204, 'Success')
    @api_ns_system_jobs.response(400, 'Job ID not provided')
    @api_ns_system_jobs.response(401, 'Not Authenticated')
    def delete(self):
        """Delete a job from the queue"""
        args = self.delete_request_parser.parse_args()
        job_id = args.get('id')
        if job_id:
            deleted = jobs_queue.remove_job_from_pending_queue(job_id=job_id)
            if deleted:
                return '', 204
        return 'Job ID not provided', 400

    post_request_parser = reqparse.RequestParser()
    post_request_parser.add_argument('job_name', type=str, required=True, help='Name for the test job')
    post_request_parser.add_argument('duration', type=int, required=True, help='Duration in seconds')
    post_request_parser.add_argument('job_type', type=str, required=False, default='short',
                                     choices=['short', 'long'],
                                     help='Job type: "short" for regular, "long" for known long-running pattern')

    @authenticate
    @api_ns_system_jobs.doc(parser=post_request_parser)
    @api_ns_system_jobs.response(201, 'Job created')
    @api_ns_system_jobs.response(401, 'Not Authenticated')
    def post(self):
        """Create a test job for stress testing the queue system"""
        args = self.post_request_parser.parse_args()
        job_name = args.get('job_name')
        duration = args.get('duration')
        job_type = args.get('job_type', 'short')

        # Use known long-running pattern if job_type is 'long'
        if job_type == 'long':
            # Prefix with known long pattern to route to long queue
            job_name = f"Sync with Sonarr - {job_name}"

        job_id = jobs_queue.feed_jobs_pending_queue(
            job_name=job_name,
            module='app.test_jobs',
            func='test_job_function',
            kwargs={'duration_seconds': duration, 'job_name': job_name}
        )
        return {'job_id': job_id, 'job_name': job_name, 'duration': duration, 'job_type': job_type}, 201
