from logging import error
import os
import yaml
import joblib
from prediction_service import prediction
from flask import Flask,request,render_template,redirect,url_for,session,flash,jsonify
from functools import wraps
import os
from werkzeug.utils import secure_filename
import pandas as pd
from dbmanagement.mongoDbOperations import MongoDBmanagement

param_path = "params.yaml"
webapp_root = "webapp"

static_dir = os.path.join(webapp_root,"static")
template_dir  =os.path.join(webapp_root,"templates")
SECRET_KEY = b'_5#y2L"F4Q8z\n\xec]/'
# logger =userlogs.get_logger(__name__)
import logging
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'usersdata'
app.config['UPLOAD_EXTENSIONS'] = ['.csv']
dir_path = os.path.dirname(os.path.realpath(__file__))
users_folders = os.path.join(dir_path,'data_given','usersdata')
app.config['SECRET_KEY'] = SECRET_KEY
app=Flask(__name__,static_folder=static_dir,template_folder=template_dir)

def file_required(f):
    @wraps(f)
    def decorated_function(*args, **kws):
            if 'filename' in session:
                return f(*args, **kws)            
    return decorated_function

# @app.route('/csv_to_h5', methods = ['POST','GET'])  
def csv_to_h5(csv_file_path,h5_file_path):
    hdf_key = 'hdf_key'
    required_cols = ['ID','recency','frequency','monetary']
    new_cols = pd.read_csv(csv_file_path,nrows=5).columns
    intersection = set(required_cols).intersection(set(new_cols))
    if intersection == required_cols: 
        store = pd.HDFStore(h5_file_path)
        print('H5 File created for users: ')
        for chunk in pd.read_csv(csv_file_path, chunksize=500000):
            store.append(hdf_key, chunk, index=False)
        # store.create_table_index(hdf_key, optlevel=9, kind='full')
        store.close()
    else:
        raise ValueError


@app.route('/upload', methods = ['POST','GET'])  
def upload():  # get the curretn user and create a folder for them in usersdata and store files there
    user_name = request.form.get('username')

    # record = mongo.findfirstRecord(db_name='usersinfo',collection_name='registered',query={'email':session['email']})
    # file_name = record['filename']
    # if file_name !='':
    #     print("already uploaded a file")
    #     return redirect(url_for('dashboard'))
    if 'filename' in session:
        return redirect(url_for('dashboard'))
    if request.method=='POST':
        user_folder = os.path.join(users_folders,user_name)
        try:
            uploaded_file = request.files['file']
        except Exception as e:
            print('Exception',e)
            # flash('Error in uploading file please try again')
            return redirect(url_for('upload')) # why this not working
            
        filename = secure_filename(uploaded_file.filename)
        if filename != '':
            file_ext = os.path.splitext(filename)[1]
            if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                print('Please upload a valid extension')
                return redirect(url_for('upload'))
            
            h5_filename = f"{filename.split('.')[0]}.h5"
            h5_file_path = os.path.join(user_folder,h5_filename)
            if os.path.isfile(h5_file_path):
                print("---file already exisrs")
                return redirect(url_for('dashboard'))

            if not os.path.isdir(user_folder):
                print('Folder created for user',user_folder)
                os.mkdir(user_folder)
            csv_file_path = os.path.join(user_folder,filename)
            
            uploaded_file.save(csv_file_path)
            print('File saved')
            try:
                csv_to_h5(csv_file_path,h5_file_path)
                if os.path.isfile(csv_file_path):
                    os.remove(csv_file_path)
                    print('File removed!')
                # mongo.updateOneRecord(db_name='usersinfo',collection_name='registered',prev={"name": user_name},query={'$set':{"filename":h5_filename}})
                return redirect(url_for('dashboard'))
            except Exception as e:
                print("coudn't convert to hdf5: ")
                return redirect(url_for('upload'))
    
    flash('Upload a file to get started')
    return render_template("file_upload.html")  

@app.route('/',methods=['GET','POST'])
def index():
    if request.method == 'POST':
        try:
            if request.form:
                data_req= dict(request.form)
                response = prediction.form_response(data_req)
                return render_template("index.html",response=response)
            elif request.json:
                response = prediction.api_response(request.json)
                return jsonify(response)
        except Exception as e:
            print(e)
            return render_template("index.html",error=str(e))
         
    else:
        return render_template("index.html")
if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000,debug=True)
