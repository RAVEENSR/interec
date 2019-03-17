import logging
import string
from datetime import timedelta

import pandas as pd
from nltk.corpus import stopwords
from nltk.stem.porter import *
from sklearn.feature_extraction.text import TfidfVectorizer

from pyspark.sql import SparkSession

database = 'rails'
spark = ""
all_prs_df = ""
all_integrators_df = ""
all_integrators = ""


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
        self.num_of_prs = 0

    @property
    def integrator_login(self):
        return self.__integrator_login

    @property
    def longest_common_prefix_score(self):
        return self.__longest_common_prefix_score

    @property
    def longest_common_suffix_score(self):
        return self.__longest_common_suffix_score

    @property
    def longest_common_sub_string_score(self):
        return self.__longest_common_sub_string_score

    @property
    def longest_common_sub_sequence_score(self):
        return self.__longest_common_sub_sequence_score

    @property
    def pr_title_similarity(self):
        return self.__pr_title_similarity

    @property
    def pr_description_similarity(self):
        return self.__pr_description_similarity

    @property
    def activeness(self):
        return self.__activeness

    @property
    def num_of_prs(self):
        return self.__num_of_prs

    @integrator_login.setter
    def integrator_login(self, val):
        self.__integrator_login = val

    @longest_common_prefix_score.setter
    def longest_common_prefix_score(self, val):
        self.__longest_common_prefix_score = val

    @longest_common_suffix_score.setter
    def longest_common_suffix_score(self, val):
        self.__longest_common_suffix_score = val

    @longest_common_sub_string_score.setter
    def longest_common_sub_string_score(self, val):
        self.__longest_common_sub_string_score = val

    @longest_common_sub_sequence_score.setter
    def longest_common_sub_sequence_score(self, val):
        self.__longest_common_sub_sequence_score = val

    @pr_title_similarity.setter
    def pr_title_similarity(self, val):
        self.__pr_title_similarity = val

    @pr_description_similarity.setter
    def pr_description_similarity(self, val):
        self.__pr_description_similarity = val

    @activeness.setter
    def activeness(self, val):
        self.__activeness = val

    @num_of_prs.setter
    def num_of_prs(self, val):
        self.__num_of_prs = val


class PullRequest:

    @staticmethod
    def initialise_files(files_string):
        return files_string.split("|")

    def __init__(self, data):
        self.pr_id = data[0]
        self.pull_number = data[1]
        self.requester_login = data[2]
        self.title = data[3]
        self.description = data[4]
        self.created_date = data[5]
        self.merged_data = data[6]
        self.integrator_login = data[7]
        self.files = self.initialise_files(data[8])

    @property
    def pr_id(self):
        return self.__pr_id

    @property
    def pull_number(self):
        return self.__pull_number

    @property
    def requester_login(self):
        return self.__requester_login

    @property
    def title(self):
        return self.__title

    @property
    def description(self):
        return self.__description

    @property
    def created_date(self):
        return self.__created_date

    @property
    def merged_data(self):
        return self.__merged_data

    @property
    def integrator_login(self):
        return self.__integrator_login

    @property
    def files(self):
        return self.__files

    @pr_id.setter
    def pr_id(self, val):
        self.__pr_id = val

    @pull_number.setter
    def pull_number(self, val):
        self.__pull_number = val

    @requester_login.setter
    def requester_login(self, val):
        self.__requester_login = val

    @title.setter
    def title(self, val):
        self.__title = val

    @description.setter
    def description(self, val):
        self.__description = val

    @created_date.setter
    def created_date(self, val):
        self.__created_date = val

    @merged_data.setter
    def merged_data(self, val):
        self.__merged_data = val

    @integrator_login.setter
    def integrator_login(self, val):
        self.__integrator_login = val

    @files.setter
    def files(self, val):
        self.__files = val


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


tfidf_vectorizer = TfidfVectorizer(analyzer=text_process)


def cos_similarity(string1, string2):
    term_frequency = tfidf_vectorizer.fit_transform([string1, string2])
    return (term_frequency * term_frequency.T).A[0, 1]


# time_decaying_parameter
const_lambda = -1


def calculate_integrator_activeness(new_pr, old_pr):
    # calculate activeness of the integrator
    activeness = new_pr.created_date - old_pr.merged_data
    if hasattr(activeness, 'days'):
        activeness = activeness.days
    else:
        activeness = 0
    if activeness > 0:
        activeness = activeness ** const_lambda

    return activeness


def initialise_app(database_name):
    global database, spark, all_prs_df, all_integrators_df, all_integrators

    database = database_name
    # Create a spark session
    spark = SparkSession \
        .builder \
        .master('local') \
        .appName("Interec") \
        .getOrCreate()

    # Read table pull_request
    all_prs_df = spark.read \
        .format("jdbc") \
        .option("url", "jdbc:mysql://localhost:3306/" + database) \
        .option("driver", 'com.mysql.cj.jdbc.Driver') \
        .option("dbtable", "pull_request") \
        .option("user", "root") \
        .option("password", "") \
        .load()

    # Read table integrator
    all_integrators_df = spark.read \
        .format("jdbc") \
        .option("url", "jdbc:mysql://localhost:3306/" + database) \
        .option("driver", 'com.mysql.cj.jdbc.Driver') \
        .option("dbtable", "integrator") \
        .option("user", "root") \
        .option("password", "") \
        .load()

    all_prs_df.createOrReplaceTempView("pull_request")
    all_integrators_df.createOrReplaceTempView("integrator")

    # Get all the integrators for the project
    query = "SELECT * FROM integrator"
    all_integrators = spark.sql(query).collect()


