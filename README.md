py -m venv env
venv\Scripts\activate
code -a .
fsutil file createnew "requirements.txt" 0
pip install -r requirements.txt
fsutil file createnew "README.md"
https://github.com/amankharwal/Website-data/blob/master/marketing_campaign.csv


--initial git commands
git init
dvc init
git remote add origin git@github.com:AtufaShireen/customersegmentation.git

--commit commands
dvc add data_given/campaign.csv
git add . 
git commit -m
git branch -M main
git push -u origin main
dvc repro

--tox or test commands
fsutil file createnew tox.ini 0
tox
pytest -v

--setup commands
pip install -e .
--build package
python setup.py sdist bdist_wheel


mkdir artifacts
--mlflow server commands
 backend-store-uri sqlite://mlflow.db --default-artifact-root ./artifacts
 --host 0.0.0.0 -p 1234