# coding=utf-8

from flask import request, jsonify
from flask_restx import Resource, Namespace

from app.scheduler import scheduler

from ..utils import authenticate

api_ns_system_tasks = Namespace('systemTasks', description='System tasks API endpoint')


@api_ns_system_tasks.route('system/tasks')
class SystemTasks(Resource):
    @authenticate
    def get(self):
        taskid = request.args.get('taskid')

        task_list = scheduler.get_task_list()

        if taskid:
            for item in task_list:
                if item['job_id'] == taskid:
                    task_list = [item]
                    continue

        return jsonify(data=task_list)

    @authenticate
    def post(self):
        taskid = request.form.get('taskid')

        scheduler.execute_job_now(taskid)

        return '', 204
