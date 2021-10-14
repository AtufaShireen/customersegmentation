import yaml
import pytest
import os
import json
import joblib
from prediction_service.prediction import form_response, format,api_response
import prediction_service

input_data = {
    ''
}
target_range={
    ''
}
def test_form_response_range(data=input_data['range']):
    res = form_response(data)
    assert target_range['min']<=res<=target_range['max']
