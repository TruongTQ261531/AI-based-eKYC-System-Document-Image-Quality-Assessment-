import unittest
from research.fc_data import stratified_random, repeated_directions


class MatchedControls(unittest.TestCase):
    def test_exact_selection_maximizes_joint_budget_support_and_repeats_seed(self):
        candidates={p:dict(stratum=('photo','one'),token_delta=d) for p,d in [('a',1),('b',1),('c',1),('d',2)]}
        first,proof=stratified_random(candidates,{('photo','one'):2},2,{'a','b'},min_new=1)
        self.assertEqual(len(set(first)-{'a','b'}),1)
        self.assertEqual(proof['enumerated_subsets'],6)
        self.assertEqual(proof['token_matched_subsets'],3)
        self.assertEqual(proof['maximum_new_ids_after_token_match'],1)
        self.assertEqual((first,proof),stratified_random(candidates,{('photo','one'):2},2,{'a','b'},min_new=1))

    def test_infeasible_budget_is_rejected_instead_of_relaxed(self):
        with self.assertRaises(ValueError):
            stratified_random({'a':dict(stratum=('x','y'),token_delta=1)}, {('x','y'):1},99,set(),min_new=1)

    def test_enumeration_cap_is_enforced_before_materializing_combinations(self):
        values={str(i):dict(stratum=('x','y'),token_delta=1) for i in range(20)}
        with self.assertRaises(ValueError):stratified_random(values,{('x','y'):10},10,set(),attempts=100,min_new=1)

    def test_repeated_orientation_preserves_total_tokens_and_balance(self):
        values={p:dict(a_tokens=a,b_tokens=b) for p,a,b in [('a',9,4),('b',8,3),('c',7,5),('d',6,4)]}
        directions=repeated_directions(values,2)
        self.assertEqual(sum(directions.values()),2)
        total=sum(2*values[p]['a_tokens' if use_a else 'b_tokens'] for p,use_a in directions.items())
        self.assertEqual(total,sum(r['a_tokens']+r['b_tokens'] for r in values.values()))

    def test_impossible_repeated_orientation_budget_stops(self):
        with self.assertRaises(ValueError):repeated_directions({'a':dict(a_tokens=9,b_tokens=4)},1)


if __name__=='__main__':unittest.main()
