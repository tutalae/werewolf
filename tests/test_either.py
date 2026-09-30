import unittest

from werewolf.either import Left, Right, ensure


def to_int(text):
    return Right(int(text)) if text.isdigit() else Left("not a number")


class EitherTest(unittest.TestCase):
    def test_then_chains_successful_steps(self):
        self.assertEqual(Right("12").then(to_int).then(ensure(lambda n: n < 20, "too big")), Right(12))

    def test_first_error_falls_through(self):
        result = Right("xx").then(to_int).then(ensure(lambda n: n < 20, "too big"))
        self.assertEqual(result, Left("not a number"))

    def test_later_error(self):
        self.assertEqual(Right("99").then(to_int).then(ensure(lambda n: n < 20, "too big")),
                         Left("too big"))

    def test_map_only_touches_right(self):
        self.assertEqual(Right(2).map(lambda n: n * 10), Right(20))
        self.assertEqual(Left("bad").map(lambda n: n * 10), Left("bad"))

    def test_either_picks_a_branch(self):
        describe = ("error: {}".format, "ok: {}".format)
        self.assertEqual(Right(1).either(*describe), "ok: 1")
        self.assertEqual(Left("bad").either(*describe), "error: bad")


if __name__ == "__main__":
    unittest.main()
