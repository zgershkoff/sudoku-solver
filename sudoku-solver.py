# a program to solve sudoku puzzles
# no reason

from itertools import combinations

# an example puzzle
# source: wikipedia
data = [
"530070000",
"600195000",
"098000060",
"800060003",
"400803001",
"700020006",
"060000280",
"000419005",
"000080079"]

# symbols that fill the grid (strings, not ints)
syms = "123456789"
# groupings of row and column incidices
rs = [[0, 1, 2], [3, 4, 5], [6, 7, 8]]
# for getting tuples from 3x3 squares
topleft = [(i, j) for i in [0, 3, 6] for j in [0, 3, 6]]
# for better iteration over "row" "col" "box"
shapes = {0:"row", 1:"col", 2:"box"}

def init_possibilties(data):
    ps = {}
    # this loop sets up a dictionary assigning
    # coordinate tuples to a set of possible values
    for i, row in enumerate(data):
        for j, entry in enumerate(row):
            if entry != '0':
                ps[(i,j)] = set([entry])
            else:
                in_row = set([c for c in row if c != '0'])
                in_col = set([r[j] for r in data if r[j] != '0'])
                # now find the values in the 3x3 square
                sq_rows = ranges(i)
                sq_cols = ranges(j)
                in_sq = set()
                for k in sq_rows:
                    for l in sq_cols:
                        in_sq.add(data[k][l])
                ps[(i, j)] = ((set(syms) - in_row) - in_col) - in_sq
    return ps


def solver(data):
    ps = init_possibilties(data)

    # as the loop below progresses, the difficulty will increment
    # to unlock harder methods
    difficulty = 0

    # if a value is known, remove that value from the neighbor possibilities
    while not all([len(s) == 1 for s in ps.values()]):
        difficulty += 1
        # the most basic check: from each set of possibilities,
        # remove values of solved neighbors
        for i, j in ps:
            if len(ps[(i,j)]) == 1:
                for (a, b) in neighbor_tuples(i, j, "all"):
                    ps[(a,b)] -= ps[(i,j)]

        # this next check looks for "hidden singles"
        # values that only show up once in a region
        for i, j in ps:
            if len(ps[(i, j)]) != 1:
                ps = check_neighbors(ps, i, j)

        if difficulty < 2:
            continue

        # inside a box, if a possibility only lives on a certain row or
        # column, we can rule out that possibility on the same row or column
        # outside of the box
        ps = trim_possibilities(ps, "row")
        ps = trim_possibilities(ps, "col")
        if difficulty < 3:
            continue

        ps = naked_pairs(ps)
        if difficulty < 4:
            continue

        ps = xwing(ps)
        if difficulty < 5:
            continue

        ps = naked_pairs(ps, triple=True)
        if difficulty < 6:
            continue

        data = remove_zeroes(data, ps)
        for row in data:
            print(row)
        print()

        # print(sorted(ps.items())) # searching for next technique

        # kills  the program if it's too broken
        for pair in ps.items():
            if pair[1] == set([]):
                print pair
                exit()

    data = reconstruct_grid(ps)
    for row in data:
        print(row)

    return data


def xwing(ps):
    for shape1, shape2 in combinations(range(3), 2):
        regions1 = get_regions(ps, shapes[shape1])
        regions2 = get_regions(ps, shapes[shape2])
        for c in syms:
            # look for the regions where a char is only a possibility twice
            coords = []
            for r1 in regions1:
                hits = [t for t in r1 if c in ps[t]]
                if len(hits) == 2:
                    coords.append(set(hits))
            for s1, s2 in combinations(coords, 2):
                bigset = s1.union(s2)

                # if this hits two of the regions for regions2, we apply xwing
                if len([r2 for r2 in regions2
                        if not bigset.isdisjoint(r2)]) == 2:
                    for r2 in regions2:
                        if not bigset.isdisjoint(r2):
                            for t in r2:
                                if t not in bigset:
                                    ps[t] -= set([c])
    return ps

def get_regions(ps, shape):
    """return a list coordinate tuples for all region of a particular shape"""
    l = []
    if shape == "row":
        for a in range(9):
            l.append(neighbor_tuples(a, 0, "row", True))
    elif shape == "col":
        for b in range(9):
            l.append(neighbor_tuples(0, b, "col", True))
    elif shape == "box":
        for i, j in topleft:
            l.append(neighbor_tuples(i, j, "box", True))
    return l


def naked_pairs(ps, triple=False):
    for (i, j) in topleft:
        ps = _naked_pairs(i, j, ps, "box", triple)
    for a in range(9):
        ps = _naked_pairs(a, 0, ps, "row", triple)
    for b in range(9):
        ps = _naked_pairs(0, b, ps, "col", triple)
    return ps

def _naked_pairs(i, j, ps, shape, triple=False):
    quant = 2
    if triple:
        quant = 3
    region = neighbor_tuples(i, j, group=shape, include=True)
    regionsets = [ps[t] for t in region]
    for comb in combinations(syms, quant):
        s = set(comb)
        tlist = []
        for t in region:
            if len(ps[t]) != 1 and s.issuperset(ps[t]):
                tlist.append(t)
        if len(tlist) >= quant:
            for coordinates in region:
                if coordinates not in tlist:
                    ps[coordinates] -= s

    return ps


def trim_possibilities(ps, group1):
    for i in range(9):
        for (a, b) in topleft:
            if group1 == "row":
                n1 = set(neighbor_tuples(i, 0, group=group1, include=True))
            elif group1 == "col":
                n1 = set(neighbor_tuples(0, i, group=group1, include=True))
            else:
                raise NotImplementedError("don't do that")
            n2 = set(neighbor_tuples(a, b, group="box", include=True))
            if not n1.isdisjoint(n2):
                inters = union_from_coords(ps, n1.intersection(n2))
                rest_of_row = union_from_coords(ps, n1 - n2)
                rest_of_sq = union_from_coords(ps, n2 - n1)
                for c in inters - rest_of_sq:
                    for t in n1 - n2:
                        ps[t] -= set([c])
                for c in inters - rest_of_row:
                    for t in n2 - n1:
                        ps[t] -= set([c])
    return ps

def union_from_coords(ps, tupleset):
    unionset = set()
    for t in tupleset:
        unionset.update(ps[t])
    return unionset


def check_neighbors(ps, i, j):
    kwds = ["row", "col", "box"]
    for kwd in kwds:
        n_poss = set()
        for (a, b) in neighbor_tuples(i, j, kwd):
            n_poss.update(ps[(a, b)])

        if len(ps[(i, j)] - n_poss) == 1:
            ps[(i, j)] -= n_poss

    return ps

def ranges(n):
    for r in rs:
        if n in r:
            return r

def neighbor_tuples(i, j, group="all", include=False):
    l = []
    if group == "all" or group == "col":
        for a in range(9):
            if a != i:
                l.append((a, j))
    if group == "all" or group == "row":
        for b in range(9):
            if b != j:
                l.append((i, b))
    if group == "all" or group == "box":
        for a in ranges(i):
            for b in ranges(j):
                if group == "all":
                    if a != i and b != j:
                        l.append((a, b))
                elif group == "box":
                    if a != i or b != j:
                        l.append((a, b))
    if include:
        l.append((i,j))
    return l

def reconstruct_grid(ps):
    grid = []
    for i in range(9):
        row = ""
        for j in range(9):
            row += list(ps[(i,j)])[0]
        grid.append(row)
    return grid


if __name__ == "__main__":
    solver(data)
