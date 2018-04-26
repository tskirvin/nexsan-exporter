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

@pytest.fixture(params=['opstats1.xml', 'opstats2.xml'])
def opstats_xml(request):
    '''
    Returns a file-like object for the Collector to consume.
    '''
    test_dir, _ = os.path.splitext(request.module.__file__)
    filename = request.param
    with open(os.path.join(test_dir, filename)) as f:
        return ET.parse(f)

def test_opstats(opstats_xml):
    '''
    Tests that real-world data parses.
    '''
    metrics = list(nexsan.Collector(opstats_xml).collect())
    assert 0 < len(metrics)

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

def test_sys_details(nexsan_sys):
    c = nexsan.Collector(nexsan_sys)
    mf = getmf(c.collect(), 'nexsan_sys_details')
    assert 'gauge' == mf.type
    assert [('nexsan_sys_details', {'firmware_version': 'fff', 'friendly_name': 'nnn', 'system_id': 'iii', 'system_name': 'sss'}, 1)] == mf.samples

def test_sys_date(nexsan_sys):
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
              <blower_rpm id="3" good="yes">4444</blower_rpm>
              <blower_rpm id="4" good="yes">7777</blower_rpm>
            </psu>
          </enclosure>
        </nexsan_env_status>
      </nexsan_op_status>
    ''')

def test_psu_power_good_1(nexsan_psu):
    c = nexsan.Collector(nexsan_psu)
    mf = getmf(c.collect(), 'nexsan_env_psu_power_good')
    assert 'gauge' == mf.type
    assert [('nexsan_env_psu_power_good', {'psu': '2', 'enclosure': '1'}, 1)] == mf.samples

def test_psu_power_good_0(nexsan_psu):
    nexsan_psu.find('.//psu/state').attrib['good'] = 'no'
    c = nexsan.Collector(nexsan_psu)
    mf = getmf(c.collect(), 'nexsan_env_psu_power_good')
    assert 'gauge' == mf.type
    assert [('nexsan_env_psu_power_good', {'psu': '2', 'enclosure': '1'}, 0)] == mf.samples

def test_psu_power_watts(nexsan_psu):
    c = nexsan.Collector(nexsan_psu)
    mf = getmf(c.collect(), 'nexsan_env_psu_power_watts')
    assert 'gauge' == mf.type
    assert [('nexsan_env_psu_power_watts', {'psu': '2', 'enclosure': '1'}, 546)] == mf.samples

def test_psu_temp_celsius(nexsan_psu):
    c = nexsan.Collector(nexsan_psu)
    mf = getmf(c.collect(), 'nexsan_env_psu_temp_celsius')
    assert 'gauge' == mf.type
    assert [('nexsan_env_psu_temp_celsius', {'psu': '2', 'enclosure': '1'}, 41)] == mf.samples

def test_psu_temp_good_1(nexsan_psu):
    c = nexsan.Collector(nexsan_psu)
    mf = getmf(c.collect(), 'nexsan_env_psu_temp_good')
    assert 'gauge' == mf.type
    assert [('nexsan_env_psu_temp_good', {'psu': '2', 'enclosure': '1'}, 1)] == mf.samples

def test_psu_temp_good_0(nexsan_psu):
    nexsan_psu.find('.//psu/temperature_deg_c').attrib['good'] = 'no'
    c = nexsan.Collector(nexsan_psu)
    mf = getmf(c.collect(), 'nexsan_env_psu_temp_good')
    assert 'gauge' == mf.type
    assert [('nexsan_env_psu_temp_good', {'psu': '2', 'enclosure': '1'}, 0)] == mf.samples

def test_psu_blower_rpm(nexsan_psu):
    c = nexsan.Collector(nexsan_psu)
    mf = getmf(c.collect(), 'nexsan_env_psu_blower_rpm')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_psu_blower_rpm', {'psu': '2', 'enclosure': '1', 'blower': '3'}, 4444),
        ('nexsan_env_psu_blower_rpm', {'psu': '2', 'enclosure': '1', 'blower': '4'}, 7777),
    ] == mf.samples

def test_psu_blower_good(nexsan_psu):
    nexsan_psu.find('.//psu/blower_rpm[@id="4"]').attrib['good'] = 'no'
    c = nexsan.Collector(nexsan_psu)
    mf = getmf(c.collect(), 'nexsan_env_psu_blower_good')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_psu_blower_good', {'psu': '2', 'enclosure': '1', 'blower': '3'}, 1),
        ('nexsan_env_psu_blower_good', {'psu': '2', 'enclosure': '1', 'blower': '4'}, 0),
    ] == mf.samples

def test_psu_multi():
    nexsan_psu_multi = ET.fromstring('''
      <nexsan_op_status version="2" status="experimental">
        <nexsan_env_status version="3" status="experimental">
          <enclosure id="1">
            <psu id="2">
              <state good="yes" power_watt="546">OK</state>
              <temperature_deg_c good="yes">41</temperature_deg_c>
              <blower_rpm id="3" good="yes">4444</blower_rpm>
            </psu>
            <psu id="9">
              <state good="yes" power_watt="100">OK</state>
              <temperature_deg_c good="yes">41</temperature_deg_c>
              <blower_rpm id="3" good="yes">4444</blower_rpm>
            </psu>
          </enclosure>
        </nexsan_env_status>
      </nexsan_op_status>
    ''')
    c = nexsan.Collector(nexsan_psu_multi)
    mf = getmf(c.collect(), 'nexsan_env_psu_power_good')
    assert [
        ('nexsan_env_psu_power_good', {'psu': '2', 'enclosure': '1'}, 1),
        ('nexsan_env_psu_power_good', {'psu': '9', 'enclosure': '1'}, 1),
    ] == mf.samples

@pytest.fixture
def nexsan_psu_v1(request):
    return ET.fromstring('''
      <nexsan_op_status version="1" status="experimental">
        <nexsan_env_status version="1" status="experimental">
          <psu id="2">
            <state good="yes">OK</state>
            <temperature_deg_c good="yes">41</temperature_deg_c>
            <blower_rpm id="3" good="yes">4444</blower_rpm>
            <blower_rpm id="4" good="yes">7777</blower_rpm>
          </psu>
        </nexsan_env_status>
      </nexsan_op_status>
    ''')

def test_psu_power_good_v1(nexsan_psu_v1):
    c = nexsan.Collector(nexsan_psu_v1)
    mf = getmf(c.collect(), 'nexsan_env_psu_power_good')
    assert 'gauge' == mf.type
    assert [('nexsan_env_psu_power_good', {'psu': '2', 'enclosure': ''}, 1)] == mf.samples

def test_psu_power_watts_v1(nexsan_psu_v1):
    c = nexsan.Collector(nexsan_psu_v1)
    mf = getmf(c.collect(), 'nexsan_env_psu_power_watts')
    assert 'gauge' == mf.type
    assert [] == mf.samples

def test_psu_temp_celsius_v1(nexsan_psu_v1):
    c = nexsan.Collector(nexsan_psu_v1)
    mf = getmf(c.collect(), 'nexsan_env_psu_temp_celsius')
    assert 'gauge' == mf.type
    assert [('nexsan_env_psu_temp_celsius', {'psu': '2', 'enclosure': ''}, 41)] == mf.samples

def test_psu_temp_good_v1(nexsan_psu_v1):
    c = nexsan.Collector(nexsan_psu_v1)
    mf = getmf(c.collect(), 'nexsan_env_psu_temp_good')
    assert 'gauge' == mf.type
    assert [('nexsan_env_psu_temp_good', {'psu': '2', 'enclosure': ''}, 1)] == mf.samples

def test_psu_blower_rpm_v1(nexsan_psu_v1):
    c = nexsan.Collector(nexsan_psu_v1)
    mf = getmf(c.collect(), 'nexsan_env_psu_blower_rpm')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_psu_blower_rpm', {'psu': '2', 'enclosure': '', 'blower': '3'}, 4444),
        ('nexsan_env_psu_blower_rpm', {'psu': '2', 'enclosure': '', 'blower': '4'}, 7777),
    ] == mf.samples

def test_psu_blower_good_v1(nexsan_psu_v1):
    nexsan_psu_v1.find('.//psu/blower_rpm[@id="4"]').attrib['good'] = 'no'
    c = nexsan.Collector(nexsan_psu_v1)
    mf = getmf(c.collect(), 'nexsan_env_psu_blower_good')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_psu_blower_good', {'psu': '2', 'enclosure': '', 'blower': '3'}, 1),
        ('nexsan_env_psu_blower_good', {'psu': '2', 'enclosure': '', 'blower': '4'}, 0),
    ] == mf.samples

def test_psu_temp_celsius_unknown_v1(request):
    nexsan_psu_temp_celsius_unknown_v1 = ET.fromstring('''
      <nexsan_op_status version="1" status="experimental">
        <nexsan_env_status version="1" status="experimental">
          <psu id="2">
            <state good="yes">OK</state>
            <temperature_deg_c good="yes">Unknown</temperature_deg_c>
            <blower_rpm id="3" good="yes">4444</blower_rpm>
          </psu>
        </nexsan_env_status>
      </nexsan_op_status>
    ''')
    c = nexsan.Collector(nexsan_psu_temp_celsius_unknown_v1)
    mf = getmf(c.collect(), 'nexsan_env_psu_temp_celsius')
    assert 'gauge' == mf.type
    assert [] == mf.samples

@pytest.fixture
def nexsan_controller(request):
    return ET.fromstring('''
      <nexsan_op_status version="2" status="experimental">
        <nexsan_env_status version="3" status="experimental">
          <enclosure id="1">
            <controller id="2">
              <voltage id="CPU" good="yes">1.18</voltage>
              <voltage id="1V0" good="yes">0.97</voltage>
              <temperature_deg_c id="PCB" good="yes">44</temperature_deg_c>
              <temperature_deg_c id="CPU" good="yes">74</temperature_deg_c>
              <battery id="3">
                <charge_state good="yes">Fully charged</charge_state>
              </battery>
            </controller>
          </enclosure>
        </nexsan_env_status>
      </nexsan_op_status>
    ''')

def test_controller_voltage_volts(nexsan_controller):
    c = nexsan.Collector(nexsan_controller)
    mf = getmf(c.collect(), 'nexsan_env_controller_voltage_volts')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_controller_voltage_volts', {'voltage': 'CPU', 'controller': '2', 'enclosure': '1'}, 1.18),
        ('nexsan_env_controller_voltage_volts', {'voltage': '1V0', 'controller': '2', 'enclosure': '1'}, 0.97),
    ] == mf.samples

def test_controller_voltage_good(nexsan_controller):
    nexsan_controller.find('.//controller/voltage[@id="1V0"]').attrib['good'] = 'no'
    c = nexsan.Collector(nexsan_controller)
    mf = getmf(c.collect(), 'nexsan_env_controller_voltage_good')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_controller_voltage_good', {'voltage': 'CPU', 'controller': '2', 'enclosure': '1'}, 1),
        ('nexsan_env_controller_voltage_good', {'voltage': '1V0', 'controller': '2', 'enclosure': '1'}, 0),
    ] == mf.samples

def test_controller_temp_celsius(nexsan_controller):
    c = nexsan.Collector(nexsan_controller)
    mf = getmf(c.collect(), 'nexsan_env_controller_temp_celsius')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_controller_temp_celsius', {'temp': 'PCB', 'controller': '2', 'enclosure': '1'}, 44),
        ('nexsan_env_controller_temp_celsius', {'temp': 'CPU', 'controller': '2', 'enclosure': '1'}, 74),
    ] == mf.samples

def test_controller_temp_good(nexsan_controller):
    nexsan_controller.find('.//controller/temperature_deg_c[@id="CPU"]').attrib['good'] = 'no'
    c = nexsan.Collector(nexsan_controller)
    mf = getmf(c.collect(), 'nexsan_env_controller_temp_good')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_controller_temp_good', {'temp': 'PCB', 'controller': '2', 'enclosure': '1'}, 1),
        ('nexsan_env_controller_temp_good', {'temp': 'CPU', 'controller': '2', 'enclosure': '1'}, 0),
    ] == mf.samples

def test_controller_battery_charge_good_1(nexsan_controller):
    c = nexsan.Collector(nexsan_controller)
    mf = getmf(c.collect(), 'nexsan_env_controller_battery_charge_good')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_controller_battery_charge_good', {'battery': '3', 'controller': '2', 'enclosure': '1'}, 1),
    ] == mf.samples

def test_controller_battery_charge_good_0(nexsan_controller):
    nexsan_controller.find('.//controller/battery[@id="3"]/charge_state').attrib['good'] = 'no'
    c = nexsan.Collector(nexsan_controller)
    mf = getmf(c.collect(), 'nexsan_env_controller_battery_charge_good')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_controller_battery_charge_good', {'battery': '3', 'controller': '2', 'enclosure': '1'}, 0),
    ] == mf.samples

def test_controller_multi():
    nexsan_psu_multi = ET.fromstring('''
      <nexsan_op_status version="2" status="experimental">
        <nexsan_env_status version="3" status="experimental">
          <enclosure id="1">
            <controller id="2">
              <voltage id="CPU" good="yes">1.18</voltage>
            </controller>
            <controller id="4">
              <voltage id="CPU" good="yes">3.2</voltage>
            </controller>
          </enclosure>
        </nexsan_env_status>
      </nexsan_op_status>
        ''')
    c = nexsan.Collector(nexsan_psu_multi)
    mf = getmf(c.collect(), 'nexsan_env_controller_voltage_good')
    assert [
        ('nexsan_env_controller_voltage_good', {'controller': '2', 'enclosure': '1', 'voltage': 'CPU'}, 1),
        ('nexsan_env_controller_voltage_good', {'controller': '4', 'enclosure': '1', 'voltage': 'CPU'}, 1),
    ] == mf.samples

@pytest.fixture
def nexsan_controller_v1(request):
    return ET.fromstring('''
      <nexsan_op_status version="1" status="experimental">
        <nexsan_env_status version="1" status="experimental">
            <controller id="2">
            <voltage id="CPU" good="yes">1.18</voltage>
            <voltage id="1V0" good="yes">0.97</voltage>
            <temperature_deg_c good="yes">44</temperature_deg_c>
            <battery id="3">
              <charge_state good="yes">Fully charged</charge_state>
            </battery>
          </controller>
        </nexsan_env_status>
      </nexsan_op_status>
    ''')

def test_controller_voltage_volts_v1(nexsan_controller_v1):
    c = nexsan.Collector(nexsan_controller_v1)
    mf = getmf(c.collect(), 'nexsan_env_controller_voltage_volts')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_controller_voltage_volts', {'voltage': 'CPU', 'controller': '2', 'enclosure': ''}, 1.18),
        ('nexsan_env_controller_voltage_volts', {'voltage': '1V0', 'controller': '2', 'enclosure': ''}, 0.97),
    ] == mf.samples

def test_controller_voltage_good_v1(nexsan_controller_v1):
    nexsan_controller_v1.find('.//controller/voltage[@id="1V0"]').attrib['good'] = 'no'
    c = nexsan.Collector(nexsan_controller_v1)
    mf = getmf(c.collect(), 'nexsan_env_controller_voltage_good')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_controller_voltage_good', {'voltage': 'CPU', 'controller': '2', 'enclosure': ''}, 1),
        ('nexsan_env_controller_voltage_good', {'voltage': '1V0', 'controller': '2', 'enclosure': ''}, 0),
    ] == mf.samples

def test_controller_temp_celsius_v1(nexsan_controller_v1):
    c = nexsan.Collector(nexsan_controller_v1)
    mf = getmf(c.collect(), 'nexsan_env_controller_temp_celsius')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_controller_temp_celsius', {'temp': '', 'controller': '2', 'enclosure': ''}, 44),
    ] == mf.samples

def test_controller_temp_good_1_v1(nexsan_controller_v1):
    c = nexsan.Collector(nexsan_controller_v1)
    mf = getmf(c.collect(), 'nexsan_env_controller_temp_good')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_controller_temp_good', {'temp': '', 'controller': '2', 'enclosure': ''}, 1),
    ] == mf.samples

def test_controller_battery_charge_good_1_v1(nexsan_controller_v1):
    c = nexsan.Collector(nexsan_controller_v1)
    mf = getmf(c.collect(), 'nexsan_env_controller_battery_charge_good')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_controller_battery_charge_good', {'battery': '3', 'controller': '2', 'enclosure': ''}, 1),
    ] == mf.samples

def test_controller_battery_charge_good_1_v1(nexsan_controller_v1):
    nexsan_controller_v1.find('.//controller/battery[@id="3"]/charge_state').attrib['good'] = 'no'
    c = nexsan.Collector(nexsan_controller_v1)
    mf = getmf(c.collect(), 'nexsan_env_controller_battery_charge_good')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_controller_battery_charge_good', {'battery': '3', 'controller': '2', 'enclosure': ''}, 0),
    ] == mf.samples

@pytest.fixture
def nexsan_pod():
    return ET.fromstring('''
      <nexsan_op_status version="2" status="experimental">
        <nexsan_env_status version="3" status="experimental">
          <enclosure id="5">
            <pod id="4">
              <voltage id="Exp A 1V2" good="yes">1.20</voltage>
              <voltage id="Exp B 1V2" good="no">1.30</voltage>
              <temperature_deg_c id="Expander A" good="yes">61</temperature_deg_c>
              <temperature_deg_c id="Expander B" good="no">62</temperature_deg_c>
              <front_panel>
                <blower_rpm id="3" good="yes">4163</blower_rpm>
                <blower_rpm id="2" good="no">4200</blower_rpm>
              </front_panel>
              <fan_tray>
                <blower_rpm id="1" good="yes">7616</blower_rpm>
                <blower_rpm id="8" good="no">13138</blower_rpm>
              </fan_tray>
            </pod>
          </enclosure>
        </nexsan_env_status>
      </nexsan_op_status>
    ''')

def test_pod_voltage_volts(nexsan_pod):
    c = nexsan.Collector(nexsan_pod)
    mf = getmf(c.collect(), 'nexsan_env_pod_voltage_volts')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_pod_voltage_volts', {'pod': '4', 'enclosure': '5', 'voltage': 'Exp A 1V2'}, 1.2),
        ('nexsan_env_pod_voltage_volts', {'pod': '4', 'enclosure': '5', 'voltage': 'Exp B 1V2'}, 1.3),
    ]

def test_pod_voltage_good(nexsan_pod):
    c = nexsan.Collector(nexsan_pod)
    mf = getmf(c.collect(), 'nexsan_env_pod_voltage_good')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_pod_voltage_good', {'pod': '4', 'enclosure': '5', 'voltage': 'Exp A 1V2'}, 1),
        ('nexsan_env_pod_voltage_good', {'pod': '4', 'enclosure': '5', 'voltage': 'Exp B 1V2'}, 0),
    ] == mf.samples

def test_pod_temp_celsius(nexsan_pod):
    c = nexsan.Collector(nexsan_pod)
    mf = getmf(c.collect(), 'nexsan_env_pod_temp_celsius')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_pod_temp_celsius', {'pod': '4', 'enclosure': '5', 'temp': 'Expander A'}, 61),
        ('nexsan_env_pod_temp_celsius', {'pod': '4', 'enclosure': '5', 'temp': 'Expander B'}, 62),
    ] == mf.samples

def test_pod_temp_good(nexsan_pod):
    c = nexsan.Collector(nexsan_pod)
    mf = getmf(c.collect(), 'nexsan_env_pod_temp_good')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_pod_temp_good', {'pod': '4', 'enclosure': '5', 'temp': 'Expander A'}, 1),
        ('nexsan_env_pod_temp_good', {'pod': '4', 'enclosure': '5', 'temp': 'Expander B'}, 0),
    ] == mf.samples

def test_pod_front_blower_rpm(nexsan_pod):
    c = nexsan.Collector(nexsan_pod)
    mf = getmf(c.collect(), 'nexsan_env_pod_front_blower_rpm')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_pod_front_blower_rpm', {'pod': '4', 'enclosure': '5', 'blower': '3'}, 4163),
        ('nexsan_env_pod_front_blower_rpm', {'pod': '4', 'enclosure': '5', 'blower': '2'}, 4200),
    ] == mf.samples

def test_pod_front_blower_good(nexsan_pod):
    c = nexsan.Collector(nexsan_pod)
    mf = getmf(c.collect(), 'nexsan_env_pod_front_blower_good')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_pod_front_blower_good', {'pod': '4', 'enclosure': '5', 'blower': '3'}, 1),
        ('nexsan_env_pod_front_blower_good', {'pod': '4', 'enclosure': '5', 'blower': '2'}, 0),
    ] == mf.samples

def test_pod_tray_blower_rpm(nexsan_pod):
    c = nexsan.Collector(nexsan_pod)
    mf = getmf(c.collect(), 'nexsan_env_pod_tray_blower_rpm')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_pod_tray_blower_rpm', {'pod': '4', 'enclosure': '5', 'blower': '1'}, 7616),
        ('nexsan_env_pod_tray_blower_rpm', {'pod': '4', 'enclosure': '5', 'blower': '8'}, 13138),
    ] == mf.samples

def test_pod_tray_blower_good(nexsan_pod):
    c = nexsan.Collector(nexsan_pod)
    mf = getmf(c.collect(), 'nexsan_env_pod_tray_blower_good')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_pod_tray_blower_good', {'pod': '4', 'enclosure': '5', 'blower': '1'}, 1),
        ('nexsan_env_pod_tray_blower_good', {'pod': '4', 'enclosure': '5', 'blower': '8'}, 0),
    ] == mf.samples


def test_pod_multi():
    nexsan_psu_multi = ET.fromstring('''
      <nexsan_op_status version="2" status="experimental">
        <nexsan_env_status version="3" status="experimental">
          <enclosure id="5">
            <pod id="4">
              <voltage id="Exp A 1V2" good="yes">1.20</voltage>
            </pod>
            <pod id="5">
              <voltage id="Exp A 1V2" good="yes">1.20</voltage>
            </pod>
          </enclosure>
        </nexsan_env_status>
      </nexsan_op_status>
        ''')
    c = nexsan.Collector(nexsan_psu_multi)
    mf = getmf(c.collect(), 'nexsan_env_pod_voltage_good')
    assert [
        ('nexsan_env_pod_voltage_good', {'pod': '4', 'enclosure': '5', 'voltage': 'Exp A 1V2'}, 1),
        ('nexsan_env_pod_voltage_good', {'pod': '5', 'enclosure': '5', 'voltage': 'Exp A 1V2'}, 1),
    ] == mf.samples

@pytest.fixture
def nexsan_volume(request):
    return ET.fromstring('''
      <nexsan_op_status version="2" status="experimental">
        <nexsan_volume_stats version="1" status="experimental">
          <volume id="1" name="v1" array="1" serial_number="0xA1B2C3D4">
            <path init_ident="WWPN: 20-00-A1-B2-C3-1E-BD-E0" target_id="1" lun="1">
              <total_ios>42</total_ios>
              <read_ios>0</read_ios>
              <write_ios>20</write_ios>
              <read_blocks>0</read_blocks>
              <write_blocks>160</write_blocks>
            </path>
            <path init_ident="WWPN: 20-00-A1-B2-C3-1E-C1-B0" target_id="0" lun="1">
              <total_ios>9445479</total_ios>
              <read_ios>4327880</read_ios>
              <write_ios>5117461</write_ios>
              <read_blocks>2782976761</read_blocks>
              <write_blocks>502621356</write_blocks>
            </path>
          </volume>
          <volume id="2" name="v2" array="2" serial_number="0xE5F6A7B8">
            <path init_ident="WWPN: 20-00-A1-B2-C3-1E-BD-E1" target_id="13" lun="2">
              <total_ios>271860997</total_ios>
              <read_ios>1798</read_ios>
              <write_ios>271857933</write_ios>
              <read_blocks>1928</read_blocks>
              <write_blocks>34797781261</write_blocks>
            </path>
            <path init_ident="WWPN: 20-00-A1-B2-C3-1E-C1-B1" target_id="2" lun="2">
              <total_ios>79</total_ios>
              <read_ios>1</read_ios>
              <write_ios>9</write_ios>
              <read_blocks>17</read_blocks>
              <write_blocks>314</write_blocks>
            </path>
          </volume>
        </nexsan_volume_stats>
      </nexsan_op_status>
      ''')

def test_volume_ios_total(nexsan_volume):
    c = nexsan.Collector(nexsan_volume)
    mf = getmf(c.collect(), 'nexsan_volume_ios_total')
    assert 'counter' == mf.type
    assert [
        ('nexsan_volume_ios_total', {'volume': '1', 'name': 'v1', 'array': '1', 'serial': '0xA1B2C3D4', 'ident': 'WWPN: 20-00-A1-B2-C3-1E-BD-E0', 'target': '1', 'lun': '1'}, 42),
        ('nexsan_volume_ios_total', {'volume': '1', 'name': 'v1', 'array': '1', 'serial': '0xA1B2C3D4', 'ident': 'WWPN: 20-00-A1-B2-C3-1E-C1-B0', 'target': '0', 'lun': '1'}, 9445479),
        ('nexsan_volume_ios_total', {'volume': '2', 'name': 'v2', 'array': '2', 'serial': '0xE5F6A7B8', 'ident': 'WWPN: 20-00-A1-B2-C3-1E-BD-E1', 'target': '13', 'lun': '2'}, 271860997),
        ('nexsan_volume_ios_total', {'volume': '2', 'name': 'v2', 'array': '2', 'serial': '0xE5F6A7B8', 'ident': 'WWPN: 20-00-A1-B2-C3-1E-C1-B1', 'target': '2', 'lun': '2'}, 79),
    ] == mf.samples

def test_volume_ios_read_total(nexsan_volume):
    c = nexsan.Collector(nexsan_volume)
    mf = getmf(c.collect(), 'nexsan_volume_ios_read_total')
    assert 'counter' == mf.type
    assert [
        ('nexsan_volume_ios_read_total', {'volume': '1', 'name': 'v1', 'array': '1', 'serial': '0xA1B2C3D4', 'ident': 'WWPN: 20-00-A1-B2-C3-1E-BD-E0', 'target': '1', 'lun': '1'}, 0),
        ('nexsan_volume_ios_read_total', {'volume': '1', 'name': 'v1', 'array': '1', 'serial': '0xA1B2C3D4', 'ident': 'WWPN: 20-00-A1-B2-C3-1E-C1-B0', 'target': '0', 'lun': '1'}, 4327880),
        ('nexsan_volume_ios_read_total', {'volume': '2', 'name': 'v2', 'array': '2', 'serial': '0xE5F6A7B8', 'ident': 'WWPN: 20-00-A1-B2-C3-1E-BD-E1', 'target': '13', 'lun': '2'}, 1798),
        ('nexsan_volume_ios_read_total', {'volume': '2', 'name': 'v2', 'array': '2', 'serial': '0xE5F6A7B8', 'ident': 'WWPN: 20-00-A1-B2-C3-1E-C1-B1', 'target': '2', 'lun': '2'}, 1),
    ] == mf.samples

def test_volume_ios_write_total(nexsan_volume):
    c = nexsan.Collector(nexsan_volume)
    mf = getmf(c.collect(), 'nexsan_volume_ios_write_total')
    assert 'counter' == mf.type
    assert [
        ('nexsan_volume_ios_write_total', {'volume': '1', 'name': 'v1', 'array': '1', 'serial': '0xA1B2C3D4', 'ident': 'WWPN: 20-00-A1-B2-C3-1E-BD-E0', 'target': '1', 'lun': '1'}, 20),
        ('nexsan_volume_ios_write_total', {'volume': '1', 'name': 'v1', 'array': '1', 'serial': '0xA1B2C3D4', 'ident': 'WWPN: 20-00-A1-B2-C3-1E-C1-B0', 'target': '0', 'lun': '1'}, 5117461),
        ('nexsan_volume_ios_write_total', {'volume': '2', 'name': 'v2', 'array': '2', 'serial': '0xE5F6A7B8', 'ident': 'WWPN: 20-00-A1-B2-C3-1E-BD-E1', 'target': '13', 'lun': '2'}, 271857933),
        ('nexsan_volume_ios_write_total', {'volume': '2', 'name': 'v2', 'array': '2', 'serial': '0xE5F6A7B8', 'ident': 'WWPN: 20-00-A1-B2-C3-1E-C1-B1', 'target': '2', 'lun': '2'}, 9),
    ] == mf.samples

def test_volume_blocks_read_total(nexsan_volume):
    c = nexsan.Collector(nexsan_volume)
    mf = getmf(c.collect(), 'nexsan_volume_blocks_read_total')
    assert 'counter' == mf.type
    assert [
        ('nexsan_volume_blocks_read_total', {'volume': '1', 'name': 'v1', 'array': '1', 'serial': '0xA1B2C3D4', 'ident': 'WWPN: 20-00-A1-B2-C3-1E-BD-E0', 'target': '1', 'lun': '1'}, 0),
        ('nexsan_volume_blocks_read_total', {'volume': '1', 'name': 'v1', 'array': '1', 'serial': '0xA1B2C3D4', 'ident': 'WWPN: 20-00-A1-B2-C3-1E-C1-B0', 'target': '0', 'lun': '1'}, 2782976761),
        ('nexsan_volume_blocks_read_total', {'volume': '2', 'name': 'v2', 'array': '2', 'serial': '0xE5F6A7B8', 'ident': 'WWPN: 20-00-A1-B2-C3-1E-BD-E1', 'target': '13', 'lun': '2'}, 1928),
        ('nexsan_volume_blocks_read_total', {'volume': '2', 'name': 'v2', 'array': '2', 'serial': '0xE5F6A7B8', 'ident': 'WWPN: 20-00-A1-B2-C3-1E-C1-B1', 'target': '2', 'lun': '2'}, 17),
    ] == mf.samples

def test_volume_blocks_write_total(nexsan_volume):
    c = nexsan.Collector(nexsan_volume)
    mf = getmf(c.collect(), 'nexsan_volume_blocks_write_total')
    assert 'counter' == mf.type
    assert [
        ('nexsan_volume_blocks_write_total', {'volume': '1', 'name': 'v1', 'array': '1', 'serial': '0xA1B2C3D4', 'ident': 'WWPN: 20-00-A1-B2-C3-1E-BD-E0', 'target': '1', 'lun': '1'}, 160),
        ('nexsan_volume_blocks_write_total', {'volume': '1', 'name': 'v1', 'array': '1', 'serial': '0xA1B2C3D4', 'ident': 'WWPN: 20-00-A1-B2-C3-1E-C1-B0', 'target': '0', 'lun': '1'}, 502621356),
        ('nexsan_volume_blocks_write_total', {'volume': '2', 'name': 'v2', 'array': '2', 'serial': '0xE5F6A7B8', 'ident': 'WWPN: 20-00-A1-B2-C3-1E-BD-E1', 'target': '13', 'lun': '2'}, 34797781261),
        ('nexsan_volume_blocks_write_total', {'volume': '2', 'name': 'v2', 'array': '2', 'serial': '0xE5F6A7B8', 'ident': 'WWPN: 20-00-A1-B2-C3-1E-C1-B1', 'target': '2', 'lun': '2'}, 314),
    ] == mf.samples

def test_volume_weird(request):
    nexsan_volume_weird = ET.fromstring('''
      <nexsan_op_status version="2" status="experimental">
        <nexsan_volume_stats version="1" status="experimental">
          <volume id="209" name="###SNAPDATA###" array="24" serial_number="0x70C09A20"></volume>
        </nexsan_volume_stats>
      </nexsan_op_status>
    ''')
    c = nexsan.Collector(nexsan_volume_weird)
    for mf in c.collect():
        assert [] == mf.samples

@pytest.fixture
def nexsan_perf(request):
    return ET.fromstring('''
      <nexsan_op_status version="2" status="experimental">
        <nexsan_perf_status version="2" status="experimental">
          <controller id="2">
            <cpu_percent>16</cpu_percent>
            <memory_percent>38</memory_percent>
            <port name="Fibre - Host0">
              <read_mbytes_per_sec>76</read_mbytes_per_sec>
              <write_mbytes_per_sec>10</write_mbytes_per_sec>
              <read_ios>2483933528</read_ios>
              <write_ios>2118181371</write_ios>
              <read_blocks>1511750808555</read_blocks>
              <write_blocks>265523917855</write_blocks>
              <port_resets>2</port_resets>
              <lun_resets>17</lun_resets>
              <!-- t 2 -->
              <link_errors>
                <link_error id="0" error_name="link_failure" count="3"/>
                <link_error id="1" error_name="loss_of_sync" count="4"/>
                <link_error id="2" error_name="loss_of_signal" count="5"/>
                <link_error id="3" error_name="primitive_seq_errs" count="6"/>
                <link_error id="4" error_name="invalid_tx_words" count="7"/>
                <link_error id="5" error_name="invalid_tx_crcs" count="8"/>
                <link_error id="6" error_name="discarded_frames" count="9"/>
                <link_error id="7" error_name="fw_dropped_frames" count="10"/>
              </link_errors>
            </port>
            <port name="Fibre - Host1">
              <read_mbytes_per_sec>77</read_mbytes_per_sec>
              <write_mbytes_per_sec>12</write_mbytes_per_sec>
              <read_ios>2090888411</read_ios>
              <write_ios>1644606275</write_ios>
              <read_blocks>1291215959784</read_blocks>
              <write_blocks>203110373427</write_blocks>
              <port_resets>4</port_resets>
              <lun_resets>3</lun_resets>
              <!-- t 2 -->
              <link_errors>
                <link_error id="0" error_name="link_failure" count="10"/>
                <link_error id="1" error_name="loss_of_sync" count="9"/>
                <link_error id="2" error_name="loss_of_signal" count="8"/>
                <link_error id="3" error_name="primitive_seq_errs" count="7"/>
                <link_error id="4" error_name="invalid_tx_words" count="6"/>
                <link_error id="5" error_name="invalid_tx_crcs" count="5"/>
                <link_error id="6" error_name="discarded_frames" count="4"/>
                <link_error id="7" error_name="fw_dropped_frames" count="3"/>
              </link_errors>
            </port>
          </controller>
          <array name="array1">
            <owner>1</owner>
            <load_percent>18</load_percent>
          </array>
          <array name="array2">
            <owner>0</owner>
            <load_percent>16</load_percent>
          </array>
        </nexsan_perf_status>
      </nexsan_op_status>
    ''')

def test_perf_cpu_usage_ratio(nexsan_perf):
    c = nexsan.Collector(nexsan_perf)
    mf = getmf(c.collect(), 'nexsan_perf_cpu_usage_percent')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_perf_cpu_usage_percent', {'controller': '2'}, 16)
    ] == mf.samples

def test_perf_memory_usage_ratio(nexsan_perf):
    c = nexsan.Collector(nexsan_perf)
    mf = getmf(c.collect(), 'nexsan_perf_memory_usage_percent')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_perf_memory_usage_percent', {'controller': '2'}, 38)
    ] == mf.samples

def test_perf_read_bytes_per_second(nexsan_perf):
    c = nexsan.Collector(nexsan_perf)
    mf = getmf(c.collect(), 'nexsan_perf_read_bytes_per_second')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_perf_read_bytes_per_second', {'controller': '2', 'port': 'Fibre - Host0'}, 76 * 1024 * 1024),
        ('nexsan_perf_read_bytes_per_second', {'controller': '2', 'port': 'Fibre - Host1'}, 77 * 1024 * 1024),

    ] == mf.samples

def test_perf_write_bytes_per_second(nexsan_perf):
    c = nexsan.Collector(nexsan_perf)
    mf = getmf(c.collect(), 'nexsan_perf_write_bytes_per_second')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_perf_write_bytes_per_second', {'controller': '2', 'port': 'Fibre - Host0'}, 10 * 1024 * 1024),
        ('nexsan_perf_write_bytes_per_second', {'controller': '2', 'port': 'Fibre - Host1'}, 12 * 1024 * 1024),
    ] == mf.samples

def test_perf_read_ios_total(nexsan_perf):
    c = nexsan.Collector(nexsan_perf)
    mf = getmf(c.collect(), 'nexsan_perf_read_ios_total')
    assert 'counter' == mf.type
    assert [
        ('nexsan_perf_read_ios_total', {'controller': '2', 'port': 'Fibre - Host0'}, 2483933528),
        ('nexsan_perf_read_ios_total', {'controller': '2', 'port': 'Fibre - Host1'}, 2090888411),
    ] == mf.samples

def test_perf_write_ios_total(nexsan_perf):
    c = nexsan.Collector(nexsan_perf)
    mf = getmf(c.collect(), 'nexsan_perf_write_ios_total')
    assert 'counter' == mf.type
    assert [
        ('nexsan_perf_write_ios_total', {'controller': '2', 'port': 'Fibre - Host0'}, 2118181371),
        ('nexsan_perf_write_ios_total', {'controller': '2', 'port': 'Fibre - Host1'}, 1644606275),
    ] == mf.samples

def test_perf_read_blocks_total(nexsan_perf):
    c = nexsan.Collector(nexsan_perf)
    mf = getmf(c.collect(), 'nexsan_perf_read_blocks_total')
    assert 'counter' == mf.type
    assert [
        ('nexsan_perf_read_blocks_total', {'controller': '2', 'port': 'Fibre - Host0'}, 1511750808555),
        ('nexsan_perf_read_blocks_total', {'controller': '2', 'port': 'Fibre - Host1'}, 1291215959784),
    ] == mf.samples

def test_perf_write_blocks_total(nexsan_perf):
    c = nexsan.Collector(nexsan_perf)
    mf = getmf(c.collect(), 'nexsan_perf_write_blocks_total')
    assert 'counter' == mf.type
    assert [
        ('nexsan_perf_write_blocks_total', {'controller': '2', 'port': 'Fibre - Host0'}, 265523917855),
        ('nexsan_perf_write_blocks_total', {'controller': '2', 'port': 'Fibre - Host1'}, 203110373427),
    ] == mf.samples

def test_perf_port_resets_total(nexsan_perf):
    c = nexsan.Collector(nexsan_perf)
    mf = getmf(c.collect(), 'nexsan_perf_port_resets_total')
    assert 'counter' == mf.type
    assert [
        ('nexsan_perf_port_resets_total', {'controller': '2', 'port': 'Fibre - Host0'}, 2),
        ('nexsan_perf_port_resets_total', {'controller': '2', 'port': 'Fibre - Host1'}, 4),
    ] == mf.samples

def test_perf_lun_resets_total(nexsan_perf):
    c = nexsan.Collector(nexsan_perf)
    mf = getmf(c.collect(), 'nexsan_perf_lun_resets_total')
    assert 'counter' == mf.type
    assert [
        ('nexsan_perf_lun_resets_total', {'controller': '2', 'port': 'Fibre - Host0'}, 17),
        ('nexsan_perf_lun_resets_total', {'controller': '2', 'port': 'Fibre - Host1'}, 3),
    ] == mf.samples

def test_perf_link_errors_total(nexsan_perf):
    c = nexsan.Collector(nexsan_perf)
    mf = getmf(c.collect(), 'nexsan_perf_link_errors_total')
    assert 'counter' == mf.type
    assert [
        ('nexsan_perf_link_errors_total', {'controller': '2', 'port': 'Fibre - Host0', 'name': 'link_failure'}, 3),
        ('nexsan_perf_link_errors_total', {'controller': '2', 'port': 'Fibre - Host0', 'name': 'loss_of_sync'}, 4),
        ('nexsan_perf_link_errors_total', {'controller': '2', 'port': 'Fibre - Host0', 'name': 'loss_of_signal'}, 5),
        ('nexsan_perf_link_errors_total', {'controller': '2', 'port': 'Fibre - Host0', 'name': 'primitive_seq_errs'}, 6),
        ('nexsan_perf_link_errors_total', {'controller': '2', 'port': 'Fibre - Host0', 'name': 'invalid_tx_words'}, 7),
        ('nexsan_perf_link_errors_total', {'controller': '2', 'port': 'Fibre - Host0', 'name': 'invalid_tx_crcs'}, 8),
        ('nexsan_perf_link_errors_total', {'controller': '2', 'port': 'Fibre - Host0', 'name': 'discarded_frames'}, 9),
        ('nexsan_perf_link_errors_total', {'controller': '2', 'port': 'Fibre - Host0', 'name': 'fw_dropped_frames'}, 10),
        ('nexsan_perf_link_errors_total', {'controller': '2', 'port': 'Fibre - Host1', 'name': 'link_failure'}, 10),
        ('nexsan_perf_link_errors_total', {'controller': '2', 'port': 'Fibre - Host1', 'name': 'loss_of_sync'}, 9),
        ('nexsan_perf_link_errors_total', {'controller': '2', 'port': 'Fibre - Host1', 'name': 'loss_of_signal'}, 8),
        ('nexsan_perf_link_errors_total', {'controller': '2', 'port': 'Fibre - Host1', 'name': 'primitive_seq_errs'}, 7),
        ('nexsan_perf_link_errors_total', {'controller': '2', 'port': 'Fibre - Host1', 'name': 'invalid_tx_words'}, 6),
        ('nexsan_perf_link_errors_total', {'controller': '2', 'port': 'Fibre - Host1', 'name': 'invalid_tx_crcs'}, 5),
        ('nexsan_perf_link_errors_total', {'controller': '2', 'port': 'Fibre - Host1', 'name': 'discarded_frames'}, 4),
        ('nexsan_perf_link_errors_total', {'controller': '2', 'port': 'Fibre - Host1', 'name': 'fw_dropped_frames'}, 3),
    ] == mf.samples

def test_perf_array_load_ratio(nexsan_perf):
    c = nexsan.Collector(nexsan_perf)
    mf = getmf(c.collect(), 'nexsan_perf_load_ratio')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_perf_load_ratio', {'array': 'array1', 'owner': '1'}, 0.18),
        ('nexsan_perf_load_ratio', {'array': 'array2', 'owner': '0'}, 0.16),
    ] == mf.samples

@pytest.fixture
def nexsan_maid(request):
    return ET.fromstring('''
      <nexsan_op_status version="2" status="experimental">
        <nexsan_maid_stats version="2" status="experimental">
          <maid_state>enabled</maid_state>
          <maid_stats_status good="yes">Valid and available</maid_stats_status>
            <maid_group name="g1">
              <active_percent>90</active_percent>
              <idle_percent>80</idle_percent>
              <slow_percent>70</slow_percent>
              <stopped_percent>60</stopped_percent>
              <off_percent>50</off_percent>
              <standby_percent>40</standby_percent>
              <efficiency_percent>30</efficiency_percent>
            </maid_group>
            <maid_group name="g2">
              <active_percent>29</active_percent>
              <idle_percent>28</idle_percent>
              <slow_percent>27</slow_percent>
              <stopped_percent>26</stopped_percent>
              <off_percent>25</off_percent>
              <standby_percent>24</standby_percent>
              <efficiency_percent>23</efficiency_percent>
            </maid_group>
          </nexsan_maid_stats>
        </nexsan_op_status>
      ''')

def test_maid_good_1(nexsan_maid):
    c = nexsan.Collector(nexsan_maid)
    mf = getmf(c.collect(), 'nexsan_maid_good')
    assert 'gauge' == mf.type
    assert [('nexsan_maid_good', {}, 1),] == mf.samples

def test_maid_good_1(nexsan_maid):
    nexsan_maid.find('.//maid_stats_status').attrib['good'] = 'no'
    c = nexsan.Collector(nexsan_maid)
    mf = getmf(c.collect(), 'nexsan_maid_good')
    assert 'gauge' == mf.type
    assert [('nexsan_maid_good', {}, 0),] == mf.samples

def test_maid_active_ratio(nexsan_maid):
    c = nexsan.Collector(nexsan_maid)
    mf = getmf(c.collect(), 'nexsan_maid_active_ratio')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_maid_active_ratio', {'group': 'g1'}, 0.9),
        ('nexsan_maid_active_ratio', {'group': 'g2'}, 0.29),
    ] == mf.samples

def test_maid_idle_ratio(nexsan_maid):
    c = nexsan.Collector(nexsan_maid)
    mf = getmf(c.collect(), 'nexsan_maid_idle_ratio')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_maid_idle_ratio', {'group': 'g1'}, 0.8),
        ('nexsan_maid_idle_ratio', {'group': 'g2'}, 0.28),
    ] == mf.samples

def test_maid_slow_ratio(nexsan_maid):
    c = nexsan.Collector(nexsan_maid)
    mf = getmf(c.collect(), 'nexsan_maid_slow_ratio')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_maid_slow_ratio', {'group': 'g1'}, 0.7),
        ('nexsan_maid_slow_ratio', {'group': 'g2'}, 0.27),
    ] == mf.samples

def test_maid_stopped_ratio(nexsan_maid):
    c = nexsan.Collector(nexsan_maid)
    mf = getmf(c.collect(), 'nexsan_maid_stopped_ratio')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_maid_stopped_ratio', {'group': 'g1'}, 0.6),
        ('nexsan_maid_stopped_ratio', {'group': 'g2'}, 0.26),
    ] == mf.samples

def test_maid_off_ratio(nexsan_maid):
    c = nexsan.Collector(nexsan_maid)
    mf = getmf(c.collect(), 'nexsan_maid_off_ratio')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_maid_off_ratio', {'group': 'g1'}, 0.5),
        ('nexsan_maid_off_ratio', {'group': 'g2'}, 0.25),
    ] == mf.samples

def test_maid_standby_ratio(nexsan_maid):
    c = nexsan.Collector(nexsan_maid)
    mf = getmf(c.collect(), 'nexsan_maid_standby_ratio')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_maid_standby_ratio', {'group': 'g1'}, 0.4),
        ('nexsan_maid_standby_ratio', {'group': 'g2'}, 0.24),
    ] == mf.samples

def test_maid_efficiency_ratio(nexsan_maid):
    c = nexsan.Collector(nexsan_maid)
    mf = getmf(c.collect(), 'nexsan_maid_efficiency_ratio')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_maid_efficiency_ratio', {'group': 'g1'}, 0.3),
        ('nexsan_maid_efficiency_ratio', {'group': 'g2'}, 0.23),
    ] == mf.samples

def test_nexsan_maid_fewer():
    c = nexsan.Collector(ET.fromstring('''
      <nexsan_op_status version="2" status="experimental">
        <nexsan_maid_stats version="2" status="experimental">
          <maid_state>enabled</maid_state>
          <maid_stats_status good="yes">Valid and available</maid_stats_status>
        </nexsan_maid_stats>
        <maid_group name="array3">
          <active_percent>44</active_percent>
          <idle_percent>0</idle_percent>
          <slow_percent>1</slow_percent>
          <stopped_percent>55</stopped_percent>
          <off_percent>0</off_percent>
          <efficiency_percent>42</efficiency_percent>
        </maid_group>
      </nexsan_op_status>
    '''))
    # Just check that the missing elements don't cause an error
    list(c.collect())

@pytest.fixture
def probe_server():
    import http.server
    import base64
    class Handler(http.server.BaseHTTPRequestHandler):
        expected = base64.b64encode(b'%b:%b' % (b'testuser', b'testpass')).decode('latin1')

        def do_GET(self):
            auth = self.headers.get('Authorization')
            if auth is None:
                self.unauthorized()
                return
            scheme, value = auth.split()
            if scheme != 'Basic' or value != self.expected:
                self.unauthorized()
                return
            self.authorized()

        def unauthorized(self):
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm="blah"')
            self.end_headers()

        def authorized(self):
            if self.path == '/admin/opstats.asp':
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'<nexsan_op_status version="2" status="experimental"/>')
            else:
                self.send_response(404)
                self.end_headers()

    server = http.server.HTTPServer(('127.0.0.1', 0), Handler)

    import functools
    import threading
    t = threading.Thread(target=functools.partial(server.serve_forever, 1), name='test_probe_server')
    t.start()
    # We need to wait for server to be ready, but there doesn't appear to be a
    # way to do that, so...
    import time
    time.sleep(0.25)

    yield server

    server.shutdown()
    t.join()

def test_probe(probe_server):
    target = '{}:{}'.format(*probe_server.server_address)
    c = nexsan.probe(target, 'testuser', 'testpass')
    assert nexsan.Collector is type(c)
