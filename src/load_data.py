# read data from source
# save in data/raw
import os
from get_data import read_params,getdata
import argparse

def load_and_save(config_path):
    config  = read_params(config_path) 
    df = getdata(config_path)
    new_cols  = [col.replace(" ","_") for col in df.columns]
    raw_data_path = config['load_data']['raw_dataset_csv']
    df.to_csv(raw_data_path,sep=',',index=False,header=new_cols)


if __name__=='__main__':
    args = argparse.ArgumentParser()
    args.add_argument("--config",default="params.yaml")
    parsed_args  =args.parse_args()
    load_and_save(parsed_args.config)  