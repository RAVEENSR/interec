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
        self.num_of_first_pulls = 0
        self.num_of_prs = 0
        self.total_commits = 0

    @property
    def integrator_login(self):
        return self.__integrator_login

    @property
    def longest_common_prefix_score(self):
        return self.__longest_common_prefix_score

    @property
    def longest_common_suffix_score(self):
        return self.__longest_common_suffix_score

    @property
    def longest_common_sub_string_score(self):
        return self.__longest_common_sub_string_score

    @property
    def longest_common_sub_sequence_score(self):
        return self.__longest_common_sub_sequence_score

    @property
    def pr_title_similarity(self):
        return self.__pr_title_similarity

    @property
    def pr_description_similarity(self):
        return self.__pr_description_similarity

    @property
    def activeness(self):
        return self.__activeness

    @property
    def num_of_first_pulls(self):
        return self.__num_of_first_pulls

    @property
    def num_of_prs(self):
        return self.__num_of_prs

    @property
    def total_commits(self):
        return self.__total_commits

    @integrator_login.setter
    def integrator_login(self, val):
        self.__integrator_login = val

    @longest_common_prefix_score.setter
    def longest_common_prefix_score(self, val):
        self.__longest_common_prefix_score = val

    @longest_common_suffix_score.setter
    def longest_common_suffix_score(self, val):
        self.__longest_common_suffix_score = val

    @longest_common_sub_string_score.setter
    def longest_common_sub_string_score(self, val):
        self.__longest_common_sub_string_score = val

    @longest_common_sub_sequence_score.setter
    def longest_common_sub_sequence_score(self, val):
        self.__longest_common_sub_sequence_score = val

    @pr_title_similarity.setter
    def pr_title_similarity(self, val):
        self.__pr_title_similarity = val

    @pr_description_similarity.setter
    def pr_description_similarity(self, val):
        self.__pr_description_similarity = val

    @activeness.setter
    def activeness(self, val):
        self.__activeness = val

    @num_of_first_pulls.setter
    def num_of_first_pulls(self, val):
        self.__num_of_first_pulls = val

    @num_of_prs.setter
    def num_of_prs(self, val):
        self.__num_of_prs = val

    @total_commits.setter
    def total_commits(self, val):
        self.__total_commits = val
