import os
# from prediction_service import prediction
from flask import Flask,request,render_template,redirect,url_for,session,flash,jsonify
from functools import wraps
from werkzeug.utils import secure_filename
import pandas as pd
from dbmanagement.mongoDbOperations import MongoDBmanagement
from  Analysis.analysedata import DataOverview, Graphs
import uuid 
import bcrypt

app = Flask(__name__)
mongo =  MongoDBmanagement()
param_path = "params.yaml"
webapp_root = "webapp"

static_dir = os.path.join(webapp_root,"static")
template_dir  =os.path.join(webapp_root,"templates")
SECRET_KEY = b'_5#y2L"F4Q8z\n\xec]/'


dir_path = os.path.dirname(os.path.realpath(__file__))
users_folders = os.path.join(dir_path,'data_given','usersdata')

app=Flask(__name__,static_folder=static_dir,template_folder=template_dir)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kws):
            if 'email' in session:
                return f(*args, **kws) 
            else:
                return redirect(url_for('login'))           
    return decorated_function

def file_required(f):
    @wraps(f)
    def decorated_function(*args, **kws):
            if 'filename' in session:
                print('----yes')
                return f(*args, **kws)
            else:
                return redirect(url_for('upload'))            
    return decorated_function


@app.route("/login", methods=["POST", "GET"])
def login():
    message = 'Please login to your account'
    if "email" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email")
        file = email.split('@')[0]
        password = request.form.get("password")

        email_found = mongo.findfirstRecord(db_name='usersinfo',collection_name='registered',query={"email": email})
        if email_found:
            email_val = email_found['email']
            passwordcheck = email_found['password']
            
            if bcrypt.checkpw(password.encode('utf-8'), passwordcheck):
                session["email"] = email_val
                file_uploaded = email_found['filename']
                if file_uploaded=='':
                    print("No files uploaded YEt")
                    return redirect(url_for('upload'))
                else:
                    return redirect(url_for('dashboard'))
            else:
                flash('Wrong password')
                print("Wrong PAssword")
                return redirect(url_for('login'))
        else:
            flash('Email not found')
            return redirect('login')
    return render_template('login.html')

@app.route("/register", methods=['POST', 'GET'])
def register():
    if "email" in session:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        user = request.form.get("fullname")
        email = request.form.get("email")
        
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")
        if password1 != password2:
            flash('Passwords should match!')
            return redirect(url_for('register'))
        user_found = mongo.findfirstRecord(db_name='usersinfo',collection_name='registered',query={"name": user})
        email_found = mongo.findfirstRecord(db_name='usersinfo',collection_name='registered',query={"email": email})
        
        if user_found:
            flash('There already is a user by that name')
            return redirect(url_for('register'))
        if email_found:
            flash('This email already exists in database')
            return redirect(url_for('register'))
        else:
            hashed = bcrypt.hashpw(password2.encode('utf-8'), bcrypt.gensalt())
            user_input = {'name': user, 'email': email, 'password': hashed,'_id':uuid.uuid4(),'active':False,'filename':''}
            mongo.InsertRecord(db_name='usersinfo',collection_name='registered',record=user_input)
            
            
            # user_data = mongo.findfirstRecord(db_name='usersinfo',collection_name='registered',query={"email": email})
            # new_email = user_data['email']
   
            return redirect(url_for('dashboard')) 
    return render_template('register.html')

# @app.route('/csv_to_h5', methods = ['POST','GET'])  
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

@app.route('/upload', methods = ['POST','GET'])  
# @login_required
def upload():  # get the curretn user and create a folder for them in usersdata and store files there
    user_name = session['email'].split('@')[0]
    record = mongo.findfirstRecord(db_name='usersinfo',collection_name='registered',query={'email':session['email']})
    file_name = record['filename']
    
    if file_name !='':
        print("already uploaded a file")
        return redirect(url_for('dashboard'))
    if request.method=='POST':
        
        user_folder = os.path.join(users_folders,user_name)
        try:
            uploaded_file = request.files['file']
            project_name = request.form['project']
            print('=====project name',project_name)
        except Exception as e:
            print('Exception',e)
            flash('Error in uploading file please try again')
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
                os.mkdir(user_folder)
                print('Folder created for user',user_folder)
            csv_file_path = os.path.join(user_folder,filename)
            
            uploaded_file.save(csv_file_path) #remove and convert here
            print('File saved')
            try:
                x= csv_to_h5(csv_file_path,h5_file_path)
                if x['status']:
                    if os.path.isfile(csv_file_path):
                        os.remove(csv_file_path)
                        print('File removed!')
                    mongo.updateOneRecord(db_name='usersinfo',collection_name='registered',prev={"name": user_name},query={'$set':{"filename":h5_filename}})
                    session['filename'] = file_name
                    flash(x['message'])
                    print(x['message'])
                    return redirect(url_for('dashboard'))
                else:
                    os.remove(csv_file_path)
                    print('File removed!')
                    flash(x['message'])
                    print(x['message'])
                    return redirect(url_for('upload'))
            except Exception as e:
                flash("coudn't convert to hdf5: ")
                return redirect(url_for('upload'))
    
    flash('Upload a file to get started')
    return render_template("file_upload.html")  


@app.route('/dashboard',methods = ['POST','GET'])
@login_required 
# @file_required
def dashboard():
    # user_name = session['email'].split('@')[0]
    # user = mongo.findfirstRecord(db_name='usersinfo',collection_name='registered',query={"email": session['email']})
    # file_name = user['filename']
    # print('sfdghj',file_name)
    # file_name = os.path.join(users_folders,user_name,file_name)
    # print('sfdghj',user_name)
    file_name = r'C:\Users\Atufa\Projects\CustomerSegments\data_given\usersdata\ammi\campaigns.h5'
    if file_name=='':
        flash('Upload a file first')
        return redirect(url_for('upload')) 
    print(f"File name{file_name}")
    data = Graphs(file_name)
    # data_info = data.data_analysis_graph()
    return render_template('dashboard.html')#,{'data_info':data_info}


if __name__ == '__main__':
    app.config['SECRET_KEY'] = SECRET_KEY
    
    app.config['UPLOAD_FOLDER'] = 'usersdata'
    app.config['UPLOAD_EXTENSIONS'] = ['.csv','.h5']
    app.run(host='0.0.0.0',port=5000,debug=True)
    
