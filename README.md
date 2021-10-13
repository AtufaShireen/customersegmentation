py -m venv env
venv\Scripts\activate
code -a .
fsutil file createnew "requirements.txt" 0
pip install -r requirements.txt
fsutil file createnew "README.md"
https://github.com/amankharwal/Website-data/blob/master/marketing_campaign.csv
git init
dvc init
dvc add data_given/campaign.csv
