import logging

from interec.entities.pull_request import PullRequest


class AccuracyCalculator:
    def __init__(self, database, spark, all_prs_df, all_integrators_df, all_integrators):
        logging.basicConfig(level=logging.INFO, filename='app.log', format='%(name)s - %(levelname)s - %(message)s')
        self.database = database
        self.spark = spark
        self.all_prs_df = all_prs_df
        self.all_integrators_df = all_integrators_df
        self.all_integrators = all_integrators

    @staticmethod
    def __is_in_top_k(ranked_df, actual_pr_integrator):
        is_included = False
        for row in ranked_df.itertuples(index=False):
            if row.integrator == actual_pr_integrator:
                is_included = True
        return is_included

    def __test_accuracy_by_field(self, ranked_data_frame, new_pr, column_name='final_rank', top1=True, top3=False,
                               top5=False):
        included_in_top1 = False
        included_in_top3 = False
        included_in_top5 = False
        actual_pr_integrator = new_pr.integrator_login

        sorted_ranked_data_frame = ranked_data_frame.sort_values(column_name, ascending=True)
        accuracy = lambda: None

        if top1:
            ranked_one_df = sorted_ranked_data_frame[sorted_ranked_data_frame[column_name] == 1]
            included_in_top1 = self.__is_in_top_k(ranked_one_df, actual_pr_integrator)
            setattr(accuracy, "top1", included_in_top1)

        if top3:
            ranked_three_df = sorted_ranked_data_frame[sorted_ranked_data_frame[column_name] <= 3]
            included_in_top3 = self.__is_in_top_k(ranked_three_df, actual_pr_integrator)
            setattr(accuracy, "top3", included_in_top3)

        if top5:
            ranked_five_df = sorted_ranked_data_frame[sorted_ranked_data_frame[column_name] <= 5]
            included_in_top5 = self.__is_in_top_k(ranked_five_df, actual_pr_integrator)
            setattr(accuracy, "top5", included_in_top5)

        return accuracy

    def __test_file_path_similarity_accuracy(self, ranked_data_frame, new_pr, top1=True, top3=False, top5=False):
        return self.__test_accuracy_by_field(ranked_data_frame, new_pr, 'file_path_rank', top1, top3, top5)

    def __test_text_similarity_accuracy(self, ranked_data_frame, new_pr, top1=True, top3=False, top5=False):
        return self.__test_accuracy_by_field(ranked_data_frame, new_pr, 'text_rank', top1, top3, top5)

    def __test_activeness_accuracy(self, ranked_data_frame, new_pr, top1=True, top3=False, top5=False):
        return self.__test_accuracy_by_field(ranked_data_frame, new_pr, 'activeness_rank', top1, top3, top5)

    def __test_combined_accuracy(self, ranked_data_frame, new_pr, top1=True, top3=False, top5=False):
        return self.__test_accuracy_by_field(ranked_data_frame, new_pr, 'final_rank', top1, top3, top5)

    # @staticmethod
    # def __standardize_score(score, min_val, max_val):
    #     new_value = ((score - min_val) * 100) / (max_val - min_val)
    #     return new_value
    #
    # def add_standard_scores_to_data_frame(self, main_df):
    #     act_min = main_df['activeness'].min()
    #     act_max = main_df['activeness'].max()
    #     file_sim_min = main_df['file_similarity'].min()
    #     file_sim_max = main_df['file_similarity'].max()
    #     txt_sim_min = main_df['text_similarity'].min()
    #     txt_sim_max = main_df['text_similarity'].max()
    #
    #     main_df['std_activeness'] = \
    #         main_df['activeness'].apply(self.__standardize_score, args=(act_min, act_max))
    #     main_df['std_file_similarity'] = \
    #         main_df['file_similarity'].apply(self.__standardize_score, args=(file_sim_min, file_sim_max))
    #     main_df['std_text_similarity'] = \
    #         main_df['text_similarity'].apply(self.__standardize_score, args=(txt_sim_min, txt_sim_max))
    #
    #     return main_df

    def test_weight_combination_accuracy_for_all_prs(self, interec_processor, offset, limit, main_data_frame):
        # main_df = self.add_standard_scores_to_data_frame(main_data_frame)

        query1 = "SELECT pr_id, pull_number, requester_login, title, description, created_date, merged_date, " \
                 "integrator_login, files " \
                 "FROM pull_request " \
                 "WHERE pr_id > '%s' and pr_id <= '%s' " \
                 "ORDER BY pr_id " \
                 "LIMIT %d" % (offset, offset + limit, limit)
        all_prs = self.spark.sql(query1)

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

                            scores_df = main_data_frame.loc[main_data_frame['new_pr_id'] == new_pr.pr_id].copy()

                            # print(new_pr.pr_id)

                            ranked_data_frame \
                                = interec_processor.generate_ranked_list(scores_df, i / 10, j / 10, k / 10)

                            combined_accuracy \
                                = self.__test_combined_accuracy(ranked_data_frame, new_pr, True, True, True)
                            file_path_accuracy \
                                = self.__test_file_path_similarity_accuracy(ranked_data_frame, new_pr, True, True, True)
                            text_accuracy \
                                = self.__test_text_similarity_accuracy(ranked_data_frame, new_pr, True, True, True)
                            activeness_accuracy \
                                = self.__test_activeness_accuracy(ranked_data_frame, new_pr, True, True, True)

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

                        avg_combined_top1_accuracy = cmb_accuracy_array[0] / total_prs
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
