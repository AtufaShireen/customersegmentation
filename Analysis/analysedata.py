from flask.globals import request
import pandas as pd
import plotly.graph_objects as go
import os
import plotly.express as px
from sklearn.cluster import KMeans
class DataOverview: #path should be here
    def __init__(self,path) -> None:
        self.path = path
        '''Hdf file path here'''
        ext = self.path.split('.')[1]
        if ext == 'h5':
            self.data = pd.read_hdf(path)
        elif ext == 'csv':
            self.data = pd.read_csv(path)
        self.data = self.data.dropna(inplace=True)
    def csv_to_h5(self):
        hdf_key = 'hdf_key'
        store = pd.HDFStore('hdffile')# set file path here

        for chunk in pd.read_csv(self.path, chunksize=500000):
            # don't index data columns in each iteration - we'll do it later ...
            store.append(hdf_key, chunk, index=False)
            # index data columns in HDFStore

        store.create_table_index(hdf_key, optlevel=9, kind='full')
        
        store.close()
    
            
    def data_to_h5(self,path,name):
        df = pd.read_csv(path)
        filename = f'/tmp/{name}.h5' # check if exists
        # hf = h5py.File('data.h5', 'w')
        try:
            df.to_hdf(filename,mode='w',format='table')
            return {'status':True,'message':'Done'}
        except Exception as e:
            return {'status':False,'message':e}
    def read_h5(self,path):
        try:
            df = pd.read_hdf(path,'w') 
            # df = pd.DataFrame(np.array(h5py.File(path)['variable_1']))
            return {'status':True,'message':df}
        except Exception as e:
            return {'status':False,'message':'Error in file reading'}
        
    def data_overview(self):
        num_stats = self.data.describe(include=['number']).transpose()   
        return num_stats
    
    
    def data_analysis(self):
        score_df = self.data[['id','frequency','monetary','recency']]
        score_df['f_score'] = pd.qcut(score_df['frequency'],q=5,labels=range(0,5))
        score_df['r_score'] = pd.qcut(score_df['recency'],q=5,labels=range(0,5))
        score_df['m_score'] = pd.qcut(score_df['monetary'],q=5,labels=range(0,5))
        conds = {
         r'44.':'Champions',
         r'[2,3,4][3,4].':'Loyal',
         r'[3,4][1,2].':'Potential Loyal',
         r'[1,2][1,2].':'Need Attention',
         r'41.':'New Customers',
         r'21.':'Hibernating',
         r'[1,0]4.':'Cant Loose',
         r'[1,0][1,0].':'Lost',
         r'[1,0][2,3].':'At Risk',
         r'40.':'New Customers'
         }
        score_df['Label'] = score_df['r_score'].astype(str)+score_df['f_score'].astype(str)
        score_df['Label'] = score_df['Label'].replace(conds,regex=True)
        score_df['Label'].value_counts()
        print('Done,df')
        return score_df
    def data_segments(self):
        data = self.data.drop('dt_customer',axis=1)
        km=KMeans(n_clusters=5,init='k-means++',n_init=50,max_iter=500,random_state=42)
        km.fit(data.drop('id',axis=1))
        data['cluster'] = km.predict(data)
        data = data.groupby('cluster')
        return data
    

class Graphs(DataOverview):
    def __init__(self,path):
        super().__init__(path)

    def data_analysis_graph(self): # convert to squarify later
        df = self.data_analysis()
        fig = px.pie(df,values='rfm_score',names='Label',title='Customer segments on RFM scores',)
        fig.update_traces(hoverinfo='percent', textinfo='percent', textfont_size=10)
        folder = r'C:\Users\Atufa\Projects\CustomerSegments\data_given\usersdata\ammi'
        fig.write_html(file=os.path.join(folder,'name.html'),auto_open=False,full_html=False) 
        return 'Done'
    def data_graph(self):
        data = self.data_overview()
        columns = ['frequency','recency','monetary']
        fig = go.Figure(data=[go.Table(
            header=dict(values=columns,
                        fill_color='paleturquoise',
                        align='left'),
            cells=dict(values=[data.count, data.mean, data.min,data.max],
                    fill_color='lavender',
                    align='left'))
        ])
        folder = r'C:\Users\Atufa\Projects\CustomerSegments\data_given\usersdata\ammi'
        fig = fig.to_json()
        fig.write_html(file=os.path.join(folder,'name.html'),auto_open=False,full_html=False) 
        return 'Done'
    
    def data_segments_graph(self):
        data = self.data_segments()
        clus_0 = data[data.label==0]
        clus_1 = data[data.label==1]
        clus_2 = data[data.label==2]
        clus_3 = data[data.label==3]
        clus_4 = data[data.label==4]
        dic = {'clus_0':clus_0.mean(),
       'clus_1':clus_1.mean(),
       'clus_2':clus_2.mean(),
       'clus_3':clus_3.mean(),
       'clus_4':clus_4.mean(),}

# hdf_file_path = r'C:\Users\Atufa\Projects\CustomerSegments\data_given\usersdata\ammi\campaigns.h5'
# x = Graphs(hdf_file_path)
# print(x.data_analysis_graph(x.data_analysis()))
