import string
from datetime import datetime

import numpy as np
import pandas as pd
import pymysql
from nltk.corpus import stopwords
from nltk.stem.porter import *


# Connection to MySQL  database
connection = pymysql.connect(host='localhost', port=3306, user='root', passwd='', db='rails')

try:
    with connection.cursor() as cursor:
        # Read records
        query1 = "SELECT * FROM pull_request"
        df1 = pd.read_sql(query1, connection)
finally:
    connection.close()

new_pr = df1.loc[32, :]

new_pr_created_date = new_pr['created_date'].strftime('%Y-%m-%d %H:%M:%S')
# integrator_login_name = new_pr['integrator_login']

# Connection to MySQL  database
connection = pymysql.connect(host='localhost', port=3306, user='root', passwd='', db='rails')

try:
    with connection.cursor() as cursor:
        # Read records
        query2 = "SELECT * FROM pull_request WHERE merged_date <%s"  # " AND integrator_login =%s"
        # inputs = (new_pr_created_date)
        cursor.execute(query2, new_pr_created_date)
        previously_reviewed_prs = cursor.fetchall()
finally:
    connection.close()


for previously_reviewed_pr in previously_reviewed_prs:
    # calculate file path similarity
    # calculate cosine similarity for each pr
    # calculate activeness according to time decaying parameter
    print(previously_reviewed_prs)
