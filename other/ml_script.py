import logging

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import GridSearchCV
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder


def find_weight_factors(train_data_csv_file_name, test_data_csv_file_name):
    logging.basicConfig(level=logging.INFO, filename='app.log', format='%(name)s - %(levelname)s - %(message)s')

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
                          ('classifier', MLPClassifier(tol=0.000000001))])
    parameter_space = {
        'classifier__hidden_layer_sizes': [(3, 11, 33, 50, 100), (3, 11, 50, 100, 33)],
        'classifier__activation': ['tanh', 'relu', 'identity', 'logistic'],
        'classifier__max_iter': [50000],
        'classifier__solver': ['sgd', 'adam', 'lbfgs'],
        'classifier__alpha': [0.0001, 0.05, 0.001],
        'classifier__learning_rate': ['constant', 'adaptive']
    }
    clf = GridSearchCV(clf, parameter_space, n_jobs=-1)
    clf.fit(train_feature_set, train_labels)

    # Best paramete set
    print('Best parameters found:\n', clf.best_params_)
    logging.info('Best parameters found:\n', clf.best_params_)

    # All results
    means = clf.cv_results_['mean_test_score']
    stds = clf.cv_results_['std_test_score']
    for mean, std, params in zip(means, stds, clf.cv_results_['params']):
        print("%0.3f (+/-%0.03f) for %r" % (mean, std * 2, params))
        logging.info("%0.3f (+/-%0.03f) for %r" % (mean, std * 2, params))

    y_pred = clf.predict(test_feature_set)
    print(classification_report(test_labels, y_pred))
    logging.info(classification_report(test_labels, y_pred))
    print(accuracy_score(test_labels, y_pred))
    logging.info(accuracy_score(test_labels, y_pred))


find_weight_factors('standardized_akka_train_pr_stats.csv', 'standardized_akka_test_pr_stats.csv')
