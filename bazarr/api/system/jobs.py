# coding=utf-8

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
            deleted = jobs_queue.remove_job_from_pending_queue(task_id=job_id)
            if deleted:
                return '', 204
        return 'Job ID not provided', 400
