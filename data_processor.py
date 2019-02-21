import string

import numpy as np
import pandas as pd
import pymysql
from nltk.corpus import stopwords
from nltk.stem.porter import *
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.metrics import classification_report
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import LinearSVC, SVC

# Connection to MySQL  database
connection = pymysql.connect(host='localhost', port=3306, user='root', passwd='', db='rails')

try:
    with connection.cursor() as cursor:
        # Read records
        query1 = "SELECT * FROM pull_request LIMIT 6156"
        df1 = pd.read_sql(query1, connection)

        query2 = "SELECT * FROM pull_request LIMIT 3000 OFFSET 6156"
        df2 = pd.read_sql(query2, connection)
finally:
    connection.close()

labels1 = df1['integrator_login']
labels2 = df2['integrator_login']

df1.drop(['pr_id', 'pull_number', 'created_date', 'merged_date', 'integrator_login', 'total_lines',
          'developer_type'], axis=1, inplace=True)

df2.drop(['pr_id', 'pull_number', 'created_date', 'merged_date', 'integrator_login', 'total_lines',
          'developer_type'], axis=1, inplace=True)


def rearrange_file_paths(file_paths_string):
    files = file_paths_string.split("|")
    new_file_string = ' '.join(files)
    return new_file_string


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


# TODO persist data to a dump file


df1['files'] = df1['files'].apply(rearrange_file_paths)
df2['files'] = df2['files'].apply(rearrange_file_paths)

X_train, X_test, y_train, y_test = df1, df2, labels1, labels2

numeric_features = ['first_pull', 'latest_time', 'num_of_commits', 'num_of_added_lines', 'num_of_deleted_lines',
                    'num_of_changed_files', 'requester_follows_core_team', 'core_team_follows_requester']
numeric_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='median'))])
# ('scaler', StandardScaler())])

categorical_features = ['requester_login']
categorical_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
    ('onehot', OneHotEncoder(handle_unknown='ignore'))])

preprocessor = ColumnTransformer(
    transformers=[
        ('num', numeric_transformer, numeric_features),
        ('cat', categorical_transformer, categorical_features),
        ('titl', TfidfVectorizer(analyzer=text_process), 'title'),
        ('desc', TfidfVectorizer(analyzer=text_process), 'description'),
        ('fls', CountVectorizer(), 'files')
    ])

# X = preprocessor.fit_transform(X_train, y_train)
# X.shape

# clf = Pipeline(steps=[('preprocessor', preprocessor),
#                       ('classifier', MultinomialNB())])

clf = Pipeline(steps=[('preprocessor', preprocessor),
                      ('svc', SVC())])  # max_iter=20000

# clf.fit(X_train, y_train)
#
# clf.score(X_train, y_train)
# #
# # # from sklearn.model_selection import KFold, cross_val_score
# # # kf = KFold(n_splits=5, shuffle=True, random_state=123)
# # # cross_val_score(clf, X_train, y_train, cv=kf).mean()
# #
# predicted = clf.predict(X_test)
# print("Accuracy ")
# print(np.mean(predicted == y_test))
#
# # train_labels = ['arthurnn', 'arunagw', 'carlosantoniodasilva',
# #                 'chancancode', 'claudiob', 'dhh', 'eileencodes', 'fxn',
# #                 'guilleiguaran', 'jeremy', 'kaspth', 'matthewd',
# #                 'pixeltrix', 'rafaelfranca', 'robin850', 'schneems', 'senny',
# #                 'seuros', 'sgrif', 'spastorino', 'tenderlove', 'vijaydev', 'zzak']
# #
# print(classification_report(predicted, y_test))
#
param_grid = {'svc__C': [0.1, 1, 10, 100, 1000], 'svc__gamma': [1, 0.1, 0.01, 0.001, 0.0001],
              'svc__kernel': ['linear', 'poly', 'rbf', 'sigmoid', 'precomputed']}
grid = GridSearchCV(clf, param_grid, refit=True, verbose=3, error_score=0, cv=2)
grid.fit(X_train, y_train)

print("Best params")
print(grid.best_params_)
print("Best estimator ")
print(grid.best_estimator_)

grid_predictions = grid.predict(X_test)
print(classification_report(y_test, grid_predictions))
