class PullRequest:

    @staticmethod
    def initialise_files(files_string):
        return files_string.split("|")

    def __init__(self, data):
        self.pr_id = data.pr_id
        self.first_pull = data.first_pull
        self.pull_number = data.pull_number
        self.con_login = data.con_login
        self.title = data.title
        self.description = data.description
        self.created_date = data.created_date
        self.merged_data = data.merged_data
        self.integrator_login = data.integrator_login
        self.num_of_commits = data.num_of_commits
        self.num_of_added_lines = data.num_of_added_lines
        self.num_of_deleted_lines = data.num_of_deleted_lines
        self.total_lines = data.total_lines
        self.num_of_changed_lines = data.num_of_changed_lines
        self.files = self.initialise_files(data.files)
        self.developer_type = data.developer_type
        self.requester_follows_core_team = data.requester_follows_core_team
        self.core_team_follows_requester = data.core_team_follows_requester


class MergedPullRequest(PullRequest):
    def __init__(self, integrator):
        super().__init__(self)
        self.longest_common_prefix_score = 0
        self.longest_common_suffix_score = 0
        self.longest_common_sub_string_score = 0
        self.longest_common_sub_sequence_score = 0
        self.pr_title_similarity = 0
        self.pr_description_similarity = 0
        self.integrator = integrator
        self.integrator_activeness = 0


class Integrator:
    def __init__(self, data):
        self.integrator_id = data.integrator_id
        self.integrator_login = data.integrator_login
