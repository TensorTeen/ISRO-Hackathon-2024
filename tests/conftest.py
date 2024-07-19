import pytest
from GeoAwareGPT import Agent


@pytest.fixture(scope="module")
def agent_instance():
    return Agent()
