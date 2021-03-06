#  BSD 3-Clause License
#
#  Copyright (c) 2019, Elasticsearch BV
#  All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#
#  * Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
#  * Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
#  * Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
#  FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
#  DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#  SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#  CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#  OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#  OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import pytest  # isort:skip

flask = pytest.importorskip("flask")  # isort:skip
celery = pytest.importorskip("celery")  # isort:skip

import mock

from elasticapm.conf.constants import ERROR, TRANSACTION

pytestmark = [pytest.mark.celery, pytest.mark.flask]


def test_task_failure(flask_celery):
    apm_client = flask_celery.flask_apm_client.client

    @flask_celery.task()
    def failing_task():
        raise ValueError("foo")

    t = failing_task.delay()
    assert t.status == "FAILURE"
    assert len(apm_client.events[ERROR]) == 1
    error = apm_client.events[ERROR][0]
    assert error["culprit"] == "tests.contrib.celery.flask_tests.failing_task"
    assert error["exception"]["message"] == "ValueError: foo"
    assert error["exception"]["handled"] is False

    transaction = apm_client.events[TRANSACTION][0]
    assert transaction["name"] == "tests.contrib.celery.flask_tests.failing_task"
    assert transaction["type"] == "celery"
    assert transaction["result"] == "FAILURE"
    assert transaction["outcome"] == "failure"


def test_task_instrumentation(flask_celery):
    apm_client = flask_celery.flask_apm_client.client

    @flask_celery.task()
    def successful_task():
        return "OK"

    t = successful_task.delay()

    assert t.status == "SUCCESS"
    assert len(apm_client.events[TRANSACTION]) == 1
    transaction = apm_client.events[TRANSACTION][0]
    assert transaction["name"] == "tests.contrib.celery.flask_tests.successful_task"
    assert transaction["type"] == "celery"
    assert transaction["result"] == "SUCCESS"
    assert transaction["outcome"] == "success"
