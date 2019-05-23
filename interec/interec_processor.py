"""
interec_processor.py
====================================
The core of the InteRec system
"""
import interec_config as icfg
import logging
from datetime import timedelta, datetime

import pandas as pd
import pymysql

from interec.accuracy_calculation.accuracy_calculation import AccuracyCalculator
from interec.activeness.integrator_activeness import ActivenessCalculator
from interec.entities.integrator import Integrator
from interec.string_compare.file_path_similarity import FilePathSimilarityCalculator
from interec.text_similarity.text_similarity import TextSimilarityCalculator
from pyspark.sql import SparkSession
from interec.entities.pull_request import PullRequest


class InterecProcessor:
    """
    This is the main class for the InteRec system. This class handles all the major operations in the system

    """
    def __init__(self):
        self.database = icfg.mysql['db']
        self.spark = ""
        self.all_prs_df = ""
        self.all_integrators_df = ""
        self.all_integrators = ""
        self.pr_count = 0
        self.integrator_count = 0
        self.file_path_similarity_calculator = FilePathSimilarityCalculator()
        self.activeness_calculator = ActivenessCalculator(const_lambda=-1)
        self.text_similarity_calculator = TextSimilarityCalculator()
        self.__initialise_app()
        self.accuracy_calculator = AccuracyCalculator(spark=self.spark)
        self.alpha = icfg.system_defaults['alpha']
        self.beta = icfg.system_defaults['beta']
        self.gamma = icfg.system_defaults['gamma']
        self.date_window = icfg.system_constants['date_window']
        logging.basicConfig(level=logging.INFO, filename='app.log', format='%(asctime)s-%(name)s-%(levelname)s '
                                                                           '- %(message)s')
        logging.info("Interec Processor created")

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
            .option("url", "jdbc:mysql://" + icfg.mysql['host'] + "/" + self.database) \
            .option("driver", 'com.mysql.cj.jdbc.Driver') \
            .option("dbtable", icfg.mysql['pr_table']) \
            .option("user", icfg.mysql['user']) \
            .option("password", icfg.mysql['password']) \
            .load()

        # Read table integrator
        self.all_integrators_df = self.spark.read \
            .format("jdbc") \
            .option("url", "jdbc:mysql://" + icfg.mysql['host'] + "/" + self.database) \
            .option("driver", 'com.mysql.cj.jdbc.Driver') \
            .option("dbtable", icfg.mysql['integrator_table']) \
            .option("user", icfg.mysql['user']) \
            .option("password", icfg.mysql['password']) \
            .load()

        self.all_prs_df.createOrReplaceTempView("pull_request")
        self.all_integrators_df.createOrReplaceTempView("integrator")

        # Get all the integrators for the project
        query = "SELECT * FROM integrator"
        self.all_integrators = self.spark.sql(query).collect()

        # Count the number of PRs
        self.pr_count = self.all_prs_df.count()

        # Count the number of integrators
        self.integrator_count = self.all_integrators_df.count()

    def __calculate_scores(self, df, new_pr, date_window=120):
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
                            (self.file_path_similarity_calculator.longest_common_prefix_similarity(
                                new_pr_file_path, file_path) / divider)
                        pr_integrator.longest_common_suffix_score += \
                            (self.file_path_similarity_calculator.longest_common_suffix_similarity(
                                new_pr_file_path, file_path) / divider)
                        pr_integrator.longest_common_sub_string_score += \
                            (self.file_path_similarity_calculator.longest_common_sub_string_similarity(
                                new_pr_file_path, file_path) / divider)
                        pr_integrator.longest_common_sub_sequence_score += \
                            (self.file_path_similarity_calculator.longest_common_sub_sequence_similarity(
                                new_pr_file_path, file_path) / divider)

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

    def __calculate_scores_for_all_prs(self, offset, limit, date_window=120):
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
            print("Scores calculated for: " + str(date_window) + "_" + str(new_pr.pr_id))
            logging.info("Scores calculated for: " + str(date_window) + "_" + str(new_pr.pr_id))
        df.to_csv(str(date_window) + "_" + self.database + "_all_integrator_scores_for_each_test_pr.csv", index=False)
        return df

    @staticmethod
    def __standardize_score(score, min_val, max_val):
        if (max_val - min_val) == 0:
            new_value = 0
        else:
            new_value = ((score - min_val) * 100) / (max_val - min_val)
        return new_value

    def __add_standard_scores_to_data_frame(self, main_df):
        act_min = main_df['activeness'].min()
        act_max = main_df['activeness'].max()
        file_sim_min = main_df['file_similarity'].min()
        file_sim_max = main_df['file_similarity'].max()
        txt_sim_min = main_df['text_similarity'].min()
        txt_sim_max = main_df['text_similarity'].max()

        main_df['std_activeness'] = \
            main_df['activeness'].apply(self.__standardize_score, args=(act_min, act_max))
        main_df['std_file_similarity'] = \
            main_df['file_similarity'].apply(self.__standardize_score, args=(file_sim_min, file_sim_max))
        main_df['std_text_similarity'] = \
            main_df['text_similarity'].apply(self.__standardize_score, args=(txt_sim_min, txt_sim_max))

        return main_df

    def generate_ranked_list(self, data_frame, alpha, beta, gamma):
        logging.info("Generating ranked list started")
        self.file_path_similarity_calculator.add_file_path_similarity_ranking(data_frame)
        self.text_similarity_calculator.add_text_similarity_ranking(data_frame)
        self.activeness_calculator.add_activeness_ranking(data_frame)

        data_frame = self.__add_standard_scores_to_data_frame(data_frame)
        data_frame['combined_score'] = (data_frame['std_file_similarity'] * alpha) + \
                                       (data_frame['std_text_similarity'] * beta) + \
                                       (data_frame['std_activeness'] * gamma)
        data_frame["final_rank"] = data_frame["combined_score"].rank(method='min', ascending=False)
        logging.info("Generating ranked list finished")
        return data_frame

    def get_weight_combinations_for_factors(self, offset, limit, main_data_frame=None, main_data_csv_file_name=None,
                                            use_csv_file=False):
        offset = int(offset)
        limit = int(limit)
        if use_csv_file:
            if main_data_csv_file_name is None:
                logging.error("main_data_csv_file_name parameter is none!")
            logging.info("Getting weight combinations for factors for csv file:" + str(main_data_csv_file_name))
            main_df = pd.read_csv(main_data_csv_file_name)
        else:
            if main_data_frame is None:
                logging.error("main_data_frame parameter is none!")
            main_df = main_data_frame

        return self.accuracy_calculator.test_weight_combination_accuracy_for_all_prs(interec_processor=self,
                                                                                     offset=offset, limit=limit,
                                                                                     main_data_frame=main_df)

    def check_pr_number_availability(self, pr_number):
        logging.info("Checking availability for PR number " + str(pr_number) + " started")
        query1 = "SELECT pr_id, pull_number, requester_login, title, description, created_date, merged_date, " \
                 "integrator_login, files " \
                 "FROM pull_request " \
                 "WHERE pull_number='%s'" % pr_number
        result = self.spark.sql(query1)
        if len(result.collect()) == 0:
            return False
        else:
            return True

    def calculate_scores_and_get_weight_combinations_for_factors(self, offset, limit):
        """
        This function calculates scores for every PR and provides accuracy for each factor weight combination.

        :EXAMPLE:

        >>> interec.calculate_scores_and_get_weight_combinations_for_factors(600, 300)

        :param offset: One less than starting PR number which scores are needed to be calculated
        :type offset: int
        :param limit: Limit of the PRs needed to be considered when calculating scores from the start PR number
        :type limit: int
        :return: Accuracy for each factor weight combination in terms of top1, top3, top5 accuracy and MRR
        :rtype: object
        """
        logging.info("Calculating scores and getting weight combinations for factors started")
        offset = int(offset)
        limit = int(limit)
        df = self.__calculate_scores_for_all_prs(offset, limit)
        logging.info("Calculating scores and getting weight combinations for factors finished")
        return self.get_weight_combinations_for_factors(offset, limit, df, use_csv_file=False)

    def set_weight_combination_for_factors(self, alpha, beta, gamma, date_window=120):
        """
        This function sets the weights for each factor(file path similarity, text similarity, activeness) of the system.
        These weights are used to determine the final score for the integrator. If date_window is not set default value
        will be considered.

        :EXAMPLE:

        >>> interec.set_weight_combination_for_factors(0.1, 0.2, 0.7)

        :param alpha: Weight for file path similarity score
        :type alpha: float
        :param beta: Weight for text similarity score
        :type beta: float
        :param gamma: Weight for activeness score
        :type gamma: float
        :param date_window: (optional) Dates needed to be considered back from PR created date to calculate scores
        :return: Whether the operation is successful or not
        :rtype: bool
        """
        self.alpha = float(alpha)
        self.beta = float(beta)
        self.gamma = float(gamma)
        self.date_window = date_window
        logging.info("Setting weights for factors finished. alpha: " + str(alpha) + " beta: " + str(beta) + " gamma: "
                     + str(gamma))

    def add_pr_to_db(self, pr_number, requester_login, title, description, created_date_time, merged_date_time,
                     integrator_login, files):
        """
        This function adds a already reviewed and merged pr to the database.

        :EXAMPLE:

        >>> interec.add_pr_to_db(10, 'John', 'PR Title', 'PR Description', '2019-03-10 17:52:31', '2019-03-11 19:52:31', 'philip', 'abc.js|def.js|ghi.js')

        :param pr_number: PR id number
        :type pr_number: int
        :param requester_login: Contributor username
        :type requester_login: String
        :param title: Title of the PR
        :type title: String
        :param description: Description of the PR
        :type description: String
        :param created_date_time: PR created date and the time
        :type created_date_time: String
        :param merged_date_time: PR merged date and the time
        :type merged_date_time: String
        :param integrator_login: PR integrator username
        :type integrator_login: String
        :param files: File paths of the PR
        :type files: String
        :return: Top five integrators data frame
        :rtype: DataFrame
        """
        logging.info("Adding PR " + str(pr_number) + " to the database started")
        created_date_time = datetime.strptime(created_date_time, '%Y-%m-%d %H:%M:%S')
        merged_date_time = datetime.strptime(merged_date_time, '%Y-%m-%d %H:%M:%S')
        # Connection to MySQL  database
        connection = pymysql.connect(host='localhost', port=3306, user='root', passwd='', db=self.database)
        try:
            with connection.cursor() as cursor:
                # save pull-request to the database
                sql = "INSERT INTO pull_request (pull_number, requester_login, title, description, created_date," \
                      "merged_date, integrator_login, files) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                inputs = (pr_number, requester_login, title, description, created_date_time, merged_date_time,
                          integrator_login, files)
                cursor.execute(sql, inputs)
        finally:
            connection.commit()
            connection.close()

        logging.info("Adding PR " + str(pr_number) + " to the database successful")

        # update the number of PRs
        self.pr_count = self.all_prs_df.count()

    def get_pr_details(self, pr_number):
        """
        This function provides details of a PR.

        :EXAMPLE:

        >>> interec.get_pr_details(10)

        :param pr_number: PR id number
        :type pr_number: int
        :return: Details of the PR
        :rtype: list
        """
        logging.info("Getting PR details for PR " + str(pr_number) + " started")
        query1 = "SELECT pr_id, pull_number, requester_login, title, description, created_date, merged_date, " \
                 "integrator_login, files " \
                 "FROM pull_request " \
                 "WHERE pull_number='%s'" % pr_number
        result = self.spark.sql(query1)
        details = result.collect()[0]
        logging.info("PR details for PR " + str(pr_number) + " presented")
        return details

    def get_related_integrators_for_pr(self, pr_number, requester_login, title, description, created_date_time, files):
        """
        This function calculates scores for each factor for each integrator and provides a ranked data frame which
        includes top five integrators.

        :EXAMPLE:

        >>> interec.get_related_integrators_for_pr(10, 'John', 'PR Title', 'PR Description', '2019-03-10 17:52:31', 'abc.js|def.js|ghi.js')

        :param pr_number: PR id number
        :type pr_number: int
        :param requester_login: Contributor username
        :type requester_login: String
        :param title: Title of the PR
        :type title: String
        :param description: Description of the PR
        :type description: String
        :param created_date_time: PR created date and the time
        :type created_date_time: String
        :param files: File paths of the PR
        :type files: String
        :return: Top five integrators data frame
        :rtype: DataFrame
        """
        logging.info("Getting related integrators by PR details for PR " + str(pr_number) + " started")
        created_date_time = datetime.strptime(created_date_time, '%Y-%m-%d %H:%M:%S')
        pr_data = [0, pr_number, requester_login, title, description, created_date_time, 0, " ", files]
        new_pr = PullRequest(pr_data)
        df = pd.DataFrame()
        df = self.__calculate_scores(df, new_pr, self.date_window)
        ranked_df = self.generate_ranked_list(df, self.alpha, self.beta, self.gamma)
        sorted_ranked_data_frame = ranked_df.sort_values('final_rank', ascending=True)
        ranked_five_df = sorted_ranked_data_frame[sorted_ranked_data_frame['final_rank'] <= 5]
        logging.info("Top five integrators for PR " + str(pr_number) + " presented")
        return ranked_five_df

    def get_related_integrators_for_pr_by_pr_number(self, pr_number):
        """
        This function calculates scores for each factor for each integrator and provides a ranked data frame which
        includes top five integrators.

        :EXAMPLE:

        >>> interec.get_related_integrators_for_pr_by_pr_number(10)

        :param pr_number: PR id number
        :type pr_number: int
        :return: Top five integrators data frame
        :rtype: DataFrame
        """
        logging.info("Getting related integrators by PR number for PR" + str(pr_number) + " started")
        pr_details = self.get_pr_details(pr_number)
        new_pr = PullRequest(pr_details)
        df = pd.DataFrame()
        df = self.__calculate_scores(df, new_pr, self.date_window)
        ranked_df = self.generate_ranked_list(df, self.alpha, self.beta, self.gamma)
        sorted_ranked_data_frame = ranked_df.sort_values('final_rank', ascending=True)
        ranked_five_df = sorted_ranked_data_frame[sorted_ranked_data_frame['final_rank'] <= 5]
        logging.info("Top five integrators for PR " + str(pr_number) + " presented")
        return ranked_five_df
