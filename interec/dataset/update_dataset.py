from datetime import datetime
from github import Github
import pymysql


def update_with_github_api(database, repo):
    # Connection to MySQL  database
    connection = pymysql.connect(host='localhost', port=3306, user='root', passwd='', db=database)

    # Connection to GitHub
    g = Github('91e299613b59fe50950fb110d079c2b7f39c70f8')  # TODO: Remove this
    # Accessing the required repository
    repo = g.get_repo(repo)
    pr_number = 0
    try:
        with connection.cursor() as cursor:
            # Read records
            # sql_1 = "SELECT pull_number FROM pull_request"
            sql_1 = "SELECT pull_number FROM pull_request LIMIT 1320"
            cursor.execute(sql_1)
            result = cursor.fetchall()
            for row in result:
                pull_number = row[0]
                pr = repo.get_pull(pull_number)
                pr_number += 1
                print("" + str(pr_number) + " - " + str(pr))
                num_of_commits = pr.commits
                num_of_changed_files = pr.changed_files
                num_of_added_lines = pr.additions
                num_of_deleted_lines = pr.deletions
                total_lines = num_of_added_lines + num_of_deleted_lines
                created_date = pr.created_at
                description = pr.body
                merged_date = pr.merged_at

                # Update records
                sql_2 = "UPDATE pull_request SET description=%s, created_date =%s, merged_date =%s, " \
                        "num_of_commits =%s, num_of_added_lines =%s, num_of_deleted_lines = %s, total_lines = %s, " \
                        "num_of_changed_files =%s " \
                        "WHERE pull_number= %s"
                inputs = (description, created_date, merged_date, num_of_commits, num_of_added_lines,
                          num_of_deleted_lines, total_lines, num_of_changed_files, pull_number)
                cursor.execute(sql_2, inputs)
        connection.commit()
    finally:
        connection.commit()
        connection.close()


def update_latest_time(latest_date_object, limit, database):
    # Connection to MySQL  database
    connection = pymysql.connect(host='localhost', port=3306, user='root', passwd='', db=database)
    try:
        with connection.cursor() as cursor:
            # Read records
            sql_1 = "SELECT pull_number, merged_date FROM pull_request LIMIT %s"
            cursor.execute(sql_1, limit)
            result = cursor.fetchall()
            for row in result:
                pull_number = row[0]
                latest_time = latest_date_object - row[1]
                if hasattr(latest_time, 'days'):
                    latest_time = latest_time.days
                    if latest_time < 0:
                        latest_time = 0
                else:
                    latest_time = 0
                # Update record
                sql_2 = "UPDATE pull_request SET latest_time=%s " \
                        "WHERE pull_number= %s"
                inputs = (latest_time, pull_number)
                cursor.execute(sql_2, inputs)
        connection.commit()
    finally:
        connection.close()


# latest_date = datetime.strptime('2014-06-10 17:52:31', '%Y-%m-%d %H:%M:%S')
# update_latest_time(latest_date, 6156, 'rails')

update_with_github_api('bitcoin', 'bitcoin/bitcoin')
