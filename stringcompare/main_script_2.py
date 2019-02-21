import string

import numpy as np
import pandas as pd
import pymysql
from nltk.corpus import stopwords
from nltk.stem.porter import *

from stringcompare.entities import PullRequest, Integrator
from stringcompare.string_compare import longest_common_prefix, longest_common_suffix, longest_common_sub_string, \
    longest_common_sub_sequence
from sklearn.feature_extraction.text import TfidfVectorizer


def rearrange_file_paths(file_paths_string):
    files = file_paths_string.split("|")
    new_file_string = ' '.join(files)
    return new_file_string


def text_process(string_variable):
    """
    Takes in a string of text, then performs the following:
    1. Remove all punctuation
    2. Remove all stopwords
    3. Returns a list of the cleaned text
    """
    # Check characters to see if they are in punctuation
    no_punctuation = [char for char in string_variable if char not in string.punctuation]

    # Join the characters again to form the string.
    no_punctuation = ''.join(no_punctuation)

    # Now just remove any stopwords
    before_stem = [word for word in no_punctuation.split() if word.lower() not in stopwords.words('english')]

    stemmer = PorterStemmer()
    return [stemmer.stem(word) for word in before_stem]


# Connection to MySQL  database
connection = pymysql.connect(host='localhost', port=3306, user='root', passwd='', db='rails')

try:
    with connection.cursor() as cursor:
        # Read records
        query1 = "SELECT * FROM pull_request"
        # df1 = pd.read_sql(query1, connection)
        cursor.execute(query1)
        all_prs = cursor.fetchall()
        df = pd.read_sql(query1, connection)
finally:
    connection.close()

# time_decaying_parameter
const_lambda = -1

tfidf_vectorizer = TfidfVectorizer(analyzer=text_process)


def cos_similarity(title1, title2):
    term_frequency = tfidf_vectorizer.fit_transform([title1, title2])
    return (term_frequency * term_frequency.T).A[0, 1]


new_pr = all_prs[33]
new_pr = PullRequest(new_pr)
pr_integrator = Integrator(new_pr.integrator_login)

# Connection to MySQL  database
connection = pymysql.connect(host='localhost', port=3306, user='root', passwd='', db='rails')

try:
    with connection.cursor() as cursor:
        # Read records
        query2 = "SELECT * FROM pull_request WHERE merged_date <%s AND integrator_login =%s"
        inputs = (new_pr.created_date.strftime('%Y-%m-%d %H:%M:%S'), new_pr.integrator_login)
        cursor.execute(query2, inputs)
        integrator_reviewed_prs = cursor.fetchall()
finally:
    connection.close()


for integrator_reviewed_pr in integrator_reviewed_prs:
    # calculate file path similarity
    # calculate cosine similarity for each pr
    # calculate activeness according to time decaying parameter
    # TODO: calculate the mean of the number of commits,first pull,number of added lines,number of deleted lines
    # TODO: Finally calculate the accuracy and add a grid search like functionality

    old_pr = PullRequest(integrator_reviewed_pr)
    
    old_pr_merged_date = old_pr.merged_data
    old_pr_file_paths = old_pr.files
    old_pr_title = old_pr.title
    old_pr_description = old_pr.description

    # calculate file path similarity
    for new_pr_file_path in new_pr.files:
        for file_path in old_pr_file_paths:
            max_file_path_length = max(len(new_pr_file_path.split("/")), len(file_path.split("/")))
            pr_integrator.longest_common_prefix_score += \
                (longest_common_prefix(new_pr_file_path, file_path)/max_file_path_length)
            pr_integrator.longest_common_suffix_score += \
                (longest_common_suffix(new_pr_file_path, file_path)/max_file_path_length)
            pr_integrator.longest_common_sub_string_score += \
                (longest_common_sub_string(new_pr_file_path, file_path)/max_file_path_length)
            pr_integrator.longest_common_sub_sequence_score += \
                (longest_common_sub_sequence(new_pr_file_path, file_path)/max_file_path_length)

    # calculate cosine similarity of title
    pr_integrator.pr_title_similarity += cos_similarity(new_pr.title, old_pr.title)

    # calculate cosine similarity of description
    if new_pr.description != "" and old_pr.description != "":
        pr_integrator.pr_description_similarity += cos_similarity(new_pr.description, old_pr.description)

    # calculate activeness of the integrator
    activeness = new_pr.created_date - old_pr.merged_data
    if hasattr(activeness, 'days'):
        activeness = activeness.days
    else:
        activeness = 0
    pr_integrator.activeness += activeness**const_lambda

print(pr_integrator.longest_common_prefix_score)
print(pr_integrator.longest_common_suffix_score)
print(pr_integrator.longest_common_sub_string_score)
print(pr_integrator.longest_common_sub_sequence_score)
print(pr_integrator.pr_title_similarity)
print(pr_integrator.pr_description_similarity)
print(pr_integrator.activeness)
print("")

