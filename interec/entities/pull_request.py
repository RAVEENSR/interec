class PullRequest:
    """
    This class models a pull-request.
    """

    @staticmethod
    def __initialize_files(files_string):
        return files_string.split("|")

    def __init__(self, data):
        self.pr_id = data[0]
        self.pull_number = data[1]
        self.requester_login = data[2]
        self.title = data[3]
        self.description = data[4]
        self.created_date = data[5]
        self.merged_data = data[6]
        self.integrator_login = data[7]
        self.files = self.__initialize_files(data[8])

    @property
    def pr_id(self):
        return self.__pr_id

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
    def integrator_login(self):
        return self.__integrator_login

    @property
    def files(self):
        return self.__files

    @pr_id.setter
    def pr_id(self, val):
        self.__pr_id = val

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

    @integrator_login.setter
    def integrator_login(self, val):
        self.__integrator_login = val

    @files.setter
    def files(self, val):
        self.__files = val
