import pandas as pd
import logging


from pyspark.sql import SparkSession
from interec.activeness.integrator_activeness import calculate_integrator_activeness, add_activeness_ranking
from interec.entities.Integrator import Integrator
from interec.entities.PullRequest import PullRequest
from interec.text_similarity.cos_similarity import cos_similarity, add_text_similarity_ranking
from interec.string_compare.string_compare import longest_common_prefix, longest_common_suffix, \
    longest_common_sub_string, longest_common_sub_sequence, add_file_path_similarity_ranking

database = 'bitcoin'

spark = SparkSession \
    .builder \
    .master('local') \
    .appName("Interec") \
    .getOrCreate()
spark.sparkContext.setLogLevel("WARN")

all_prs_df = spark.read \
    .format("jdbc") \
    .option("url", "jdbc:mysql://localhost:3306/" + database) \
    .option("driver", 'com.mysql.cj.jdbc.Driver') \
    .option("dbtable", "pull_request") \
    .option("user", "root") \
    .option("password", "") \
    .load()
all_prs_df.printSchema()
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

query = "SELECT * FROM integrator"
all_integrators = spark.sql(query).collect()


def calculate_scores(new_pr):
    df1 = pd.DataFrame()

    # Calculate scores for each integrator
    for integrator in all_integrators:
        pr_integrator = Integrator(integrator[1])

        # Read all the PRs integrator reviewed before
        query1 = "SELECT * FROM pull_request WHERE merged_date < timestamp('%s') AND integrator_login = '%s'" % \
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

        row = {'integrator': pr_integrator.integrator_login,
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
    return df1


def combine_ranked_lists(data_frame):
    num_of_non_zero_candidates_in_file_similarity = len(data_frame['file_similarity'].to_numpy().nonzero()[0])
    num_of_non_zero_candidates_in_text_similarity = len(data_frame['text_similarity'].to_numpy().nonzero()[0])
    num_of_non_zero_candidates_in_activeness = len(data_frame['activeness'].to_numpy().nonzero()[0])

    data_frame['combined_score'] = (num_of_non_zero_candidates_in_file_similarity - data_frame['file_path_rank']) + \
                                   (num_of_non_zero_candidates_in_text_similarity - data_frame['text_rank']) + \
                                   (num_of_non_zero_candidates_in_activeness - data_frame['activeness_rank'])
    data_frame["final_rank"] = data_frame["combined_score"].rank(method='min', ascending=False)
    return data_frame


def generate_ranked_list(new_pr):
    data_frame = calculate_scores(new_pr)
    add_file_path_similarity_ranking(data_frame)
    add_text_similarity_ranking(data_frame)
    add_activeness_ranking(data_frame)

    # data_frame.to_csv('pr_stats.csv', index=False)
    combined_ranked_list = combine_ranked_lists(data_frame)
    return combined_ranked_list


def is_in_top_k(ranked_df, actual_pr_integrator):
    is_included = False
    for row in ranked_df.itertuples(index=False):
        if row.integrator == actual_pr_integrator:
            is_included = True
    return is_included


def test_accuracy_by_field(ranked_data_frame, new_pr, column_name='final_rank', top1=True, top3=False, top5=False):
    included_in_top1 = False
    included_in_top3 = False
    included_in_top5 = False
    actual_pr_integrator = new_pr.integrator_login

    sorted_ranked_data_frame = ranked_data_frame.sort_values(column_name, ascending=True)
    accuracy = lambda: None

    if top1:
        ranked_one_df = sorted_ranked_data_frame[sorted_ranked_data_frame[column_name] == 1]
        included_in_top1 = is_in_top_k(ranked_one_df, actual_pr_integrator)
        setattr(accuracy, "top1", included_in_top1)

    if top3:
        ranked_three_df = sorted_ranked_data_frame[sorted_ranked_data_frame[column_name] <= 3]
        included_in_top3 = is_in_top_k(ranked_three_df, actual_pr_integrator)
        setattr(accuracy, "top3", included_in_top3)

    if top5:
        ranked_five_df = sorted_ranked_data_frame[sorted_ranked_data_frame[column_name] <= 5]
        included_in_top5 = is_in_top_k(ranked_five_df, actual_pr_integrator)
        setattr(accuracy, "top5", included_in_top5)

    return accuracy


def test_file_path_similarity_accuracy(ranked_data_frame, new_pr, top1=True, top3=False, top5=False):
    return test_accuracy_by_field(ranked_data_frame, new_pr, 'file_path_rank', top1, top3, top5)


def test_text_similarity_accuracy(ranked_data_frame, new_pr, top1=True, top3=False, top5=False):
    return test_accuracy_by_field(ranked_data_frame, new_pr, 'text_rank', top1, top3, top5)


def test_activeness_accuracy(ranked_data_frame, new_pr, top1=True, top3=False, top5=False):
    return test_accuracy_by_field(ranked_data_frame, new_pr, 'activeness_rank', top1, top3, top5)


def test_combined_accuracy(ranked_data_frame, new_pr, top1=True, top3=False, top5=False):
    return test_accuracy_by_field(ranked_data_frame, new_pr, 'final_rank', top1, top3, top5)


# TODO: add a global variable for database- add getter and setter
# TODO ADD comments like ''' some text ''' for all the scripts
# TODO Implement Recall
# TODO Add a method to a new coming PR- make it applicable for PullRequest object
def test_accuracy_for_all_prs(database, offset, limit):
    logging.basicConfig(level=logging.INFO, filename='app.log', format='%(name)s - %(levelname)s - %(message)s')

    query1 = "SELECT * FROM pull_request " \
             "WHERE pr_id > '%s' and pr_id <= '%s' " \
             "ORDER BY pr_id " \
             "LIMIT %d" % (offset, offset + limit, limit)
    all_prs = spark.sql(query1)

    total_prs = 0
    cmb_accuracy_array = [0, 0, 0]
    file_accuracy_array = [0, 0, 0]
    txt_accuracy_array = [0, 0, 0]
    act_accuracy_array = [0, 0, 0]

    for new_pr in all_prs.collect():
        total_prs += 1
        new_pr = PullRequest(new_pr)
        print(new_pr.pr_id)
        ranked_data_frame = generate_ranked_list(new_pr)
        combined_accuracy = test_combined_accuracy(ranked_data_frame, new_pr, True, True, True)
        file_path_accuracy = test_file_path_similarity_accuracy(ranked_data_frame, new_pr, True, True, True)
        text_accuracy = test_text_similarity_accuracy(ranked_data_frame, new_pr, True, True, True)
        activeness_accuracy = test_activeness_accuracy(ranked_data_frame, new_pr, True, True, True)

        if hasattr(combined_accuracy, 'top1') and combined_accuracy.top1:
            cmb_accuracy_array[0] += 1
        if hasattr(combined_accuracy, 'top3') and combined_accuracy.top3:
            cmb_accuracy_array[1] += 1
        if hasattr(combined_accuracy, 'top5') and combined_accuracy.top5:
            cmb_accuracy_array[2] += 1

        if hasattr(file_path_accuracy, 'top1') and file_path_accuracy.top1:
            file_accuracy_array[0] += 1
        if hasattr(file_path_accuracy, 'top3') and file_path_accuracy.top3:
            file_accuracy_array[1] += 1
        if hasattr(file_path_accuracy, 'top5') and file_path_accuracy.top5:
            file_accuracy_array[2] += 1

        if hasattr(text_accuracy, 'top1') and text_accuracy.top1:
            txt_accuracy_array[0] += 1
        if hasattr(text_accuracy, 'top3') and text_accuracy.top3:
            txt_accuracy_array[1] += 1
        if hasattr(text_accuracy, 'top5') and text_accuracy.top5:
            txt_accuracy_array[2] += 1

        if hasattr(activeness_accuracy, 'top1') and activeness_accuracy.top1:
            act_accuracy_array[0] += 1
        if hasattr(activeness_accuracy, 'top3') and activeness_accuracy.top3:
            act_accuracy_array[1] += 1
        if hasattr(activeness_accuracy, 'top5') and activeness_accuracy.top5:
            act_accuracy_array[2] += 1

    avg_combined_top1_accuracy = cmb_accuracy_array[0]/total_prs
    avg_combined_top3_accuracy = cmb_accuracy_array[1] / total_prs
    avg_combined_top5_accuracy = cmb_accuracy_array[2] / total_prs

    avg_file_path_top1_accuracy = file_accuracy_array[0] / total_prs
    avg_file_path_top3_accuracy = file_accuracy_array[1] / total_prs
    avg_file_path_top5_accuracy = file_accuracy_array[2] / total_prs

    avg_text_top1_accuracy = txt_accuracy_array[0] / total_prs
    avg_text_top3_accuracy = txt_accuracy_array[1] / total_prs
    avg_text_top5_accuracy = txt_accuracy_array[2] / total_prs

    avg_act_top1_accuracy = act_accuracy_array[0] / total_prs
    avg_act_top3_accuracy = act_accuracy_array[1] / total_prs
    avg_act_top5_accuracy = act_accuracy_array[2] / total_prs

    print("---------------------------------------------------------------------------")
    print("                         Top1          Top3            Top5")
    print("Combined Accuracy         " + str(avg_combined_top1_accuracy) + "          " +
          str(avg_combined_top3_accuracy) + "         " + str(avg_combined_top5_accuracy))
    print("File Path Accuracy        " + str(avg_file_path_top1_accuracy) + "          " +
          str(avg_file_path_top3_accuracy) + "         " + str(avg_file_path_top5_accuracy))
    print("Text Accuracy             " + str(avg_text_top1_accuracy) + "          " +
          str(avg_text_top3_accuracy) + "         " + str(avg_text_top5_accuracy))
    print("Activeness Accuracy       " + str(avg_act_top1_accuracy) + "          " +
          str(avg_act_top3_accuracy) + "         " + str(avg_act_top5_accuracy))


test_accuracy_for_all_prs('bitcoin', 2000, 2)
