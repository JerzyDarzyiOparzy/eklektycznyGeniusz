from rapdna.stats.schemes import classify


def scheme(*pairs):
    s = {frozenset(p) for p in pairs}
    return classify(lambda i, j: frozenset((i, j)) in s)


def test_schemes():
    assert scheme((0, 1), (2, 3)) == "aabb"
    assert scheme((0, 2), (1, 3)) == "abab"
    assert scheme((0, 3), (1, 2)) == "abba"
    assert scheme((0, 1), (1, 2), (2, 3)) == "monorhyme"
    assert scheme((0, 1)) == "other"
