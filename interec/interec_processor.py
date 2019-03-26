import logging
from datetime import timedelta

import pandas as pd

from interec.accuracy_calculation.accuracy_calculation import AccuracyCalculator
from interec.activeness.integrator_activeness import ActivenessCalculator
from interec.entities.integrator import Integrator
from interec.string_compare.file_path_similarity import FilePathSimilarityCalculator
from interec.text_similarity.text_similarity import TextSimilarityCalculator
from pyspark.sql import SparkSession
from interec.entities.pull_request import PullRequest


class InterecProcessor:
    def __init__(self, database_name):
        self.database = database_name
        self.spark = ""
        self.all_prs_df = ""
        self.all_integrators_df = ""
        self.all_integrators = ""
        self.file_path_similarity_calculator = FilePathSimilarityCalculator()
        self.activeness_calculator = ActivenessCalculator(const_lambda=-1)
        self.text_similarity_calculator = TextSimilarityCalculator()
        self.__initialise_app()
        self.accuracy_calculator = AccuracyCalculator(self.database, self.spark, self.all_prs_df,
                                                      self.all_integrators_df, self.all_integrators)
        self.alpha = 0
        self.beta = 0
        self.gamma = 0
        self.time_window = 0

    def __initialise_app(self):
        # Create a spark session
        self.spark = SparkSession \
            .builder \
            .master('local') \
            .appName("Interec") \
            .getOrCreate()

        # Read table pull_request
        self.all_prs_df = self.spark.read \
            .format("jdbc") \
            .option("url", "jdbc:mysql://localhost:3306/" + self.database) \
            .option("driver", 'com.mysql.cj.jdbc.Driver') \
            .option("dbtable", "pull_request") \
            .option("user", "root") \
            .option("password", "") \
            .load()

        # Read table integrator
        self.all_integrators_df = self.spark.read \
            .format("jdbc") \
            .option("url", "jdbc:mysql://localhost:3306/" + self.database) \
            .option("driver", 'com.mysql.cj.jdbc.Driver') \
            .option("dbtable", "integrator") \
            .option("user", "root") \
            .option("password", "") \
            .load()

        self.all_prs_df.createOrReplaceTempView("pull_request")
        self.all_integrators_df.createOrReplaceTempView("integrator")

        # Get all the integrators for the project
        query = "SELECT * FROM integrator"
        self.all_integrators = self.spark.sql(query).collect()

    def __calculate_scores(self, df, new_pr, date_window=0):
        # Calculate scores for each integrator
        for integrator in self.all_integrators:
            pr_integrator = Integrator(integrator[1])

            # Read all the PRs integrator reviewed before
            if date_window == 0:
                query1 = "SELECT pr_id, pull_number, requester_login, title, description, created_date, merged_date, " \
                         "integrator_login, files " \
                         "FROM pull_request " \
                         "WHERE merged_date < timestamp('%s') AND integrator_login = '%s'" % \
                         (new_pr.created_date, pr_integrator.integrator_login)
                integrator_reviewed_prs = self.spark.sql(query1).collect()
            else:
                query1 = "SELECT pr_id, pull_number, requester_login, title, description, created_date, merged_date, " \
                         "integrator_login, files " \
                         "FROM pull_request " \
                         "WHERE merged_date < timestamp('%s') " \
                         "AND merged_date > timestamp('%s') " \
                         "AND integrator_login = '%s'" % \
                         (new_pr.created_date, new_pr.created_date - timedelta(days=date_window),
                          pr_integrator.integrator_login)
                integrator_reviewed_prs = self.spark.sql(query1).collect()

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
                            (self.file_path_similarity_calculator.longest_common_prefix(new_pr_file_path, file_path)
                             / divider)
                        pr_integrator.longest_common_suffix_score += \
                            (self.file_path_similarity_calculator.longest_common_suffix(new_pr_file_path, file_path)
                             / divider)
                        pr_integrator.longest_common_sub_string_score += \
                            (self.file_path_similarity_calculator.longest_common_sub_string(new_pr_file_path, file_path)
                             / divider)
                        pr_integrator.longest_common_sub_sequence_score += \
                            (self.file_path_similarity_calculator.longest_common_sub_sequence(new_pr_file_path,
                                                                                              file_path) / divider)

                # Calculate cosine similarity of title
                pr_integrator.pr_title_similarity \
                    += self.text_similarity_calculator.cos_similarity(new_pr.title, old_pr.title)

                # Calculate cosine similarity of description
                if new_pr.description != "" and old_pr.description != "":
                    pr_integrator.pr_description_similarity \
                        += self.text_similarity_calculator.cos_similarity(new_pr.description, old_pr.description)

                # Calculate activeness of the integrator
                pr_integrator.activeness += self.activeness_calculator.calculate_integrator_activeness(new_pr, old_pr)

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

    def __calculate_scores_for_all_prs(self, offset, limit, date_window=0):
        logging.basicConfig(level=logging.INFO, filename='app.log', format='%(name)s - %(levelname)s - %(message)s')

        query1 = "SELECT pr_id, pull_number, requester_login, title, description, created_date, merged_date, " \
                 "integrator_login, files " \
                 "FROM pull_request " \
                 "WHERE pr_id > '%s' and pr_id <= '%s' " \
                 "ORDER BY pr_id " \
                 "LIMIT %d" % (offset, offset + limit, limit)
        all_prs = self.spark.sql(query1)

        total_prs = 0
        df = pd.DataFrame()

        for new_pr in all_prs.collect():
            total_prs += 1
            new_pr = PullRequest(new_pr)
            df = self.__calculate_scores(df, new_pr, date_window)
            print(str(date_window) + "_" + str(new_pr.pr_id))  # TODO: Remove this
            logging.info(str(date_window) + "_" + str(new_pr.pr_id))
        df.to_csv(str(date_window) + "_" + self.database + "_all_integrator_scores_for_each_test_pr.csv", index=False)
        return df

    def generate_ranked_list(self, data_frame, alpha, beta, gamma):
        self.file_path_similarity_calculator.add_file_path_similarity_ranking(data_frame)
        self.text_similarity_calculator.add_text_similarity_ranking(data_frame)
        self.activeness_calculator.add_activeness_ranking(data_frame)

        data_frame['combined_score'] = data_frame['std_file_similarity'] * alpha + \
            data_frame['std_text_similarity'] * beta + data_frame['std_activeness'] * gamma
        data_frame["final_rank"] = data_frame["combined_score"].rank(method='min', ascending=False)
        return data_frame

    def get_weight_combinations_for_factors(self, offset, limit, main_data_frame=None, main_data_csv_file_name=None,
                                            use_csv_file=False):
        if use_csv_file:
            if main_data_csv_file_name is None:
                print("main_data_csv_file_name parameter is none!")
                exit(0)
            main_df = pd.read_csv(main_data_csv_file_name)
        else:
            if main_data_frame is None:
                print("main_data_frame parameter is none!")
                exit(0)
                # TODO: Exception handling
            main_df = main_data_frame

        self.accuracy_calculator.test_weight_combination_accuracy_for_all_prs(interec_processor=self, offset=offset,
                                                                              limit=limit, main_data_frame=main_df)

    def calculate_scores_and_get_weight_combinations_for_factors(self, offset, limit):
        df = self.__calculate_scores_for_all_prs(offset, limit)
        self.get_weight_combinations_for_factors(offset, limit, df, use_csv_file=False)

    def set_weight_combination_for_factors(self, alpha, beta, gamma, time_window):
        return True

    def add_pr_to_db(self, pr_number, requester_login, title, description, created_date, merged_date, files,
                     integrator_login=None):
        return True

    def add_reviewed_integrator_to_pr(self, pr_number, integrator_login):
        return True

    def get_pr_details(self, pr_number):
        return True

    def get_related_integrators_for_pr(self, pr_number, requester_login, title, description, created_date, merged_date,
                                       files):
        return True

# TODO: in all the 4 databases make the 'integrator_login' field can be null
# initialise_app('akka')
# test_accuracy_for_all_prs('akka_all_integrator_scores_for_each_test_pr.csv', 600, 5)
