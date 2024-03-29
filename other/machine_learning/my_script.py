import string

import pandas as pd
import pymysql
from nltk.corpus import stopwords
from nltk.stem.porter import *

from sklearn.feature_extraction.text import TfidfVectorizer

from interec.entities.integrator import Integrator
from interec.entities.pull_request import PullRequest
from interec.string_compare.file_path_similarity import longest_common_prefix, longest_common_suffix, \
    longest_common_sub_string, longest_common_sub_sequence


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
        query1 = "SELECT * FROM pull_request LIMIT 2 OFFSET 6156"
        cursor.execute(query1)
        test_prs = cursor.fetchall()

        query2 = "SELECT integrator_login FROM integrator"
        cursor.execute(query2)
        integrators = cursor.fetchall()
finally:
    connection.close()

# time_decaying_parameter
const_lambda = -1

tfidf_vectorizer = TfidfVectorizer(analyzer=text_process)


def cos_similarity(title1, title2):
    term_frequency = tfidf_vectorizer.fit_transform([title1, title2])
    return (term_frequency * term_frequency.T).A[0, 1]


df1 = pd.DataFrame()

for test_pr in test_prs:
    test_pr = PullRequest(test_pr)
    print(test_pr.pr_id)
    for integrator in integrators:
        pr_integrator = Integrator(integrator[0])

        # Connection to MySQL  database
        connection = pymysql.connect(host='localhost', port=3306, user='root', passwd='', db='rails')

        try:
            with connection.cursor() as cursor:
                # Read records
                query2 = "SELECT * FROM pull_request WHERE merged_date <%s AND integrator_login =%s"
                inputs = (test_pr.created_date.strftime('%Y-%m-%d %H:%M:%S'), pr_integrator.integrator_login)
                cursor.execute(query2, inputs)
                integrator_reviewed_prs = cursor.fetchall()
        finally:
            connection.close()

        for integrator_reviewed_pr in integrator_reviewed_prs:

            old_pr = PullRequest(integrator_reviewed_pr)
            old_pr_merged_date = old_pr.merged_data
            old_pr_file_paths = old_pr.files
            old_pr_title = old_pr.title
            old_pr_description = old_pr.description

            # calculate file path similarity
            for test_pr_file_path in test_pr.files:
                for file_path in old_pr_file_paths:
                    max_file_path_length = max(len(test_pr_file_path.split("/")), len(file_path.split("/")))
                    pr_integrator.longest_common_prefix_score += \
                        (longest_common_prefix(test_pr_file_path, file_path) / max_file_path_length)
                    pr_integrator.longest_common_suffix_score += \
                        (longest_common_suffix(test_pr_file_path, file_path) / max_file_path_length)
                    pr_integrator.longest_common_sub_string_score += \
                        (longest_common_sub_string(test_pr_file_path, file_path) / max_file_path_length)
                    pr_integrator.longest_common_sub_sequence_score += \
                        (longest_common_sub_sequence(test_pr_file_path, file_path) / max_file_path_length)

            # calculate cosine similarity of title
            pr_integrator.pr_title_similarity += cos_similarity(test_pr.title, old_pr.title)

            # calculate cosine similarity of description
            if test_pr.description != "" and old_pr.description != "":
                pr_integrator.pr_description_similarity += cos_similarity(test_pr.description, old_pr.description)

            # calculate activeness of the integrator
            activeness = test_pr.created_date - old_pr.merged_data
            if hasattr(activeness, 'days'):
                activeness = activeness.days
            else:
                activeness = 0
            if activeness > 0:
                pr_integrator.activeness += activeness ** const_lambda

            if old_pr.first_pull == 1:
                pr_integrator.num_of_first_pulls += 1
            pr_integrator.num_of_prs += 1
            pr_integrator.total_commits += old_pr.num_of_commits

        if pr_integrator.num_of_prs == 0:
            first_pull_similarity = 0
            average_commits = 0
        else:
            first_pull_similarity = pr_integrator.num_of_first_pulls / pr_integrator.num_of_prs
            average_commits = pr_integrator.total_commits / pr_integrator.num_of_prs

        row = {'pull_number': test_pr.pull_number,
               'actual_integrator': test_pr.integrator_login,
               'possible_integrator': pr_integrator.integrator_login,
               'lcp': pr_integrator.longest_common_prefix_score,
               'lcs': pr_integrator.longest_common_suffix_score,
               'lc_substr': pr_integrator.longest_common_sub_string_score,
               'ls_subseq': pr_integrator.longest_common_sub_sequence_score,
               'cos_title': pr_integrator.pr_title_similarity,
               'cos_description': pr_integrator.pr_description_similarity,
               'activeness': pr_integrator.activeness,
               'first_pull': first_pull_similarity,
               'avg_commits': average_commits}
        df1 = df1.append(row, ignore_index=True)

df1.to_csv('test_pr_stats.csv', index=False)
print(df1)
