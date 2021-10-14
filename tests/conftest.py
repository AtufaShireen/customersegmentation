import yaml
import pytest
import os
import json
@pytest.fixture
def config(config_path="params.yaml"):
    with open(config_path) as yaml_file:
        config = yaml.safe_load(yaml_file)
    return config

@pytest.fixture
def schema_in()