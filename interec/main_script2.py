import pandas as pd
import logging

from pyspark.sql import SparkSession
from interec.activeness.integrator_activeness import calculate_integrator_activeness
from interec.entities.Integrator import Integrator
from interec.entities.PullRequest import PullRequest
from interec.text_similarity.cos_similarity import cos_similarity
from interec.string_compare.string_compare import longest_common_prefix, longest_common_suffix, \
    longest_common_sub_string, longest_common_sub_sequence

database = 'rails'
spark = ""
all_prs_df = ""
all_integrators_df = ""
all_integrators = ""


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


def calculate_scores(df, new_pr):
    # Calculate scores for each integrator
    for integrator in all_integrators:
        pr_integrator = Integrator(integrator[1])

        # Read all the PRs integrator reviewed before
        query1 = "SELECT pr_id, pull_number, requester_login, title, description, created_date, merged_date, " \
                 "integrator_login, files " \
                 "FROM pull_request " \
                 "WHERE merged_date < timestamp('%s') AND integrator_login = '%s'" % \
                 (new_pr.created_date, pr_integrator.integrator_login)
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


def calculate_scores_for_all_prs(offset, limit):
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
        df = calculate_scores(df, new_pr)
        print(new_pr.pr_id)  # TODO: Remove this
    df.to_csv(database + "_all_integrator_scores_for_each_test_pr.csv", index=False)


initialise_app('bitcoin')
calculate_scores_for_all_prs(2000, 3)
