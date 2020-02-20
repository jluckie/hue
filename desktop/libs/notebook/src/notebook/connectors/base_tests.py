#!/usr/bin/env python
## -*- coding: utf-8 -*-
# Licensed to Cloudera, Inc. under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  Cloudera, Inc. licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from builtins import object
import json
import sys

from nose.tools import assert_equal, assert_true, assert_false

from django.urls import reverse

from desktop.lib.django_test_util import make_logged_in_client
from useradmin.models import User

from notebook.connectors.base import Notebook

if sys.version_info[0] > 2:
  from unittest.mock import patch, Mock, MagicMock
else:
  from mock import patch, Mock, MagicMock


class TestNotebook(object):

  def setUp(self):
    self.client = make_logged_in_client(username="test", groupname="empty", recreate=True, is_superuser=False)
    self.user = User.objects.get(username="test")


  def test_execute_and_wait(self):
    query = Notebook()

    query.execute = Mock(return_value={'history_uuid': 1})
    query.check_status = Mock(
      side_effect=check_status_side_effect
    )
    request=Mock()

    resp = query.execute_and_wait(request=request)
    assert_equal(1, resp['uuid'])
    assert_equal(2, query.check_status.call_count)


  def test_check_status(self):
    query = Notebook()

    notebook = MagicMock()
    def notebook_side_effect(key):
      if key == 'type':
        return 'query-hive'
      elif key == 'uuid':
        return 'uuid-1'
      else:
        return Mock()
    notebook.__getitem__.side_effect = notebook_side_effect
    snippet = MagicMock()
    def snippet_side_effect(key):
      if key == 'status':
        return 0
      else:
        return Mock()
    snippet.__getitem__.side_effect = snippet_side_effect
    request=Mock()

    with patch('notebook.api.Document2.objects.get_by_uuid') as get_by_uuid:
      with patch('notebook.api.get_api') as get_api:
        with patch('notebook.api.Notebook') as Notebook2:
          get_api.return_value=Mock(
            check_status=Mock(return_value={'status': 0})
          )
          resp = query.check_status(request=request, notebook=notebook, snippet=snippet)

          assert_equal(0, resp['status'])
          assert_equal(0, resp['query_status']['status'])


iteration = 0
def check_status_side_effect(request, snippet):
  """First time query is still running, second time the execution is finished."""
  global iteration

  if iteration == 0:
    iteration += 1
    return {'status': 'running'}
  else:
    return {'status': 'done'}
