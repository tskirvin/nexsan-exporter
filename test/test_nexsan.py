import os
from xml.etree import ElementTree

import prometheus_client
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

@pytest.fixture
def registry(request):
    return prometheus_client.CollectorRegistry()

@pytest.mark.xfail
def test_collector_opstats1(datadir, registry):
    with open(os.path.join(datadir, 'opstats1.xml')) as f:
        registry.register(nexsan.Collector(ElementTree.parse(f)))

    body = prometheus_client.generate_latest(registry).split(b'\n')

@pytest.mark.xfail
def test_collector_opstats2(datadir, registry):
    with open(os.path.join(datadir, 'opstats2.xml')) as f:
        registry.register(nexsan.Collector(ElementTree.parse(f)))

    body = prometheus_client.generate_latest(registry).split(b'\n')
