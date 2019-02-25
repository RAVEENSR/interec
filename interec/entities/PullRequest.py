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

    @property
    def pr_id(self):
        return self.__pr_id

    @property
    def first_pull(self):
        return self.__first_pull

    @property
    def location(self):
        return self.__location

    @property
    def pull_number(self):
        return self.__pull_number

    @property
    def requester_login(self):
        return self.__requester_login

    @property
    def title(self):
        return self.__title

    @property
    def description(self):
        return self.__description

    @property
    def created_date(self):
        return self.__created_date

    @property
    def merged_data(self):
        return self.__merged_data

    @property
    def latest_time(self):
        return self.__latest_time

    @property
    def integrator_login(self):
        return self.__integrator_login

    @property
    def num_of_commits(self):
        return self.__num_of_commits

    @property
    def num_of_added_lines(self):
        return self.__num_of_added_lines

    @property
    def num_of_deleted_lines(self):
        return self.__num_of_deleted_lines

    @property
    def total_lines(self):
        return self.__total_lines

    @property
    def num_of_changed_files(self):
        return self.__num_of_changed_files

    @property
    def files(self):
        return self.__files

    @property
    def developer_type(self):
        return self.__developer_type

    @property
    def requester_follows_core_team(self):
        return self.__requester_follows_core_team

    @property
    def core_team_follows_requester(self):
        return self.__core_team_follows_requester

    @pr_id.setter
    def pr_id(self, val):
        self.__pr_id = val

    @first_pull.setter
    def first_pull(self, val):
        self.__first_pull = val

    @location.setter
    def location(self, val):
        self.__location = val

    @pull_number.setter
    def pull_number(self, val):
        self.__pull_number = val

    @requester_login.setter
    def requester_login(self, val):
        self.__requester_login = val

    @title.setter
    def title(self, val):
        self.__title = val

    @description.setter
    def description(self, val):
        self.__description = val

    @created_date.setter
    def created_date(self, val):
        self.__created_date = val

    @merged_data.setter
    def merged_data(self, val):
        self.__merged_data = val

    @latest_time.setter
    def latest_time(self, val):
        self.__latest_time = val

    @integrator_login.setter
    def integrator_login(self, val):
        self.__integrator_login = val

    @num_of_commits.setter
    def num_of_commits(self, val):
        self.__num_of_commits = val

    @num_of_added_lines.setter
    def num_of_added_lines(self, val):
        self.__num_of_added_lines = val

    @num_of_deleted_lines.setter
    def num_of_deleted_lines(self, val):
        self.__num_of_deleted_lines = val

    @total_lines.setter
    def total_lines(self, val):
        self.__total_lines = val

    @num_of_changed_files.setter
    def num_of_changed_files(self, val):
        self.__num_of_changed_files = val

    @files.setter
    def files(self, val):
        self.__files = val

    @developer_type.setter
    def developer_type(self, val):
        self.__developer_type = val

    @requester_follows_core_team.setter
    def requester_follows_core_team(self, val):
        self.__requester_follows_core_team = val

    @core_team_follows_requester.setter
    def core_team_follows_requester(self, val):
        self.__core_team_follows_requester = val

