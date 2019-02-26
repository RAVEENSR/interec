import pandas as pd
import pymysql
import logging

from interec.activeness.integrator_activeness import calculate_integrator_activeness, get_activeness_ranked_list
from interec.entities.Integrator import Integrator
from interec.entities.PullRequest import PullRequest
from interec.text_similarity.cos_similarity import cos_similarity, get_text_similarity_ranked_list
from interec.string_compare.string_compare import longest_common_prefix, longest_common_suffix, \
    longest_common_sub_string, longest_common_sub_sequence, get_file_path_similarity_ranked_list


def calculate_scores(database, new_pr):
    df1 = pd.DataFrame()

    # Connection to MySQL  database
    connection = pymysql.connect(host='localhost', port=3306, user='root', passwd='', db=database)

    # Get all the integrators
    try:
        with connection.cursor() as cursor:
            # Read records to get integrators
            query1 = "SELECT * FROM integrator"
            cursor.execute(query1)
            integrators = cursor.fetchall()
    finally:
        connection.close()

    # Calculate scores for each integrator
    for integrator in integrators:
        pr_integrator = Integrator(integrator.integrator_login)

        # Connection to MySQL  database
        connection = pymysql.connect(host='localhost', port=3306, user='root', passwd='', db=database)

        try:
            with connection.cursor() as cursor:
                # Read all the PRs integrator reviewed before
                query2 = "SELECT * FROM pull_request WHERE merged_date <%s AND integrator_login =%s"
                inputs = (new_pr.created_date.strftime('%Y-%m-%d %H:%M:%S'), integrator.integrator_login)
                cursor.execute(query2, inputs)
                integrator_reviewed_prs = cursor.fetchall()
        finally:
            connection.close()

        for integrator_reviewed_pr in integrator_reviewed_prs:
            old_pr = PullRequest(integrator_reviewed_pr)
            old_pr_file_paths = old_pr.files

            # Calculate file path similarity
            for new_pr_file_path in new_pr.files:
                for file_path in old_pr_file_paths:
                    max_file_path_length = max(len(new_pr_file_path.split("/")), len(file_path.split("/")))
                    pr_integrator.longest_common_prefix_score += \
                        (longest_common_prefix(new_pr_file_path, file_path) / max_file_path_length)
                    pr_integrator.longest_common_suffix_score += \
                        (longest_common_suffix(new_pr_file_path, file_path) / max_file_path_length)
                    pr_integrator.longest_common_sub_string_score += \
                        (longest_common_sub_string(new_pr_file_path, file_path) / max_file_path_length)
                    pr_integrator.longest_common_sub_sequence_score += \
                        (longest_common_sub_sequence(new_pr_file_path, file_path) / max_file_path_length)

            # Calculate cosine similarity of title
            pr_integrator.pr_title_similarity += cos_similarity(new_pr.title, old_pr.title)

            # Calculate cosine similarity of description
            if new_pr.description != "" and old_pr.description != "":
                pr_integrator.pr_description_similarity += cos_similarity(new_pr.description, old_pr.description)

            # Calculate activeness of the integrator
            pr_integrator.activeness = calculate_integrator_activeness(new_pr, old_pr)

            # Calculate number of first pulls merged, total number of prs and total commits
            if old_pr.first_pull == 1:
                pr_integrator.num_of_first_pulls += 1
            pr_integrator.num_of_prs += 1
            pr_integrator.total_commits += old_pr.num_of_commits

        # Calculate first pull similarity and average commits
        if pr_integrator.num_of_prs == 0:
            first_pull_similarity = 0
            average_commits = 0
        else:
            first_pull_similarity = pr_integrator.num_of_first_pulls / pr_integrator.num_of_prs
            average_commits = pr_integrator.total_commits / pr_integrator.num_of_prs

        row = {'lcp': pr_integrator.longest_common_prefix_score,
               'lcs': pr_integrator.longest_common_suffix_score,
               'lc_substr': pr_integrator.longest_common_sub_string_score,
               'ls_subseq': pr_integrator.longest_common_sub_sequence_score,
               'cos_title': pr_integrator.pr_title_similarity,
               'cos_description': pr_integrator.pr_description_similarity,
               'activeness': pr_integrator.activeness,
               'first_pull': first_pull_similarity,
               'avg_commits': average_commits}
        df1 = df1.append(row, ignore_index=True)
    return df1


def combine_ranked_lists(file_path_similarity_ranked_list, text_similarity_ranked_list, activeness_ranked_list):
    return False


def generate_ranked_list(database, new_pr):
    data_frame = calculate_scores(database, new_pr)
    file_path_similarity_ranked_list = get_file_path_similarity_ranked_list(data_frame)
    text_similarity_ranked_list = get_text_similarity_ranked_list(data_frame)
    activeness_ranked_list = get_activeness_ranked_list(data_frame)

    combined_ranked_lists = combine_ranked_lists(file_path_similarity_ranked_list, text_similarity_ranked_list,
                                                 activeness_ranked_list)
    return combined_ranked_lists


def test_accuracy(database, new_pr, top1=True, top3=False, top5=False):
    actual_pr_integrator = new_pr.integrator_login
    ranked_list = generate_ranked_list(database, new_pr)
    return False


def test_accuracy_for_all_prs(database, starting_pr_number, limit):
    # TODO ADD comments for all the scripts
    logging.basicConfig(level=logging.INFO, filename='app.log', format='%(name)s - %(levelname)s - %(message)s')
    # Connection to MySQL  database
    connection = pymysql.connect(host='localhost', port=3306, user='root', passwd='', db=database)

    try:
        with connection.cursor() as cursor:
            # Read records
            query1 = "SELECT * FROM pull_request LIMIT %s OFFSET %s"
            inputs = (limit, starting_pr_number)
            cursor.execute(query1, inputs)
            all_prs = cursor.fetchall()
    finally:
        connection.close()

    for new_pr in all_prs:
        new_pr = PullRequest(new_pr)
        test_accuracy(database, new_pr)
        logging.info(new_pr.pr_id + "-" + test_accuracy)
        print(new_pr.pr_id + "-" + test_accuracy)


test_accuracy_for_all_prs('rails', 0, 2000)
