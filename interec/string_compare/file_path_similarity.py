class FilePathSimilarityCalculator:

    @staticmethod
    def path_to_list(file_string):
        return file_string.split("/")

    def longest_common_prefix(self, f1, f2):
        f1 = self.path_to_list(f1)
        f2 = self.path_to_list(f2)
        common_path = 0
        min_length = min(len(f1), len(f2))
        for i in range(min_length):
            if f1[i] == f2[i]:
                common_path += 1
            else:
                break
        return common_path

    def longest_common_suffix(self, f1, f2):
        f1 = self.path_to_list(f1)
        f2 = self.path_to_list(f2)
        common_path = 0
        r = range(min(len(f1), len(f2)))
        reversed(r)
        for i in r:
            if f1[i] == f2[i]:
                common_path += 1
            else:
                break
        return common_path

    def longest_common_sub_string(self, f1, f2):
        f1 = self.path_to_list(f1)
        f2 = self.path_to_list(f2)
        common_path = 0
        if len(set(f1) & set(f2)) > 0:
            mat = [[0 for x in range(len(f2) + 1)] for x in range(len(f1) + 1)]
            for i in range(len(f1) + 1):
                for j in range(len(f2) + 1):
                    if i == 0 or j == 0:
                        mat[i][j] = 0
                    elif f1[i - 1] == f2[j - 1]:
                        mat[i][j] = mat[i - 1][j - 1] + 1
                        common_path = max(common_path, mat[i][j])
                    else:
                        mat[i][j] = 0
        return common_path

    def longest_common_sub_sequence(self, f1, f2):
        f1 = self.path_to_list(f1)
        f2 = self.path_to_list(f2)
        if len(set(f1) & set(f2)) > 0:
            l = [[0 for x in range(len(f2) + 1)] for x in range(len(f1) + 1)]
            for i in range(len(f1) + 1):
                for j in range(len(f2) + 1):
                    if i == 0 or j == 0:
                        l[i][j] = 0
                    elif f1[i - 1] == f2[j - 1]:
                        l[i][j] = l[i - 1][j - 1] + 1
                    else:
                        l[i][j] = max(l[i - 1][j], l[i][j - 1])
            common_path = l[len(f1)][len(f2)]
        else:
            common_path = 0
        return common_path

    @staticmethod
    def add_file_path_similarity_ranking(data_frame):
        # data_frame['file_similarity'] = data_frame['lc_substr'] + data_frame['ls_subseq'] + data_frame['lcp'] \
        #                                 + data_frame['lcs']
        data_frame["file_path_rank"] = data_frame["file_similarity"].rank(method='min', ascending=False)
