import pytest
import yaml
import os.path

data = None

@pytest.fixture
def data(qapp):
    with open("./default.yaml") as f:
        data = yaml.load(f, Loader=yaml.Loader)
    return data

def test_initial(data):
    assert 'initial' in data.keys()
    initial = data['initial']
    assert 'name' in initial.keys()
    assert 'type' in initial.keys()
    assert 'url' in initial.keys()
    # assert os.path.isfile(initial['url']), "The file specified for initial.url does not exist."

def test_events(data):
    assert 'events' in data.keys()
    # print(data)
    events = data['events']
    # for event in events:
    #     print(event)

def test_bad1():
    with open("./tests/stubs/bad1.yaml") as f:
        data = yaml.load(f, Loader=yaml.Loader)
    print(data)
