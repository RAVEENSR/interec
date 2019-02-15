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


class ReviewPullRequest(PullRequest):
    def __init__(self, data):
        super().__init__(self)
        self.prev_pr_similarity = []
        # TODO [0][0] = PR object | [0][1] algo1 | [0][2] algo2 | [0][3] algo3 | [0][4] algo3
        '''
            # TODO create a common object to hold each new pr details( ex. ine object to hold the file path similarity
            , one object to hold the textual similarity) These things should be done without repeating the saving 
            details again and again.
        '''
