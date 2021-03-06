# services/tasks/project/tests/test_tasks.py


import json
import unittest

from flask import current_app
from project import db
from project.api.models import Task
from project.tests.base import BaseTestCase


def add_task(creator,
             url,
             created_at='2019-05-17 00:58:56.285241',
             updated_at='2019-05-17 00:58:56.285241',
             updated_locally_at='2019-05-17 00:58:56.285241',
             language=None,
             labels=None,
             num_of_comments=None,
             num_or_reactions=None,
             rice_total=None
             ):
    task = Task(creator=creator,
                url=url,
                created_at=created_at,
                updated_at=updated_at,
                updated_locally_at=updated_locally_at,
                language=language,
                labels=labels,
                num_of_comments=num_of_comments,
                num_of_reactions=num_or_reactions,
                rice_total=rice_total
                )
    db.session.add(task)
    db.session.commit()
    return task


class TestTaskService(BaseTestCase):
    """Tests for the Tasks Service."""

    def test_tasks(self):
        """Ensure the /ping route behaves correctly."""
        response = self.client.get('/tasks/ping/pong')
        data = json.loads(response.data.decode())
        self.assertEqual(response.status_code, 200)
        self.assertIn('pong!', data['message'])
        self.assertIn('success', data['status'])

    def test_add_single_task(self):
        """Ensure a new task can be added to the database."""
        with self.client:
            response = self.client.post(
                '/tasks',
                data=json.dumps({
                    'creator': 'anshul',
                    'url': 'anshulsinghal.me'
                }),
                content_type='application/json',
            )
            data = json.loads(response.data.decode())
            self.assertEqual(response.status_code, 201)
            self.assertIn('anshulsinghal.me was added!', data['message'])
            self.assertIn('success', data['status'])

    def test_add_task_invalid_json(self):
        """Ensure error is thrown if the JSON object is empty."""
        with self.client:
            response = self.client.post(
                '/tasks',
                data=json.dumps({}),
                content_type='application/json',
            )
            data = json.loads(response.data.decode())
            self.assertEqual(response.status_code, 400)
            self.assertIn('Invalid payload.', data['message'])
            self.assertIn('fail', data['status'])

    def test_add_task_invalid_json_keys(self):
        """
        Ensure error is thrown if the JSON object does not have a taskname key.
        """
        with self.client:
            response = self.client.post(
                '/tasks',
                data=json.dumps({'phone': '999999999'}),
                content_type='application/json',
            )
            data = json.loads(response.data.decode())
            self.assertEqual(response.status_code, 400)
            self.assertIn(current_app.config['ERROR_DB_WRITE_FAILURE'], data['message'])
            self.assertIn('fail', data['status'])

    def test_add_task_duplicate_link(self):
        """Ensure error is thrown if the email already exists."""
        with self.client:
            self.client.post(
                '/tasks',
                data=json.dumps({
                    'creator': 'anshul',
                    'link': 'anshulsinghal.me'
                }),
                content_type='application/json',
            )
            response = self.client.post(
                '/tasks',
                data=json.dumps({
                    'creator': 'anshul',
                    'link': 'anshulsinghal.me'
                }),
                content_type='application/json',
            )
            data = json.loads(response.data.decode())
            self.assertEqual(response.status_code, 400)
            self.assertIn(
                current_app.config['ERROR_DB_WRITE_FAILURE'], data['message'])
            self.assertIn('fail', data['status'])

    def test_single_task(self):
        """Ensure get single task behaves correctly."""
        task = add_task(creator='anshul', url='anshulsinghal.me')
        with self.client:
            response = self.client.get(f'/tasks/{task.id}')
            data = json.loads(response.data.decode())
            self.assertEqual(response.status_code, 200)
            self.assertIn('anshul', data['message']['creator'])
            self.assertIn('anshulsinghal.me', data['message']['url'])
            self.assertIn('success', data['status'])

    def test_single_task_no_id(self):
        """Ensure error is thrown if an id is not provided."""
        with self.client:
            response = self.client.get('/tasks/blah')
            data = json.loads(response.data.decode())
            self.assertEqual(response.status_code, 404)
            self.assertIn('task_id blah does not exist', data['message'])
            self.assertIn('fail', data['status'])

    def test_all_tasks(self):
        """Ensure get all tasks behaves correctly."""
        add_task('anshul', 'anshulsinghal.me')
        add_task('another', 'another.com')
        with self.client:
            response = self.client.get('/tasks')
            data = json.loads(response.data.decode())
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(data['message']['tasks']), 2)
            self.assertIn('anshul', data['message']['tasks'][0]['creator'])
            self.assertIn(
                'anshulsinghal.me', data['message']['tasks'][0]['url'])
            self.assertIn('another', data['message']['tasks'][1]['creator'])
            self.assertIn(
                'another.com', data['message']['tasks'][1]['url'])
            self.assertIn('success', data['status'])

    def test_calculate_rice_score(self):
        task = add_task(
            'thinkingserious',
            'http://twilio.com',
            '2019-05-17 00:58:56.285241',
            '2019-05-17 00:58:56.285241',
            '2019-05-17 00:58:56.285241',
            'python',
            '{"difficulty: medium","status: work in progress","type: community enhancement"}',
            11,
            5
        )
        with self.client:
            query_params = {
                "reach": 2,
                "impact": 2,
                "confidence": 2,
                "effort": 4
            }
            response = self.client.get(f'/tasks/rice/{task.id}', query_string=query_params)
            response = json.loads(response.data.decode())
            task = response['message']
            self.assertEqual(task['rice_total'], 2.0)
    
    def test_calculate_rice_score_with_strings(self):
        task = add_task(
            'thinkingserious',
            'http://twilio.com',
            '2019-05-17 00:58:56.285241',
            '2019-05-17 00:58:56.285241',
            '2019-05-17 00:58:56.285241',
            'python',
            '{"difficulty: medium","status: work in progress","type: community enhancement"}',
            11,
            5
        )
        with self.client:
            query_params = {
                "reach": "2",
                "impact": "2",
                "confidence": "2",
                "effort": "4"
            }
            response = self.client.get(f'/tasks/rice/{task.id}', query_string=query_params)
            response = json.loads(response.data.decode())
            task = response['message']
            self.assertEqual(task['rice_total'], 2.0)    
    
    def test_rice_sorted_list(self):
        add_task(
            'thinkingserious',
            'http://twilio.com',
            '2019-05-17 00:58:56.285241',
            '2019-05-17 00:58:56.285241',
            '2019-05-17 00:58:56.285241',
            'python',
            '{"difficulty: medium","status: work in progress","type: community enhancement"}',
            11,
            5,
            100
        )
        add_task(
            'childish-sambino',
            'http://twilio.com',
            '2019-05-17 00:58:56.285241',
            '2019-05-17 00:58:56.285241',
            '2019-05-17 00:58:56.285241',
            'python',
            '{"difficulty: medium","status: work in progress","type: twilio enhancement"}',
            11,
            5,
            200
        )
        query_params = {
            "page_index": 1,
            "num_results": 2
        }
        response = self.client.get('/tasks/rice', query_string=query_params)
        response = json.loads(response.data.decode())
        tasks = response['message']
        self.assertTrue(tasks[0]['rice_total'] > tasks[1]['rice_total'])

if __name__ == '__main__':
    unittest.main()
