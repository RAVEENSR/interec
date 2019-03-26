import logging

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import GridSearchCV
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler

from interec.activeness.integrator_activeness import calculate_integrator_activeness
from interec.entities.integrator import Integrator
from interec.entities.pull_request import PullRequest
from interec.string_compare.file_path_similarity import longest_common_prefix, longest_common_suffix, \
    longest_common_sub_string, longest_common_sub_sequence
from interec.text_similarity.text_similarity import cos_similarity
from pyspark.sql import SparkSession

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


def calculate_scores(offset, limit):
    df = pd.DataFrame()

    logging.basicConfig(level=logging.INFO, filename='app.log', format='%(name)s - %(levelname)s - %(message)s')

    query1 = "SELECT pr_id, pull_number, requester_login, title, description, created_date, merged_date, " \
             "integrator_login, files " \
             "FROM pull_request " \
             "WHERE pr_id > '%s' and pr_id <= '%s' " \
             "ORDER BY pr_id " \
             "LIMIT %d" % (offset, offset + limit, limit)
    all_prs = spark.sql(query1)

    for test_pr in all_prs.collect():
        test_pr = PullRequest(test_pr)
        print(test_pr.pr_id)
        logging.info(test_pr.pr_id)
        pr_integrator = Integrator(test_pr.integrator_login)
        # Calculate scores for integrator

        # Read all the PRs integrator reviewed before
        query1 = "SELECT pr_id, pull_number, requester_login, title, description, created_date, merged_date, " \
                 "integrator_login, files " \
                 "FROM pull_request " \
                 "WHERE merged_date < timestamp('%s') AND integrator_login = '%s'" % \
                 (test_pr.created_date, pr_integrator.integrator_login)
        integrator_reviewed_prs = spark.sql(query1).collect()

        for integrator_reviewed_pr in integrator_reviewed_prs:
            old_pr = PullRequest(integrator_reviewed_pr)
            old_pr_file_paths = old_pr.files

            # Calculate file path similarity
            for new_pr_file_path in test_pr.files:
                for file_path in old_pr_file_paths:
                    number_of_file_combinations = len(old_pr_file_paths) * len(test_pr.files)
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
            pr_integrator.pr_title_similarity += cos_similarity(test_pr.title, old_pr.title)

            # Calculate cosine similarity of description
            if test_pr.description != "" and old_pr.description != "":
                pr_integrator.pr_description_similarity += cos_similarity(test_pr.description, old_pr.description)

            # Calculate activeness of the integrator
            pr_integrator.activeness += calculate_integrator_activeness(test_pr, old_pr)

        row = {'pr_id': test_pr.pr_id,
               'integrator': pr_integrator.integrator_login,
               'lcp': pr_integrator.longest_common_prefix_score,
               'lcs': pr_integrator.longest_common_suffix_score,
               'lc_substr': pr_integrator.longest_common_sub_string_score,
               'ls_subseq': pr_integrator.longest_common_sub_sequence_score,
               'cos_title': pr_integrator.pr_title_similarity,
               'cos_description': pr_integrator.pr_description_similarity,
               'activeness': pr_integrator.activeness,
               'text_similarity': pr_integrator.pr_title_similarity + pr_integrator.pr_description_similarity,
               'file_similarity': (pr_integrator.longest_common_prefix_score
                                   + pr_integrator.longest_common_suffix_score
                                   + pr_integrator.longest_common_sub_string_score
                                   + pr_integrator.longest_common_sub_sequence_score)
               }
        df = df.append(row, ignore_index=True)
    csv_file_name = database + "_test_pr_stats.csv"
    df.to_csv(csv_file_name, index=False)


def standardize_score(score, min_val, max_val):
    new_value = ((score - min_val)*100)/(max_val - min_val)
    return new_value


def scale_scores(csv_file_name):
    df = pd.read_csv(csv_file_name)
    act_min = df['activeness'].min()
    act_max = df['activeness'].max()
    file_sim_min = df['file_similarity'].min()
    file_sim_max = df['file_similarity'].max()
    txt_sim_min = df['text_similarity'].min()
    txt_sim_max = df['text_similarity'].max()

    df['std_activeness'] = df['activeness'].apply(standardize_score, args=(act_min, act_max))
    df['std_file_similarity'] = df['file_similarity'].apply(standardize_score, args=(file_sim_min, file_sim_max))
    df['std_text_similarity'] = df['text_similarity'].apply(standardize_score, args=(txt_sim_min, txt_sim_max))

    df.to_csv('standardized_' + csv_file_name, index=False)
    return df


def find_weight_factors(train_data_csv_file_name, test_data_csv_file_name):
    train_df = pd.read_csv(train_data_csv_file_name)
    test_df = pd.read_csv(test_data_csv_file_name)

    label_encoder = LabelEncoder()

    train_labels = label_encoder.fit_transform(train_df['integrator'])
    train_feature_set = train_df[['std_activeness', 'std_file_similarity', 'std_text_similarity']]

    test_labels = label_encoder.fit_transform(test_df['integrator'])
    test_feature_set = test_df[['std_activeness', 'std_file_similarity', 'std_text_similarity']]

    numeric_features = ['std_activeness', 'std_file_similarity', 'std_text_similarity']
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median'))])  # ('scaler', StandardScaler())])

    preprocessor = ColumnTransformer(transformers=[
        ('num', numeric_transformer, numeric_features)
    ])

    clf = Pipeline(steps=[('preprocessor', preprocessor),
                          ('classifier', MLPClassifier(  solver='sgd', activation='identity',
                                                       hidden_layer_sizes=(3, 100), tol=0.000000001))])
    # parameter_space = {
    #     'classifier__hidden_layer_sizes': [(3, 11, 33, 50, 100), (3, 11, 50, 100, 33)],
    #     'classifier__activation': ['tanh', 'relu', 'identity', 'logistic'],
    #     'classifier__max_iter': [50000],
    #     'classifier__solver': ['sgd', 'adam', 'lbfgs'],
    #     'classifier__alpha': [0.0001, 0.05, 0.001],
    #     'classifier__learning_rate': ['constant', 'adaptive']
    # }
    # clf = GridSearchCV(clf, parameter_space, n_jobs=-1)
    clf.fit(train_feature_set, train_labels)

    # # Best paramete set
    # print('Best parameters found:\n', clf.best_params_)

    # # All results
    # means = clf.cv_results_['mean_test_score']
    # stds = clf.cv_results_['std_test_score']
    # for mean, std, params in zip(means, stds, clf.cv_results_['params']):
    #     print("%0.3f (+/-%0.03f) for %r" % (mean, std * 2, params))

    y_pred = clf.predict(test_feature_set)
    print(classification_report(test_labels, y_pred))
    print(accuracy_score(test_labels, y_pred))


# initialise_app('scala')
# calculate_scores(0, 640)

# scale_scores('akka_test_pr_stats.csv')
# scale_scores('akka_train_pr_stats.csv')

find_weight_factors('standardized_akka_train_pr_stats.csv', 'standardized_akka_test_pr_stats.csv')
