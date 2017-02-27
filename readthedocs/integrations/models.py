"""Integration with external services"""

import json
import uuid

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.safestring import mark_safe
from jsonfield import JSONField
from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import HtmlFormatter


class HttpTransactionManager(models.Manager):

    """HTTP manager methods"""

    def from_transaction(self, req, resp, related_object=None,
                         payload=None):
        """Create object from Django request and response objects

        If an explicit Request ``payload`` is not specified, the payload will be
        determined directly from the Request object. This makes a good effort to
        normalize the data, however we don't enforce that the payload is JSON
        """
        request_payload = payload
        if request_payload is None:
            request_payload = getattr(req, 'data', None)
            if req.content_type != 'application/json':
                # Here, request_body can be a dict or a MergeDict. Probably best
                # to normalize everything first
                try:
                    request_payload = dict(request_payload.items())
                except AttributeError:
                    pass
        try:
            request_body = json.dumps(request_payload, sort_keys=True)
        except TypeError:
            request_body = str(request_payload)
        # This is the rawest form of request header we have, the WSGI
        # headers. HTTP headers are prefixed with `HTTP_`, which we remove,
        # and because the keys are all uppercase, we'll normalize them to
        # title case-y hyphen separated values.
        request_headers = dict(
            (key[5:].title().replace('_', '-'), str(val))
            for (key, val) in req.META.items()
            if key.startswith('HTTP_')
        )
        request_headers['Content-Type'] = req.content_type

        response_payload = resp.data if hasattr(resp, 'data') else resp.content
        try:
            response_body = json.dumps(response_payload, sort_keys=True)
        except TypeError:
            response_body = str(response_payload)
        response_headers = dict(resp.items())

        fields = {
            'status_code': resp.status_code,
            'request_headers': request_headers,
            'request_body': request_body,
            'response_body': response_body,
            'response_headers': response_headers,
        }
        if related_object is not None:
            fields['related_object'] = related_object
        return self.create(**fields)


class HttpTransaction(models.Model):

    """Record an HTTP transaction"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    related_object = GenericForeignKey('content_type', 'object_id')

    date = models.DateTimeField(_('Date'), auto_now_add=True)

    request_headers = JSONField(_('Request headers'), )
    request_body = models.TextField(_('Request body'))

    response_headers = JSONField(_('Request headers'), )
    response_body = models.TextField(_('Response body'))

    status_code = models.IntegerField(_('Status code'))

    objects = HttpTransactionManager()

    def __unicode__(self):
        return _('Transaction {0}').format(self.pk)

    @property
    def failed(self):
        return self.status_code >= 300 or self.status_code < 200

    def formatted_json(self, field):
        """Try to return pretty printed and Pygment highlighted code"""
        value = getattr(self, field) or ''
        try:
            json_value = json.dumps(json.loads(value), sort_keys=True, indent=2)
            formatter = HtmlFormatter()
            html = highlight(json_value, JsonLexer(), formatter)
            return mark_safe(html)
        except (ValueError, TypeError):
            return value

    @property
    def formatted_request_body(self):
        return self.formatted_json('request_body')

    @property
    def formatted_response_body(self):
        return self.formatted_json('response_body')
