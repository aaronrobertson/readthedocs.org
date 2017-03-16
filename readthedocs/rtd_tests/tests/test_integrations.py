import django_dynamic_fixture as fixture
from django.test import TestCase, RequestFactory
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient
from rest_framework.test import APIRequestFactory
from rest_framework.response import Response

from readthedocs.integrations.models import HttpTransaction
from readthedocs.projects.models import Project


class HttpTransactionTests(TestCase):

    """Test HttpTransaction model by using existing views

    This doesn't mock out a req/resp cycle, as manually creating these outside
    views misses a number of attributes on the request object.
    """

    def test_transaction_json_request_body(self):
        client = APIClient()
        client.login(username='super', password='test')
        project = fixture.get(Project, main_language_project=None)
        resp = client.post(
            '/api/v2/webhook/github/{0}/'.format(project.slug),
            {'ref': 'transaction_json'},
            format='json'
        )
        transaction = HttpTransaction.objects.get(
            content_type=ContentType.objects.filter(
                app_label='projects',
                model='project'
            ),
            object_id=project.pk
        )
        self.assertEqual(
            transaction.request_body,
            '{"ref": "transaction_json"}'
        )
        self.assertEqual(
            transaction.request_headers,
            {u'Content-Type': u'application/json; charset=None',
             u'Cookie': u''}
        )
        self.assertEqual(
            transaction.response_body,
            ('{{"build_triggered": false, "project": "{0}", "versions": []}}'
             .format(project.slug)),
        )
        self.assertEqual(
            transaction.response_headers,
            {u'Allow': u'POST, OPTIONS',
             u'Content-Type': u'text/html; charset=utf-8'}
        )

    def test_transaction_form_request_body(self):
        client = APIClient()
        client.login(username='super', password='test')
        project = fixture.get(Project, main_language_project=None)
        resp = client.post(
            '/api/v2/webhook/github/{0}/'.format(project.slug),
            'payload=%7B%22ref%22%3A+%22transaction_form%22%7D',
            content_type='application/x-www-form-urlencoded',
        )
        transaction = HttpTransaction.objects.get(
            content_type=ContentType.objects.filter(
                app_label='projects',
                model='project'
            ),
            object_id=project.pk
        )
        self.assertEqual(
            transaction.request_body,
            '{"ref": "transaction_form"}'
        )
        self.assertEqual(
            transaction.request_headers,
            {u'Content-Type': u'application/x-www-form-urlencoded',
             u'Cookie': u''}
        )
        self.assertEqual(
            transaction.response_body,
            ('{{"build_triggered": false, "project": "{0}", "versions": []}}'
             .format(project.slug)),
        )
        self.assertEqual(
            transaction.response_headers,
            {u'Allow': u'POST, OPTIONS',
             u'Content-Type': u'text/html; charset=utf-8'}
        )
