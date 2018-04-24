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
              <blower_rpm id="3" good="yes">4444</blower_rpm>
              <blower_rpm id="4" good="yes">7777</blower_rpm>
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

def test_collector_psu_blower_rpm(nexsan_psu):
    c = nexsan.Collector(nexsan_psu)
    mf = getmf(c.collect(), 'nexsan_env_psu_blower_rpm')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_psu_blower_rpm', {'psu': '2', 'enclosure': '1', 'blower': '3'}, 4444),
        ('nexsan_env_psu_blower_rpm', {'psu': '2', 'enclosure': '1', 'blower': '4'}, 7777),
    ] == mf.samples

def test_collector_psu_blower_good(nexsan_psu):
    nexsan_psu.find('.//psu/blower_rpm[@id="4"]').attrib['good'] = 'no'
    c = nexsan.Collector(nexsan_psu)
    mf = getmf(c.collect(), 'nexsan_env_psu_blower_good')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_psu_blower_good', {'psu': '2', 'enclosure': '1', 'blower': '3'}, 1),
        ('nexsan_env_psu_blower_good', {'psu': '2', 'enclosure': '1', 'blower': '4'}, 0),
    ] == mf.samples

def test_collector_psu_multi():
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

def test_collector_controller_voltage_volts(nexsan_controller):
    c = nexsan.Collector(nexsan_controller)
    mf = getmf(c.collect(), 'nexsan_env_controller_voltage_volts')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_controller_voltage_volts', {'voltage': 'CPU', 'controller': '2', 'enclosure': '1'}, 1.18),
        ('nexsan_env_controller_voltage_volts', {'voltage': '1V0', 'controller': '2', 'enclosure': '1'}, 0.97),
    ] == mf.samples

def test_collector_controller_voltage_good(nexsan_controller):
    nexsan_controller.find('.//controller/voltage[@id="1V0"]').attrib['good'] = 'no'
    c = nexsan.Collector(nexsan_controller)
    mf = getmf(c.collect(), 'nexsan_env_controller_voltage_good')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_controller_voltage_good', {'voltage': 'CPU', 'controller': '2', 'enclosure': '1'}, 1),
        ('nexsan_env_controller_voltage_good', {'voltage': '1V0', 'controller': '2', 'enclosure': '1'}, 0),
    ] == mf.samples

def test_collector_controller_temp_celsius(nexsan_controller):
    c = nexsan.Collector(nexsan_controller)
    mf = getmf(c.collect(), 'nexsan_env_controller_temp_celsius')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_controller_temp_celsius', {'temp': 'PCB', 'controller': '2', 'enclosure': '1'}, 44),
        ('nexsan_env_controller_temp_celsius', {'temp': 'CPU', 'controller': '2', 'enclosure': '1'}, 74),
    ] == mf.samples

def test_collector_controller_temp_good(nexsan_controller):
    nexsan_controller.find('.//controller/temperature_deg_c[@id="CPU"]').attrib['good'] = 'no'
    c = nexsan.Collector(nexsan_controller)
    mf = getmf(c.collect(), 'nexsan_env_controller_temp_good')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_controller_temp_good', {'temp': 'PCB', 'controller': '2', 'enclosure': '1'}, 1),
        ('nexsan_env_controller_temp_good', {'temp': 'CPU', 'controller': '2', 'enclosure': '1'}, 0),
    ] == mf.samples

def test_collector_controller_battery_charge_good_1(nexsan_controller):
    c = nexsan.Collector(nexsan_controller)
    mf = getmf(c.collect(), 'nexsan_env_controller_battery_charge_good')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_controller_battery_charge_good', {'battery': '3', 'controller': '2', 'enclosure': '1'}, 1),
    ] == mf.samples

def test_collector_controller_battery_charge_good_1(nexsan_controller):
    nexsan_controller.find('.//controller/battery[@id="3"]/charge_state').attrib['good'] = 'no'
    c = nexsan.Collector(nexsan_controller)
    mf = getmf(c.collect(), 'nexsan_env_controller_battery_charge_good')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_controller_battery_charge_good', {'battery': '3', 'controller': '2', 'enclosure': '1'}, 0),
    ] == mf.samples