def calculate_scores(df, new_pr, date_window=0):
    # Calculate scores for each integrator
    for integrator in all_integrators:
        pr_integrator = Integrator(integrator[1])

        # Read all the PRs integrator reviewed before
        if date_window == 0:
            query1 = "SELECT pr_id, pull_number, requester_login, title, description, created_date, merged_date, " \
                     "integrator_login, files " \
                     "FROM pull_request " \
                     "WHERE merged_date < timestamp('%s') AND integrator_login = '%s'" % \
                     (new_pr.created_date, pr_integrator.integrator_login)
            integrator_reviewed_prs = spark.sql(query1).collect()
        else:
            query1 = "SELECT pr_id, pull_number, requester_login, title, description, created_date, merged_date, " \
                     "integrator_login, files " \
                     "FROM pull_request " \
                     "WHERE merged_date < timestamp('%s') " \
                     "AND merged_date > timestamp('%s') " \
                     "AND integrator_login = '%s'" % \
                     (new_pr.created_date, new_pr.created_date - timedelta(days=date_window),
                      pr_integrator.integrator_login)
            integrator_reviewed_prs = spark.sql(query1).collect()

        for integrator_reviewed_pr in integrator_reviewed_prs:
            old_pr = PullRequest(integrator_reviewed_pr)
            old_pr_file_paths = old_pr.files

            # Calculate file path similarity
            for new_pr_file_path in new_pr.files:
                for file_path in old_pr_file_paths:
                    number_of_file_combinations = len(old_pr_file_paths) * len(new_pr.files)
                    max_file_path_length = max(len(new_pr_file_path.split("/")), len(file_path.split("/")))
                    divider = max_file_path_length * number_of_file_combinations

                    pr_integrator.longest_common_prefix_score += \
                        (longest_common_prefix(new_pr_file_path, file_path) / divider)
                    pr_integrator.longest_common_suffix_score += \
                        (longest_common_suffix(new_pr_file_path, file_path) / divider)
                    pr_integrator.longest_common_sub_string_score += \
                        (longest_common_sub_string(new_pr_file_path, file_path) / divider)
                    pr_integrator.longest_common_sub_sequence_score += \
                        (longest_common_sub_sequence(new_pr_file_path, file_path) / divider)

            # Calculate cosine similarity of title
            pr_integrator.pr_title_similarity += cos_similarity(new_pr.title, old_pr.title)

            # Calculate cosine similarity of description
            if new_pr.description != "" and old_pr.description != "":
                pr_integrator.pr_description_similarity += cos_similarity(new_pr.description, old_pr.description)

            # Calculate activeness of the integrator
            pr_integrator.activeness += calculate_integrator_activeness(new_pr, old_pr)

        row = {'new_pr_id': new_pr.pr_id,
               'new_pr_number': new_pr.pull_number,
               'integrator': pr_integrator.integrator_login,
               'lcp': pr_integrator.longest_common_prefix_score,
               'lcs': pr_integrator.longest_common_suffix_score,
               'lc_substr': pr_integrator.longest_common_sub_string_score,
               'ls_subseq': pr_integrator.longest_common_sub_sequence_score,
               'cos_title': pr_integrator.pr_title_similarity,
               'cos_description': pr_integrator.pr_description_similarity,
               'activeness': pr_integrator.activeness,
               'file_similarity': pr_integrator.longest_common_prefix_score +
                                  pr_integrator.longest_common_suffix_score +
                                  pr_integrator.longest_common_sub_string_score +
                                  pr_integrator.longest_common_sub_sequence_score,
               'text_similarity': pr_integrator.pr_title_similarity + pr_integrator.pr_description_similarity}
        df = df.append(row, ignore_index=True)
    return df


def calculate_scores_for_all_prs(offset, limit, date_window=0):
    logging.basicConfig(level=logging.INFO, filename='app.log', format='%(name)s - %(levelname)s - %(message)s')

    query1 = "SELECT pr_id, pull_number, requester_login, title, description, created_date, merged_date, " \
             "integrator_login, files " \
             "FROM pull_request " \
             "WHERE pr_id > '%s' and pr_id <= '%s' " \
             "ORDER BY pr_id " \
             "LIMIT %d" % (offset, offset + limit, limit)
    all_prs = spark.sql(query1)

    total_prs = 0
    df = pd.DataFrame()

    for new_pr in all_prs.collect():
        total_prs += 1
        new_pr = PullRequest(new_pr)
        df = calculate_scores(df, new_pr, date_window)
        print(str(date_window) + "_" + str(new_pr.pr_id))  # TODO: Remove this
        logging.info(str(date_window) + "_" + str(new_pr.pr_id))
    df.to_csv(str(date_window) + "_" + database + "_all_integrator_scores_for_each_test_pr.csv", index=False)


initialise_app('akka')
calculate_scores_for_all_prs(600, 5, 7)
calculate_scores_for_all_prs(600, 5, 15)
calculate_scores_for_all_prs(600, 5, 30)
calculate_scores_for_all_prs(600, 5, 60)
calculate_scores_for_all_prs(600, 5, 120)
