import os
from xml.etree import ElementTree as ET

import pytest

from nexsan_exporter import nexsan

def test_attrib_good():
    elem = ET.Element('a')
    elem.attrib['good'] = 'yes'
    c = nexsan.Collector(elem)
    assert 1 == c.isgood(elem)

def test_attrib_bad():
    elem = ET.Element('a')
    elem.attrib['good'] = 'no'
    c = nexsan.Collector(elem)
    assert 0 == c.isgood(elem)

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
        metrics = list(nexsan.Collector(ET.parse(f)).collect())
        from pprint import pprint
        pprint(list(m.samples for m in metrics))
        assert [] == metrics

@pytest.mark.xfail
def test_collector_opstats2(datadir):
    with open(os.path.join(datadir, 'opstats2.xml')) as f:
        metrics = list(nexsan.Collector(ET.parse(f)).collect())
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
    return ET.fromstring('''
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

@pytest.fixture
def nexsan_psu(request):
    return ET.fromstring('''
      <nexsan_op_status version="2" status="experimental">
        <nexsan_env_status version="3" status="experimental">
          <enclosure id="1">
            <psu id="2">
              <state good="yes" power_watt="546">OK</state>
              <temperature_deg_c good="yes">41</temperature_deg_c>
              <blower_rpm id="0" good="yes">14438</blower_rpm>
              <blower_rpm id="1" good="yes">14210</blower_rpm>
              <blower_rpm id="2" good="yes">14210</blower_rpm>
              <blower_rpm id="3" good="yes">14210</blower_rpm>
            </psu>
          </enclosure>
        </nexsan_env_status>
      </nexsan_op_status>
    ''')

def test_collector_psu_power_good_1(nexsan_psu):
    c = nexsan.Collector(nexsan_psu)
    mf = getmf(c.collect(), 'nexsan_env_psu_power_good')
    assert 'gauge' == mf.type
    assert [('nexsan_env_psu_power_good', {'psu': '2', 'enclosure': '1'}, 1)] == mf.samples

def test_collector_psu_power_good_0(nexsan_psu):
    nexsan_psu.find('.//psu/state').attrib['good'] = 'no'
    c = nexsan.Collector(nexsan_psu)
    mf = getmf(c.collect(), 'nexsan_env_psu_power_good')
    assert 'gauge' == mf.type
    assert [('nexsan_env_psu_power_good', {'psu': '2', 'enclosure': '1'}, 0)] == mf.samples

def test_collector_psu_power_watts(nexsan_psu):
    c = nexsan.Collector(nexsan_psu)
    mf = getmf(c.collect(), 'nexsan_env_psu_power_watts')
    assert 'gauge' == mf.type
    assert [('nexsan_env_psu_power_watts', {'psu': '2', 'enclosure': '1'}, 546)] == mf.samples

def test_collector_psu_temp_celsius(nexsan_psu):
    c = nexsan.Collector(nexsan_psu)
    mf = getmf(c.collect(), 'nexsan_env_psu_temp_celsius')
    assert 'gauge' == mf.type
    assert [('nexsan_env_psu_temp_celsius', {'psu': '2', 'enclosure': '1'}, 41)] == mf.samples

def test_collector_psu_temp_good_1(nexsan_psu):
    c = nexsan.Collector(nexsan_psu)
    mf = getmf(c.collect(), 'nexsan_env_psu_temp_good')
    assert 'gauge' == mf.type
    assert [('nexsan_env_psu_temp_good', {'psu': '2', 'enclosure': '1'}, 1)] == mf.samples

def test_collector_psu_temp_good_0(nexsan_psu):
    nexsan_psu.find('.//psu/temperature_deg_c').attrib['good'] = 'no'
    c = nexsan.Collector(nexsan_psu)
    mf = getmf(c.collect(), 'nexsan_env_psu_temp_good')
    assert 'gauge' == mf.type
    assert [('nexsan_env_psu_temp_good', {'psu': '2', 'enclosure': '1'}, 0)] == mf.samples

