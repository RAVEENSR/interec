for i in range(1, 9):
    for j in range(1, 9):
        for k in range(1,9):
            if i != 0 and j != 0 and k != 0 and i + j + k == 10:
                print(str(i/10) + " " + str(j/10) + " " + str(k/10))
