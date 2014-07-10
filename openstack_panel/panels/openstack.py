#!/usr/bin/env python
# -*- coding: utf-8 -*-

import inspect
import functools
import os
import six
import time

from collections import OrderedDict

from django.conf import settings
from django.template.defaultfilters import pluralize
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from debug_toolbar.panels import Panel


def get_class_that_defined_method(meth):
    for cls in inspect.getmro(meth.im_class):
        if meth.__name__ in cls.__dict__:
            return cls
    return None


def get_class_from_frame_values(values):
    args, _, _, value_dict = values
    if len(args) and args[0] == 'self':
        instance = value_dict.get('self', None)
        if instance:
            return getattr(instance, '__class__', None)
    return None


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = \
                super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

    def _drop(self):
        Singleton._instances = {}


class Conf():
    def __init__(self):
        self.PANEL_CONF = getattr(settings,
                                  'DEBUG_TOOLBAR_OPENSTACK_PANEL', None)

    def _get_modules_to_watch(self, var):
        if self.PANEL_CONF:
            return self.PANEL_CONF.get(var, ())
        return tuple()

    @property
    def TRACE_STACK(self):
        if self.PANEL_CONF:
            return self.PANEL_CONF.get('TRACE_STACK', True)
        return True

    @property
    def CLIENTS_LIST(self):
        return self._get_modules_to_watch('OPENSTACK_CLIENTS_LIST')

    @property
    def OTHERS_LIST(self):
        return self._get_modules_to_watch('OPENSTACK_OTHERS_LIST')


class ModulesWatcher(six.with_metaclass(Singleton, object)):
    def __init__(self,
                 clients=('ceilometerclient', 'cinderclient', 'glanceclient',
                          'heatclient', 'keystoneclient', 'neutronclient',
                          'novaclient', 'swiftclient', 'troveclient', ),
                 others=('horizon', 'openstack_dashboard', ),
                 trace_stack=True):
        self._clients = clients
        self._others = others
        self._trace_stack = trace_stack

    def _get_paths(self, lst):
        return tuple(set(
            [os.path.dirname(__import__(module).__file__) for module in lst]
        ))

    @cached_property
    def clients(self):
        return self._get_paths(self._clients)

    @cached_property
    def others(self):
        return self._get_paths(self._others)

    @cached_property
    def clients_and_others(self):
        return self.clients + self.others

    def detect_client_used(self, files):
        for f in files:
            for p in self.clients:
                if f.startswith(p):
                    return p
        return None

    def verify_clients_path(self, path):
        return any([path.startswith(p) for p in self.clients])

    def verify_others_path(self, path):
        return any([path.startswith(p) for p in self.others])

    def verify_path(self, path):
        return any([path.startswith(p) for p in self.clients_and_others])


class RequestsLogger(object):
    def __init__(self, panel, watcher=None):
        self.panel = panel
        self.watcher = watcher
        self.counter = 0
        self.total_time = 0

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            self.counter += 1
            client = 'No information available'
            _stack = []
            files = []
            start = time.time()
            result = func(*args, **kwargs)
            end = time.time()
            time_res = end - start
            time_res_str = "%.2gs" % time_res
            self.total_time += time_res

            try:
                if self.watcher._trace_stack:
                    stack = inspect.stack()[0:]  # exclude current func
                    for item in stack:
                        frame, filename, _, func_name, _, _ = item
                        #TODO(handle traceback correctly)
                        # f_exc_traceback
                        # f_exc_type
                        # f_exc_value
                        if not self.watcher.verify_path(filename):
                            continue
                        values = inspect.getargvalues(frame)
                        klass = get_class_from_frame_values(values)
                        if klass:
                            func_and_signature = '{}.{}{}'.format(
                                klass,
                                func_name,
                                inspect.formatargvalues(*values)
                            )
                        else:
                            func_and_signature = '{}{}'.format(
                                func_name, inspect.formatargvalues(*values))

                        if self.watcher.verify_clients_path(filename):
                            files.append(filename)
                        _stack.append({'file': filename,
                                       'function': func_and_signature})
                    used = self.watcher.detect_client_used(set(files))
                    client = os.path.basename(used) if used else None
                # always requests.Session
                cls = get_class_that_defined_method(func)
                fname = '{cls_mod}.{cls_name}.{func_name}'.format(
                    cls_mod=cls.__module__,
                    cls_name=cls.__name__,
                    func_name=func.__name__)
                collected_data = {'req_number': self.counter,
                                  'time_res': time_res_str,
                                  'func': fname,
                                  'args': args,
                                  'kwargs': kwargs,
                                  'client': client,
                                  'response': result,
                                  'stack': tuple(_stack)}
                self.panel.set_request_info(str(self.counter), collected_data)
                self.panel.set_requests_info_total(
                    {'time': "%.2gs" % self.total_time,
                     'num': str(self.counter)}
                )
            except Exception:
                pass
            return result
        return wrapper


class OpenstackPanel(Panel):
    template = 'openstack_panel/openstack.html'
    title = _("OpenStack")

    def __init__(self, toolbar):
        import requests
        import httplib2
        self.conf = Conf()
        self._requests_info = OrderedDict()
        self._requests_info_total = {}
        self.orig_request_method = requests.Session.request
        self.orig_httplib2_request_method = httplib2.Http.request
        super(OpenstackPanel, self).__init__(toolbar)

    def enable_instrumentation(self):
        import requests
        import httplib2
        watcher = ModulesWatcher(clients=self.conf.CLIENTS_LIST,
                                 others=self.conf.OTHERS_LIST,
                                 trace_stack=self.conf.TRACE_STACK)
        requests_logger = RequestsLogger(self, watcher=watcher)
        _request = requests_logger(requests.Session.request)
        _httplib2_request = requests_logger(requests.Session.request)
        requests.Session.request = _request
        httplib2.Http.request = _httplib2_request

    def disable_instrumentation(self):
        import requests
        import httplib2
        requests.Session.request = self.orig_request_method
        httplib2.Http.request = self.orig_httplib2_request_method

    @property
    def nav_subtitle(self):
        req_count = len(self._requests_info)
        return _("{} request{}".format(req_count, pluralize(req_count)))

    def set_request_info(self, k, v):
        self._requests_info[k] = v

    def set_requests_info_total(self, d):
        self._requests_info_total = d

    def process_response(self, request, response):
        self.record_stats({'info': self._requests_info,
                           'total': self._requests_info_total})
