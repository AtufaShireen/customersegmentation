# load train test
# train algo
# save metrics, params
import os
import warnings
from sklearn.metrics import silhouette_score
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import KMeans
from get_data import read_params
import argparse
import joblib
import json
# import mlflow
from urllib.parse import urlparse

# def eval_metrics(actual, pred):
#     rmse = np.sqrt(mean_squared_error(actual, pred))
#     mae = mean_absolute_error(actual, pred)
#     r2 = r2_score(actual, pred)
#     return rmse, mae, r2
    
def train_eval(config_path):
    config = read_params(config_path)
    rfm_actual_path = config['split_data']['rfm_actual']
    n_clusters = config['estimators']['Kmeans']['n_clusters']
    init = config['estimators']['Kmeans']['init']
    n_init = config['estimators']['Kmeans']['n_init']
    max_iter = config['estimators']['Kmeans']['max_iter']
    random_state = config['base']['random_state']

    model_dir = config['model_dir']

    rfm_actual = pd.read_csv(rfm_actual_path,sep = ',')
    scaler = MinMaxScaler()
    rf_actual_df = scaler.fit_transform(rfm_actual.drop(['ID'],axis=1))

    km=KMeans(n_clusters=n_clusters,init=init,n_init=n_init,max_iter=max_iter,random_state=random_state)
    km.fit(rf_actual_df)
    predicts = km.predict(rf_actual_df)
    sil_score = silhouette_score(rf_actual_df,predicts)

    scores_file = config["reports"]["scores"]
    params_file = config["reports"]["params"]

    with open(scores_file, "w") as f:
        scores = {
            "silhoutte_score": sil_score
        }
        json.dump(scores, f, indent=4)

    with open(params_file, "w") as f:
        params = {
            "n_clusters": n_clusters,
            "init": init,
            "n_init": n_init,
            "max_iter": max_iter,
            "random_state": random_state
        }
        json.dump(params, f, indent=4)
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, "model.joblib")

    joblib.dump(km, model_path)

   
if __name__=="__main__":
    args = argparse.ArgumentParser()
    args.add_argument("--config", default="params.yaml")
    parsed_args = args.parse_args()
    train_eval(config_path=parsed_args.config)