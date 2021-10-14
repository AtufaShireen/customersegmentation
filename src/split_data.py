# split raw data
# save in data/processed
import os

from get_data import read_params,getdata
import argparse
import pandas as pd
from sklearn.model_selection import train_test_split

def split_and_save(config_path):
    config = read_params(config_path)
    score_path = config['split_data']['score_path']
    actual_path = config['split_data']['actual_path']
    raw_data_path = config['load_data']['raw_dataset_csv']

    df = pd.read_csv(raw_data_path,sep=',',usecols=['ID','Recency','Frequency','Monetary','Dt_Customer'])
    
    score_df = df[['ID','Recency','Frequency','Monetary']].sort_values(by=['Recency','Frequency','Monetary'],ascending=[False,False,False])
    #split data into 20% quantiles 5*5*5 and 5*20% = 100
    score_df['f_score'] = pd.qcut(score_df['FREQUENCY'],q=4,labels=range(1,5))
    score_df['r_score'] = pd.qcut(score_df['RECENCY'],q=4,labels=range(1,5))
    score_df['m_score'] = pd.qcut(score_df['MONETARY'],q=4,labels=range(1,5))
    score_df['rfm_score'] = score_df['f_score'].astype(str)+score_df['r_score'].astype(str)+score_df['m_score'].astype(str)
    assert score_df.shape[0]==df.shape[0]

    actual_df = df[['ID','Recency','Frequency','Monetary']].sort_values(by=['Recency','Frequency','Moneatry'],ascending=[True,False,False])
    assert actual_df.shape[0]==df.shape[0]

    score_df.to_csv(actual_path,index=False)
    actual_df.to_csv(score_path,index = False)

if __name__=='__main__':
    args = argparse.ArgumentParser()
    args.add_argument("--config",default="params.yaml")
    parsed_args  =args.parse_args()
    split_and_save(parsed_args.config)