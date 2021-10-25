import pandas as pd
def xe():
    print('------')
    required_cols = ['id','recency','frequency','monetary','dt_customer']
    csv_file_path = r'C:\Users\Atufa\Projects\CustomerSegments\data_given\usersdata\ammi\campaign.csv'
    new_cols = [i.lower() for i in pd.read_csv(csv_file_path,nrows=5).columns]
    print(new_cols)
    intersection = set(required_cols.sort()).intersection(set(new_cols.sort()))
    print('intersection',intersection)
    if intersection == required_cols:
        print('yes')  
    else:
        print('no')
def csv_to_h5(csv_file_path,h5_file_path):
    hdf_key = 'hdf_key'
    required_cols = ['id','recency','frequency','monetary','dt_customer']
    new_cols = list(map(str.lower,pd.read_csv(csv_file_path,nrows=5).columns))
    intersection = set(required_cols).intersection(set(new_cols))
    print('intersection',intersection)
    if sorted(intersection) == sorted(required_cols): 
        store = pd.HDFStore(h5_file_path)
        print('H5 File created for users: ')
        for chunk in pd.read_csv(csv_file_path, chunksize=500000):
            store.append(hdf_key, chunk, index=False)
        # store.create_table_index(hdf_key, optlevel=9, kind='full')
        store.close()
        return {'status':True,'message':'File stored'}
    else:
        return {'status':False,'message':'File doesnot contain required columns'}

csv_file_path = r'C:\Users\Atufa\Projects\CustomerSegments\data_given\usersdata\ammi\campaigns.csv'
hdf_file_path = r'C:\Users\Atufa\Projects\CustomerSegments\data_given\usersdata\ammi\campaigns.h5'
print(csv_to_h5(csv_file_path,hdf_file_path))