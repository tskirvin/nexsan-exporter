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
