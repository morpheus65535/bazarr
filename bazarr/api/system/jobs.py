# coding=utf-8

from flask_restx import Resource, Namespace, reqparse, fields, marshal

from app.jobs_queue import jobs_queue

from ..utils import authenticate

api_ns_system_jobs = Namespace('System Jobs', description='List or delete jobs from the queue')


@api_ns_system_jobs.route('system/jobs')
class SystemJobs(Resource):
    get_response_model = api_ns_system_jobs.model('SystemJobsGetResponse', {
        'id': fields.Integer(),
        'name': fields.String(),
    })

    @authenticate
    @api_ns_system_jobs.doc(parser=None)
    @api_ns_system_jobs.response(204, 'Success')
    @api_ns_system_jobs.response(401, 'Not Authenticated')
    def get(self):
        """List jobs from the queue"""
        return marshal(jobs_queue.list_jobs_from_queue(), self.get_response_model, envelope='data')

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
            deleted = jobs_queue.remove_job_from_queue(task_id=job_id)
            if deleted:
                return '', 204
        return 'Job ID not provided', 400
