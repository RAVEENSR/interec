#########################################################################
# File: string_compare.py
# Descriptions: String comparison techniques for file path similarity	
# Input: The arguments f1, f2 are strings of file path 					
# Output: Number of common file path components in f1 and f2
#########################################################################


def path_to_list(file_string):
    return file_string.split("/")


def longest_common_prefix(f1, f2):
    f1 = path_to_list(f1)
    f2 = path_to_list(f2)
    common_path = 0
    min_length = min(len(f1), len(f2))
    for i in range(min_length):
        if f1[i] == f2[i]:
            common_path += 1
        else:
            break
    return common_path


def longest_common_suffix(f1, f2):
    f1 = path_to_list(f1)
    f2 = path_to_list(f2)
    common_path = 0
    r = range(min(len(f1), len(f2)))
    reversed(r)
    for i in r:
        if f1[i] == f2[i]:
            common_path += 1
        else:
            break
    return common_path


def longest_common_sub_string(f1, f2):
    f1 = path_to_list(f1)
    f2 = path_to_list(f2)
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


def longest_common_sub_sequence(f1, f2):
    f1 = path_to_list(f1)
    f2 = path_to_list(f2)
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


def get_file_path_similarity_ranked_list(data_frame):
    return True
