import os
import yaml
import joblib
import numpy as np
import json
param_path = "params.yaml"
schema_path = os.path.join("prediction_servive","schema.json")

class NotInRange(Exception):
    def __init__(self, message="value not in range"):
        self.message=message
        super().__init__(self.message)
        
def read_params(config_path=param_path):
    with open(config_path) as yaml_file:
        config = yaml.safe_load(yaml_file)
    return config

def predict(data):
    config = read_params(param_path)
    model_dir_path = config['webapp_model_dir']
    model = joblib.load(model_dir_path)
    prediction = model.predict(data).tolist()

    try:
        if 3<= prediction<=8:
            return prediction
        else:
            raise NotInRange
    except NotInRange:
        return "Unexpected"

def get_schema(schema_path=schema_path):
    with open(schema_path) as json_file:
        shema = json.load(json_file)
    return shema



def validate_input(dict_req):
    def _validate_cols(col):
        schema = get_schema()
        actual_cols = schema.keys()
        if col not in actual_cols:
            raise NotInCols
    def _validate_values(col,val):
        schema = get_schema()
        if not (schema[col]['min']<= float(dict_req[col])<= schema[col]['max']):
            raise NotInRange
    for col,value in dict_req.items():
        _validate_cols(col)
        _validate_values(value)

def form_response(dict_response):
    if validate_input(dict_response):
        data = dict_response.values()
        data = list(map(float,data))
        response = predict(data)
        return response

def api_response(dict_request):
    try:
        if validate_input(dict_request):
            data = np.array(list(dict_request.values()))
            response = predict(data)
            response ={'response':response}
            return response
    except Exception as e:
        response = {'expected':get_schema(),"response":str(e)} 
