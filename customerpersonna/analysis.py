from datetime import date
from datetime import datetime
import pandas as pd
import numpy as np
from customerpersonna.utils import *
from customerpersonna.segmentation import ml_segment
from customerpersonna.plottings import *
from customerpersonna.models import *

class Segmentation():
    def __init__(self,data,path=None) -> None:
        if path:
            self.df = read_corr_df(path)
        else:
            self.df = data
        self.ggf_model = None
        self.bgf_model = None

    def abstract_rfma_df(self,req_df,id_col,trans_col=None,trans_date_col=None,recency_col=None,frequency_col=None,monetary_col=None,age_col=None,cal_rec=None,cal_freq=None,cal_mon=None):
        req_df.dropna(inplace=True)
        df = req_df.copy()
        new_df = df.groupby([id_col],as_index=False)[id_col].first()
        new_df.columns = ['cust_id']

        if trans_date_col!=None:
            df[trans_date_col] = pd.to_datetime(df[trans_date_col],infer_datetime_format=True).dt.normalize()
            dates_df = df.groupby(by=id_col,
                                    as_index=False)[trans_date_col].agg(['min','max']).reset_index()
            dates_df.columns = ['cust_id', 'FirstPurchaseDate','LastPurchaseDate']

        if age_col!=None:
            new_df['uniq_age'] = df[age_col] 

        elif (age_col==None) & (trans_date_col!=None):
            print('herer (age_col==None) & (trans_date_col!=None)')
            last_date = max(dates_df['LastPurchaseDate'])
            dates_df['uniq_age'] = last_date - dates_df['FirstPurchaseDate']
            new_df['uniq_age'] = dates_df['uniq_age'].dt.days

        if cal_rec!=None:
            new_df['uniq_rec'] = df[cal_rec]
            new_df['recency'] = df[cal_rec]

        elif (recency_col ==None)& (trans_date_col!=None):
            print('herer (rececncy_col==None) & (trans_date_col!=None)')
            recent_date = max(df[trans_date_col])
            new_df['recency'] = pd.to_numeric(dates_df['LastPurchaseDate'].apply(lambda x: (recent_date - x)).dt.days, downcast='integer')
            new_df['uniq_rec']=(dates_df['LastPurchaseDate']-dates_df['FirstPurchaseDate']).dt.days
        elif (recency_col!=None):
            new_df['uniq_rec']=(new_df['uniq_age']-df[recency_col])
            new_df['recency'] = df[recency_col]


        if cal_freq!=None:
            new_df['uniq_freq'] = df[cal_freq]
            new_df['frequency'] = df[cal_freq]

        elif (frequency_col ==None)& (trans_date_col!=None):
            print('herer (frequnecy_col==None) & (trans_date_col!=None)')
            frequency_df = df.drop_duplicates().groupby(
            by=[id_col], as_index=False)[trans_date_col].count()
            frequency_df.columns = ['cust_id', 'frequency']
            
            uni_freq_df = df.drop_duplicates().groupby(
            by=[id_col], as_index=False)[trans_date_col].nunique()

            uni_freq_df.columns = ['cust_id', 'uniq_freq']
            uni_freq_df['uniq_freq']=uni_freq_df['uniq_freq']

            new_df['frequency'] =frequency_df['frequency']
            new_df['uniq_freq'] =uni_freq_df['uniq_freq']-1
            # uni_freq_df['uniq_freq']=uni_freq_df['uniq_freq'] -1
        else:
            new_df['frequency'] =df[frequency_col]
            new_df['uniq_freq'] =df[frequency_col]-1

        if cal_mon!=None:
            new_df['monetary'] = df[cal_mon]
            new_df['uniq_mon'] = df[cal_mon]
        elif monetary_col ==None:
            print('herer (monetary_col==None) & (trans_date_col!=None)')
            monetary_df = df.groupby(by=id_col, as_index=False)[trans_col].sum()
            monetary_df.columns = ['cust_id', 'monetary']
            monetary_df['uniq_mon'] = monetary_df['monetary'] / (new_df['frequency'])
            monetary_df.fillna(0,inplace=True)
            monetary_df[monetary_df['uniq_mon']< 0 ] = 0
            new_df[['monetary','uniq_mon']] = monetary_df[['monetary','uniq_mon']]
        else:
            new_df['monetary'] = df[monetary_col]
            new_df['uniq_mon'] = df[monetary_col] / new_df['frequency']
        

        # rfm_df =  recency_df.merge(frequency_df,on='cust_id')
        # rfm_df = rfm_df.merge(monetary_df, on='cust_id')
        # rfm_df = rfm_df.merge(uni_freq_df, on='cust_id')
        # rfm_df['uniq_age'] = dates_df['uniq_age']
        # return rfm_df[['cust_id','uniq_rec','uniq_freq','uniq_mon','uniq_age','recency','frequency','monetary']]

        return new_df
    
    def calculate_ltv_df(self,id_col,trans_col=None,trans_date_col=None,recency_col=None,frequency_col=None,monetary_col=None,age_col=None,cal_rec=None,cal_freq=None,cal_mon=None,profit_margin=1):
        args = locals()
        print('values herererer',args)
        print(id_col,trans_col)
        raw_df = self.df.copy()
        #extract rfma cols
        abs_df = self.abstract_rfma_df(raw_df,id_col,trans_col,trans_date_col,recency_col,frequency_col,monetary_col,age_col,cal_rec,cal_freq,cal_mon)
        #add ml segment label
        print(abs_df.info())
        abs_df = ml_segment(abs_df,'recency','frequency','monetary')
        # fit clv required models
        self.bgf_model,self.ggf_model = (fit_clv_model(abs_df,'uniq_rec','uniq_freq','uniq_mon','uniq_age'))
        # predict clv
        predictions_ = (predict_purchase(self.bgf_model,self.ggf_model,abs_df,'uniq_rec','uniq_freq','uniq_mon','uniq_age'))
        abs_df['LTV'] = predictions_['LTV']
        abs_df['p_churn']  = predictions_['p_alive']
        abs_df['exp_purchases']  = predictions_['predicted_purchases']
        abs_df['LTV'].fillna(0,inplace=True)
        if profit_margin:
            abs_df['LTV'] = abs_df['LTV'] * profit_margin
        else:
            abs_df['LTV'] = abs_df['LTV'] * 1
        return abs_df