def test_collector_controller_multi():
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

def test_collector_pod_voltage_volts(nexsan_pod):
    c = nexsan.Collector(nexsan_pod)
    mf = getmf(c.collect(), 'nexsan_env_pod_voltage_volts')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_pod_voltage_volts', {'pod': '4', 'enclosure': '5', 'voltage': 'Exp A 1V2'}, 1.2),
        ('nexsan_env_pod_voltage_volts', {'pod': '4', 'enclosure': '5', 'voltage': 'Exp B 1V2'}, 1.3),
    ]

def test_collector_pod_voltage_good(nexsan_pod):
    c = nexsan.Collector(nexsan_pod)
    mf = getmf(c.collect(), 'nexsan_env_pod_voltage_good')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_pod_voltage_good', {'pod': '4', 'enclosure': '5', 'voltage': 'Exp A 1V2'}, 1),
        ('nexsan_env_pod_voltage_good', {'pod': '4', 'enclosure': '5', 'voltage': 'Exp B 1V2'}, 0),
    ] == mf.samples

def test_collector_pod_temp_celsius(nexsan_pod):
    c = nexsan.Collector(nexsan_pod)
    mf = getmf(c.collect(), 'nexsan_env_pod_temp_celsius')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_pod_temp_celsius', {'pod': '4', 'enclosure': '5', 'temp': 'Expander A'}, 61),
        ('nexsan_env_pod_temp_celsius', {'pod': '4', 'enclosure': '5', 'temp': 'Expander B'}, 62),
    ] == mf.samples

def test_collector_pod_temp_good(nexsan_pod):
    c = nexsan.Collector(nexsan_pod)
    mf = getmf(c.collect(), 'nexsan_env_pod_temp_good')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_pod_temp_good', {'pod': '4', 'enclosure': '5', 'temp': 'Expander A'}, 1),
        ('nexsan_env_pod_temp_good', {'pod': '4', 'enclosure': '5', 'temp': 'Expander B'}, 0),
    ] == mf.samples

def test_collector_pod_front_blower_rpm(nexsan_pod):
    c = nexsan.Collector(nexsan_pod)
    mf = getmf(c.collect(), 'nexsan_env_pod_front_blower_rpm')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_pod_front_blower_rpm', {'pod': '4', 'enclosure': '5', 'blower': '3'}, 4163),
        ('nexsan_env_pod_front_blower_rpm', {'pod': '4', 'enclosure': '5', 'blower': '2'}, 4200),
    ] == mf.samples

def test_collector_pod_front_blower_good(nexsan_pod):
    c = nexsan.Collector(nexsan_pod)
    mf = getmf(c.collect(), 'nexsan_env_pod_front_blower_good')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_pod_front_blower_good', {'pod': '4', 'enclosure': '5', 'blower': '3'}, 1),
        ('nexsan_env_pod_front_blower_good', {'pod': '4', 'enclosure': '5', 'blower': '2'}, 0),
    ] == mf.samples

def test_collector_pod_tray_blower_rpm(nexsan_pod):
    c = nexsan.Collector(nexsan_pod)
    mf = getmf(c.collect(), 'nexsan_env_pod_tray_blower_rpm')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_pod_tray_blower_rpm', {'pod': '4', 'enclosure': '5', 'blower': '1'}, 7616),
        ('nexsan_env_pod_tray_blower_rpm', {'pod': '4', 'enclosure': '5', 'blower': '8'}, 13138),
    ] == mf.samples

def test_collector_pod_tray_blower_good(nexsan_pod):
    c = nexsan.Collector(nexsan_pod)
    mf = getmf(c.collect(), 'nexsan_env_pod_tray_blower_good')
    assert 'gauge' == mf.type
    assert [
        ('nexsan_env_pod_tray_blower_good', {'pod': '4', 'enclosure': '5', 'blower': '1'}, 1),
        ('nexsan_env_pod_tray_blower_good', {'pod': '4', 'enclosure': '5', 'blower': '8'}, 0),
    ] == mf.samples


def test_collector_pod_multi():
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
