import string

import pandas as pd
import pymysql
from nltk.corpus import stopwords
from nltk.stem.porter import *

from sklearn.feature_extraction.text import TfidfVectorizer

import logging

logging.basicConfig(level=logging.INFO, filename='app.log', format='%(name)s - %(levelname)s - %(message)s')


def path_to_list(file_string):
    return file_string.split("/")


def longest_common_prefix(f1, f2):
    f1 = path_to_list(f1)
    f2 = path_to_list(f2)
    common_path = 0
    min_length = min(len(f1), len(f2))
    for i in range(min_length):
        if f1[i] == f2[i]:
            common_path += 1
        else:
            break
    return common_path


def longest_common_suffix(f1, f2):
    f1 = path_to_list(f1)
    f2 = path_to_list(f2)
    common_path = 0
    r = range(min(len(f1), len(f2)))
    reversed(r)
    for i in r:
        if f1[i] == f2[i]:
            common_path += 1
        else:
            break
    return common_path


def longest_common_sub_string(f1, f2):
    f1 = path_to_list(f1)
    f2 = path_to_list(f2)
    common_path = 0
    if len(set(f1) & set(f2)) > 0:
        mat = [[0 for x in range(len(f2) + 1)] for x in range(len(f1) + 1)]
        for i in range(len(f1) + 1):
            for j in range(len(f2) + 1):
                if i == 0 or j == 0:
                    mat[i][j] = 0
                elif f1[i - 1] == f2[j - 1]:
                    mat[i][j] = mat[i - 1][j - 1] + 1
                    common_path = max(common_path, mat[i][j])
                else:
                    mat[i][j] = 0
    return common_path


def longest_common_sub_sequence(f1, f2):
    f1 = path_to_list(f1)
    f2 = path_to_list(f2)
    if len(set(f1) & set(f2)) > 0:
        l = [[0 for x in range(len(f2) + 1)] for x in range(len(f1) + 1)]
        for i in range(len(f1) + 1):
            for j in range(len(f2) + 1):
                if i == 0 or j == 0:
                    l[i][j] = 0
                elif f1[i - 1] == f2[j - 1]:
                    l[i][j] = l[i - 1][j - 1] + 1
                else:
                    l[i][j] = max(l[i - 1][j], l[i][j - 1])
        common_path = l[len(f1)][len(f2)]
    else:
        common_path = 0
    return common_path


class PullRequest:

    @staticmethod
    def initialise_files(files_string):
        return files_string.split("|")

    def __init__(self, data):
        self.pr_id = data[0]
        self.first_pull = data[1]
        self.location = data[2]
        self.pull_number = data[3]
        self.requester_login = data[4]
        self.title = data[5]
        self.description = data[6]
        self.created_date = data[7]
        self.merged_data = data[8]
        self.latest_time = data[9]
        self.integrator_login = data[10]
        self.num_of_commits = data[11]
        self.num_of_added_lines = data[12]
        self.num_of_deleted_lines = data[13]
        self.total_lines = data[14]
        self.num_of_changed_files = data[15]
        self.files = self.initialise_files(data[16])
        self.developer_type = data[17]
        self.requester_follows_core_team = data[18]
        self.core_team_follows_requester = data[19]


class Integrator:
    def __init__(self, login_name):
        self.integrator_login = login_name
        self.longest_common_prefix_score = 0
        self.longest_common_suffix_score = 0
        self.longest_common_sub_string_score = 0
        self.longest_common_sub_sequence_score = 0
        self.pr_title_similarity = 0
        self.pr_description_similarity = 0
        self.activeness = 0
        self.num_of_first_pulls = 0
        self.num_of_prs = 0
        self.total_commits = 0


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
connection = pymysql.connect(host='34.73.65.150', port=3306, user='root', passwd='Rahula123', db='rails')

try:
    with connection.cursor() as cursor:
        # Read records
        query1 = "SELECT * FROM pull_request LIMIT 3000 OFFSET 6156"
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
    logging.info(test_pr.pr_id)
    print(test_pr.pr_id)
    for integrator in integrators:
        pr_integrator = Integrator(integrator[0])

        # Connection to MySQL  database
        connection = pymysql.connect(host='34.73.65.150', port=3306, user='root', passwd='Rahula123', db='rails')

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
