# services/tasks/project/api/tasks.py


from flask import Blueprint, jsonify, request, render_template
from project import db
from sqlalchemy import exc
from project.api.models import Task
from python_http_client import Client
import os
import json
import time

tasks_blueprint = Blueprint('tasks', __name__, template_folder='./templates')

@tasks_blueprint.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        db.session.add(Task(creator=request.form['creator'],
                       link=request.form['link']))
        db.session.commit()
    tasks = Task.query.all()
    return render_template('index.html', tasks=tasks)


@tasks_blueprint.route('/tasks/ping/pong', methods=['GET'])
def ping_pong():
    return jsonify({
        'status': 'success',
        'message': 'pong!'
    })


@tasks_blueprint.route('/tasks', methods=['POST'])
def add_single_task():
    post_data = request.get_json()
    response_object = {
        'status': 'fail',
        'message': 'Invalid payload.'
    }
    if not post_data:
        return jsonify(response_object), 400

    # TODO: Add the other optional paramaters here
    creator = post_data.get('creator')
    link = post_data.get('link')
    try:
        task = Task.query.filter_by(link=link).first()
        if not task:
            db.session.add(Task(creator=creator, link=link))
            db.session.commit()
            response_object = {
                'status': 'success',
                'message': f'{link} was added!'
            }
            return jsonify(response_object), 201
        else:
            response_object['message'] = 'Sorry. That link already exists.'
            return jsonify(response_object), 400
    except exc.IntegrityError:
        db.session.rollback()
        return jsonify(response_object), 400


@tasks_blueprint.route('/tasks/<task_id>', methods=['GET'])
def get_single_task(task_id):
    response_object = {
        'status': 'fail',
        'message': 'task does not exist'
    }
    try:
        task = Task.query.filter_by(id=int(task_id)).first()
        if not task:
            return jsonify(response_object), 404
        else:
            response_object = {
                'status': 'success',
                'data': {
                    'id': task.id,
                    'link': task.link,
                    'creator': task.creator
                }
            }
            return jsonify(response_object), 200
    except ValueError:
        return jsonify(response_object), 404


@tasks_blueprint.route('/tasks', methods=['GET'])
def get_all_tasks():
    response_object = {
        'status': 'success',
        'data': {
            'tasks': [task.to_json() for task in Task.query.all()]
        }
    }
    return jsonify(response_object), 200



@tasks_blueprint.route('/tasks/init/db', methods=['GET'])
def populate_db():
    all_repos = [
        'sendgrid-nodejs',
        'sendgrid-csharp',
        'sendgrid-php',
        'sendgrid-python',
        'sendgrid-java',
        'sendgrid-go',
        'sendgrid-ruby',
        'smtpapi-nodejs',
        'smtpapi-go',
        'smtpapi-python',
        'smtpapi-php',
        'smtpapi-csharp',
        'smtpapi-java',
        'smtpapi-ruby',
        'sendgrid-oai',
        'open-source-library-data-collector',
        'python-http-client',
        'php-http-client',
        'csharp-http-client',
        'java-http-client',
        'ruby-http-client',
        'rest',
        'nodejs-http-client',
        'dx-automator'
    ]

    response_object = dict()

    # make get request to DX_IP
    # we will have a list of issues for each repo and we will add that to the json response object
    # which is a dictionary
    # issues = {status: success, repo1: [list of issues 1], repo2: [list of issues 2], ...}
    # response_object = {'status' : 'success'}
    client = Client(host="http://{}".format(os.environ.get('DX_IP')))
    for repo in all_repos:
        query_params = {
            "repo":repo,
            "states":"OPEN",
            "filter":"all"
        }
        #TODO: Get the PRs too
        try:
            response_issues = client.github.issues.get(query_params=query_params)
            response_prs = client.github.prs.get(query_params=query_params)
            issues = json.loads(response_issues.body)
            prs = json.loads(response_prs.body)
            issues_and_prs = issues + prs
            response_object[repo] = issues_and_prs
        except Exception as e:
            print(e)

    # post payload to /tasks/init
    for repo in response_object:
        if len(response_object[repo]) != 0:
            for issue in response_object[repo]:
                if issue != None:
                    creator = issue['author']
                    url = issue['url']
                    created_at = issue['createdAt']
                    labels = issue['labels']
                    num_of_comments = issue['comments']
                    num_of_reactions = issue['reactions']
                    title = issue['title']
                    language = repo[9:]
                    try:
                        db.session.add(
                            Task(
                                created_at=created_at,
                                creator=creator,
                                labels=labels,
                                language=language,
                                num_of_comments=num_of_comments,
                                num_of_reactions=num_of_reactions,
                                title=title,
                                url=url
                            )
                        )
                        db.session.commit()
                    except exc.IntegrityError:
                        db.session.rollback()
                        return jsonify(response_object), 400

    return jsonify(response_object), 201