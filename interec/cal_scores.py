import logging

import pandas as pd

from interec.activeness.integrator_activeness import add_activeness_ranking
from interec.string_compare.string_compare import add_file_path_similarity_ranking
from interec.text_similarity.cos_similarity import add_text_similarity_ranking
from pyspark.sql import SparkSession
from interec.entities.PullRequest import PullRequest

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


def generate_ranked_list(data_frame, alpha, beta, gamma):
    add_file_path_similarity_ranking(data_frame)
    add_text_similarity_ranking(data_frame)
    add_activeness_ranking(data_frame)

    data_frame['combined_score'] = data_frame['std_file_similarity']*alpha + data_frame['std_text_similarity']*beta + \
                                   data_frame['std_activeness']*gamma
    data_frame["final_rank"] = data_frame["combined_score"].rank(method='min', ascending=False)
    return data_frame


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


def standardize_score(score, min_val, max_val):
    new_value = ((score - min_val)*100)/(max_val - min_val)
    return new_value


def test_accuracy_for_all_prs(main_data_csv_file_name, offset, limit):
    logging.basicConfig(level=logging.INFO, filename='app.log', format='%(name)s - %(levelname)s - %(message)s')

    main_df = pd.read_csv(main_data_csv_file_name)
    # TODO: standardise data
    act_min = main_df['activeness'].min()
    act_max = main_df['activeness'].max()
    file_sim_min = main_df['file_similarity'].min()
    file_sim_max = main_df['file_similarity'].max()
    txt_sim_min = main_df['text_similarity'].min()
    txt_sim_max = main_df['text_similarity'].max()

    main_df['std_activeness'] = \
        main_df['activeness'].apply(standardize_score, args=(act_min, act_max))
    main_df['std_file_similarity'] = \
        main_df['file_similarity'].apply(standardize_score, args=(file_sim_min, file_sim_max))
    main_df['std_text_similarity'] = \
        main_df['text_similarity'].apply(standardize_score, args=(txt_sim_min, txt_sim_max))
    
    query1 = "SELECT pr_id, pull_number, requester_login, title, description, created_date, merged_date, " \
             "integrator_login, files " \
             "FROM pull_request " \
             "WHERE pr_id > '%s' and pr_id <= '%s' " \
             "ORDER BY pr_id " \
             "LIMIT %d" % (offset, offset + limit, limit)
    all_prs = spark.sql(query1)

    flag = True
    for i in range(1, 9):
        for j in range(1, 9):
            for k in range(1, 9):
                if i != 0 and j != 0 and k != 0 and i + j + k == 10:
                    total_prs = 0
                    cmb_accuracy_array = [0, 0, 0]
                    file_accuracy_array = [0, 0, 0]
                    txt_accuracy_array = [0, 0, 0]
                    act_accuracy_array = [0, 0, 0]

                    print("")
                    print("---------------------------------------------------------------------------")
                    print("alpha= " + str(i / 10) + " beta= " + str(j / 10) + " gamma= " + str(k / 10))

                    for new_pr in all_prs.collect():
                        total_prs += 1
                        new_pr = PullRequest(new_pr)

                        scores_df = main_df.loc[main_df['new_pr_id'] == new_pr.pr_id].copy()

                        # print(new_pr.pr_id)

                        ranked_data_frame = generate_ranked_list(scores_df, i / 10, j / 10, k / 10)

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
                    if flag:
                        print("File Path Accuracy        " + str(avg_file_path_top1_accuracy) + "          " +
                              str(avg_file_path_top3_accuracy) + "         " + str(avg_file_path_top5_accuracy))
                        print("Text Accuracy             " + str(avg_text_top1_accuracy) + "          " +
                              str(avg_text_top3_accuracy) + "         " + str(avg_text_top5_accuracy))
                        print("Activeness Accuracy       " + str(avg_act_top1_accuracy) + "          " +
                              str(avg_act_top3_accuracy) + "         " + str(avg_act_top5_accuracy))
                    flag = False


initialise_app('akka')
test_accuracy_for_all_prs('akka_all_integrator_scores_for_each_test_pr.csv', 600, 5)
