class FilePathSimilarityCalculator:

    @staticmethod
    def path_separator(file_string):
        return file_string.split("/")

    def longest_common_prefix_similarity(self, file1, file2):
        file1 = self.path_separator(file1)
        file2 = self.path_separator(file2)
        common_file_path = 0
        min_length = min(len(file1), len(file2))
        for i in range(min_length):
            if file1[i] == file2[i]:
                common_file_path += 1
            else:
                break
        return common_file_path

    def longest_common_suffix_similarity(self, file1, file2):
        file1 = self.path_separator(file1)
        file2 = self.path_separator(file2)
        common_file_path = 0
        r = range(min(len(file1), len(file2)))
        reversed(r)
        for i in r:
            if file1[i] == file2[i]:
                common_file_path += 1
            else:
                break
        return common_file_path

    def longest_common_sub_string_similarity(self, file1, file2):
        file1 = self.path_separator(file1)
        file2 = self.path_separator(file2)
        common_file_path = 0
        if len(set(file1) & set(file2)) > 0:
            mat = [[0 for x in range(len(file2) + 1)] for x in range(len(file1) + 1)]
            for i in range(len(file1) + 1):
                for j in range(len(file2) + 1):
                    if i == 0 or j == 0:
                        mat[i][j] = 0
                    elif file1[i - 1] == file2[j - 1]:
                        mat[i][j] = mat[i - 1][j - 1] + 1
                        common_file_path = max(common_file_path, mat[i][j])
                    else:
                        mat[i][j] = 0
        return common_file_path

    def longest_common_sub_sequence_similarity(self, file1, file2):
        file1 = self.path_separator(file1)
        file2 = self.path_separator(file2)
        if len(set(file1) & set(file2)) > 0:
            l = [[0 for x in range(len(file2) + 1)] for x in range(len(file1) + 1)]
            for i in range(len(file1) + 1):
                for j in range(len(file2) + 1):
                    if i == 0 or j == 0:
                        l[i][j] = 0
                    elif file1[i - 1] == file2[j - 1]:
                        l[i][j] = l[i - 1][j - 1] + 1
                    else:
                        l[i][j] = max(l[i - 1][j], l[i][j - 1])
            common_file_path = l[len(file1)][len(file2)]
        else:
            common_file_path = 0
        return common_file_path

    @staticmethod
    def add_file_path_similarity_ranking(data_frame):
        # data_frame['file_similarity'] = data_frame['lc_substr'] + data_frame['ls_subseq'] + data_frame['lcp'] \
        #                                 + data_frame['lcs']
        data_frame["file_path_rank"] = data_frame["file_similarity"].rank(method='min', ascending=False)
