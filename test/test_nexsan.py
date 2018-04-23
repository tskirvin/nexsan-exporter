import os
from xml.etree import ElementTree

import pytest

from nexsan_exporter import nexsan

@pytest.fixture
def datadir(request):
    '''
    Returns a file-like object for the Collector to consume.
    '''
    filename = request.module.__file__
    test_dir, _ = os.path.splitext(filename)

    assert os.path.isdir(test_dir)
    return test_dir

@pytest.mark.xfail
def test_collector_opstats1(datadir):
    with open(os.path.join(datadir, 'opstats1.xml')) as f:
        metrics = list(nexsan.Collector(ElementTree.parse(f)).collect())
        from pprint import pprint
        pprint(list(m.samples for m in metrics))
        assert [] == metrics

@pytest.mark.xfail
def test_collector_opstats2(datadir):
    with open(os.path.join(datadir, 'opstats2.xml')) as f:
        metrics = list(nexsan.Collector(ElementTree.parse(f)).collect())
        from pprint import pprint
        pprint(list(m.samples for m in metrics))
        assert [] == metrics

def getmf(families, name):
    skipped = []
    for f in families:
        if f.name == name:
            return f
        else:
            skipped.append(f.name)
    raise Exception('Metric family "{}" not found (got {!r})'.format(name, skipped))

@pytest.fixture
def nexsan_sys(request):
    return ElementTree.fromstring('''
        <nexsan_op_status version="2" status="experimental">
          <nexsan_sys_details version="1" status="experimental">
            <friendly_name>nnn</friendly_name>
            <system_name>sss</system_name>
            <system_id>iii</system_id>
            <firmware_version>fff</firmware_version>
            <date human="Tuesday 17-Apr-2018 11:07">1523963221</date>
          </nexsan_sys_details>
        </nexsan_op_status>
    ''')

def test_collector_sys_details(nexsan_sys):
    c = nexsan.Collector(nexsan_sys)
    mf = getmf(c.collect(), 'nexsan_sys_details')
    assert 'untyped' == mf.type
    assert [('nexsan_sys_details', {'firmware_version': 'fff', 'friendly_name': 'nnn', 'system_id': 'iii', 'system_name': 'sss'}, 1)] == mf.samples

def test_collector_sys_date(nexsan_sys):
    c = nexsan.Collector(nexsan_sys)
    mf = getmf(c.collect(), 'nexsan_sys_date')
    assert 'counter' == mf.type
    assert [('nexsan_sys_date', {}, 1523963221)] == mf.samples
