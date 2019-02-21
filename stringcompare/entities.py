class PullRequest:

    @staticmethod
    def initialise_files(files_string):
        return files_string.split("|")

    def __init__(self, data):
        self.pr_id = data[0]
        self.first_pull = data[1]
        self.location = data[2]
        self.pull_number = data[3]
        self.requester_login = data[4]
        self.title = data[5]
        self.description = data[6]
        self.created_date = data[7]
        self.merged_data = data[8]
        self.latest_time = data[9]
        self.integrator_login = data[10]
        self.num_of_commits = data[11]
        self.num_of_added_lines = data[12]
        self.num_of_deleted_lines = data[13]
        self.total_lines = data[14]
        self.num_of_changed_files = data[15]
        self.files = self.initialise_files(data[16])
        self.developer_type = data[17]
        self.requester_follows_core_team = data[18]
        self.core_team_follows_requester = data[19]


# class MergedPullRequest(PullRequest):
#     def __init__(self, data):
#         super().__init__(data)
#         self.longest_common_prefix_score = 0
#         self.longest_common_suffix_score = 0
#         self.longest_common_sub_string_score = 0
#         self.longest_common_sub_sequence_score = 0
#         self.pr_title_similarity = 0
#         self.pr_description_similarity = 0
#         self.integrator_activeness = 0


class Integrator:
    def __init__(self, login_name):
        self.integrator_login = login_name
        self.longest_common_prefix_score = 0
        self.longest_common_suffix_score = 0
        self.longest_common_sub_string_score = 0
        self.longest_common_sub_sequence_score = 0
        self.pr_title_similarity = 0
        self.pr_description_similarity = 0
        self.activeness = 0