rfm_cols = {	"SampleFileName": "retail_28011992_120212.csv",
	"LengthOfDateStampInFile": 8,
	"LengthOfTimeStampInFile": 6,
	"NumberofColumns" : 9,
	"ColName": {
        "InvoiceNo":"String",
        "StockCode":"String",
        "Description":"String",
         "Quantity":"float",
          "InvoiceDate":"String",
       "UnitPrice":"float",
        "CustomerID":"float",
         "Country":"String",
          "spent_total":"float"
},
    "RFMCols":{
        "id_col":"CustomerID",
        "trans_col":"spent_total",
        "trans_date_col":"InvoiceDate"
    }
}



id_col = rfm_cols['RFMCols'].get('id_col',None)
trans_col=rfm_cols['RFMCols'].get('trans_col',None)
trans_date_col=rfm_cols['RFMCols'].get('trans_date_col',None)
recency_col=rfm_cols['RFMCols'].get('recency_col',None)
frequency_col=rfm_cols['RFMCols'].get('frequency_col',None)
monetary_col=rfm_cols['RFMCols'].get('monetary_col',None)
age_col=rfm_cols['RFMCols'].get('age_col',None)
cal_rec=rfm_cols['RFMCols'].get('cal_rec',None)
cal_freq=rfm_cols['RFMCols'].get('cal_freq',None)
cal_mon=rfm_cols['RFMCols'].get('cal_mon',None)
profit_margin=rfm_cols.get('profit_margin',1)

import os
#@title Retail Dataset
retail_dum_df = pd.read_csv('https://raw.githubusercontent.com/databricks/Spark-The-Definitive-Guide/master/data/retail-data/all/online-retail-dataset.csv')
retail_dum_df.head()
retail_dum_df['spent_total'] = retail_dum_df['Quantity']*retail_dum_df['UnitPrice']
retail_dum_df.to_csv('retail.csv',index=False)
print(retail_dum_df.head())

from datetime import date
last_date = date(2014,10, 4)
campaign_dum_df = pd.read_csv('marketing_campaign.csv',sep=';')
campaign_dum_df['Age']=pd.to_datetime(campaign_dum_df['Dt_Customer'], dayfirst=True,format = '%Y-%m-%d')
campaign_dum_df['Age'] = pd.to_numeric(campaign_dum_df['Age'].dt.date.apply(lambda x: (last_date - x)).dt.days, downcast='integer')
campaign_dum_df['Frequency'] =  campaign_dum_df['NumWebPurchases']+campaign_dum_df['NumCatalogPurchases']+campaign_dum_df['NumStorePurchases']
campaign_dum_df['spent_total'] = campaign_dum_df['MntFruits']+campaign_dum_df['MntWines']+campaign_dum_df['MntMeatProducts']+campaign_dum_df['MntFishProducts']+campaign_dum_df['MntSweetProducts']+campaign_dum_df['MntSweetProducts']
campaign_dum_df.to_csv('market_campaign.csv',index=False)
campaign_dum_df.head()


cd_now_df = pd.read_csv('https://raw.githubusercontent.com/CamDavidsonPilon/lifetimes/master/lifetimes/datasets/cdnow_customers_summary_with_transactions.csv')
cd_now_df.columns = ['id','frequency','recency','T','monetary_value']
cd_now_df.to_csv('cdnow.csv',index=False)
cd_now_df.head()

play_dum_df = pd.read_csv('https://raw.githubusercontent.com/alifiaharmd/ML-DLPlayground/main/Dataset/Retail_Data_Transactions.csv')
play_dum_df.to_csv('playground.csv',index=False)
play_dum_df.head()

segment = Segmentation(data=retail_dum_df)
rfm_df = segment.calculate_ltv_df(id_col,trans_col,trans_date_col,recency_col,frequency_col,monetary_col,age_col,cal_rec,cal_freq,cal_mon,profit_margin)
print(rfm_df.head())
print(retail_dum_df['ID'].nunique())
g = SegmentAnalysis(rfm_df)
print(g.plot_cust_bar())