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
import mlflow
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
    mlflow_config = config['mlflow_config']
    remote_server_uri = config['remote_server_uri']
    mlflow.set_tracking_uri(remote_server_uri)
    mlflow.set_experiment(mlflow_config['experiment_name'])


    with mlflow.start_run(run_name=mlflow_config['run_name']) as mlops_run:
        km=KMeans(n_clusters=n_clusters,init=init,n_init=n_init,max_iter=max_iter,random_state=random_state)
        km.fit(rf_actual_df)
        predicts = km.predict(rf_actual_df)
        sil_score = silhouette_score(rf_actual_df,predicts)
        mlflow.log_param("n_clusters",n_clusters)
        mlflow.log_param("init",init)
        mlflow.log_param("n_init",n_init)
        mlflow.log_param("max_iter",max_iter)
        mlflow.log_param("random_state",random_state)
        mlflow.log_metric("silhoutte score",sil_score)

        tracking_url_type = urlparse(mlflow.get_artifact_uri()).scheme
        if tracking_url_type!='file':
            mlflow.sklearn.log_model(km,"model",registered_model_name=mlflow_config['registered_model_name'])
        else:
            mlflow.sklearn.load_model(km,"model")
        # os.makedirs(model_dir,exist_ok=True)
        # model_path = os.path.join(model_dir,'model.joblib')
        # joblib.dump(km,model_path)
   
if __name__=="__main__":
    args = argparse.ArgumentParser()
    args.add_argument("--config", default="params.yaml")
    parsed_args = args.parse_args()
    train_eval(config_path=parsed_args.config)