"""Constructed controls only; these tests do not need the organizer workspace."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np
from PIL import Image

from research.evidence_contract.oracle_reliability import controls, policy
from research.evidence_contract.oracle_reliability.g04_5_compatibility import classify, mrz_pixels
from research.evidence_contract.oracle_reliability.mrz_ablation_v1 import compare_pair

LITERAL = dict(line1=controls.LINE1, line2=controls.LINE2)
NUMBER = controls.LINE2[:9]


class FieldCompatibility(unittest.TestCase):
    def test_ordinary_document_number(self):
        status, facts = classify('id_number', 'id_number', NUMBER, LITERAL, NUMBER)
        self.assertEqual(status, 'STRUCTURALLY_COMPATIBLE')
        self.assertEqual(facts['td3_native_precision'], 'td3_literal_checks_pass')

    def test_different_personal_id_even_with_optional_match(self):
        personal = controls.LINE2[28:42].rstrip('<')
        status, facts = classify('id_number', 'id_number', personal, LITERAL, NUMBER)
        self.assertEqual(status, 'UNSUPPORTED_SOURCE_SLOT')
        self.assertEqual(facts['locked_identifier_vs_optional_data'], 'MATCH_EXACT')
        self.assertEqual(facts['number_vs_document_slot'], 'MATCH')

    def test_number_alias_does_not_rebind_locked_source(self):
        self.assertEqual(classify('id_number', 'number', NUMBER, LITERAL, NUMBER)[0], 'AMBIGUOUS_MAPPING')

    def test_field_swap(self):
        self.assertEqual(classify('dob', 'expiry_date', '12.08.1974', LITERAL, NUMBER)[0], 'AMBIGUOUS_MAPPING')

    def test_both_centuries_same_diagnostic(self):
        for century in ('19', '20'):
            with self.subTest(century=century):
                status, facts = classify('dob', 'birth_date', f'12.08.{century}74.', LITERAL, NUMBER)
                self.assertEqual(status, 'UNSUPPORTED_PRECISION')
                self.assertEqual(facts['diagnostic_yymmdd_projection'], 'MATCH')
        self.assertIsNone(policy.canonical('000229', 'date_yymmdd'))

    def test_expiry_uses_expiry_offset_and_valid_calendar(self):
        for body, expected in [('15.04.2012', 'MATCH'), ('12.08.1974', 'DIFFERENT')]:
            status, facts = classify('expiry_date', 'expiry_date', body, LITERAL, NUMBER)
            self.assertEqual(status, 'UNSUPPORTED_PRECISION')
            self.assertEqual(facts['diagnostic_yymmdd_projection'], expected)
        with self.assertRaises(ValueError):
            classify('expiry_date', 'expiry_date', '31.02.2000', LITERAL, NUMBER)

    def test_malformed_td3_and_checksum(self):
        for broken in [dict(LITERAL, line1='I' + controls.LINE1[1:]),
                       dict(LITERAL, line2=controls.LINE2[:-1] + '9')]:
            with self.subTest():
                self.assertEqual(classify('id_number', 'id_number', NUMBER, broken, NUMBER)[0],
                                 'UNSUPPORTED_LITERAL_PROFILE')

    def test_polygon_pixels_ignore_changes_outside_footprint(self):
        with TemporaryDirectory() as tmp:
            files = {side: Path(tmp)/(side+'.png') for side in ('a', 'b', 'c')}
            patch = np.zeros((8, 8, 3), np.uint8)
            for side, pos in [('a', (0, 0)), ('b', (7, 7)), ('c', (3, 3))]:
                im = patch.copy()
                im[pos] = 255
                Image.fromarray(im).save(files[side])
            region = dict(box=[4, 5, 12, 13], quad=[[6, 7], [9, 7], [9, 10], [6, 10]])
            pixels = [mrz_pixels(dict(region, sha256=side), files) for side in files]
            self.assertTrue(np.array_equal(pixels[0], pixels[1]))
            self.assertFalse(np.array_equal(pixels[0], pixels[2]))


class FrozenEndpointControls(unittest.TestCase):
    def exercise(self, name, checked, asserted):
        case = next(c for c in controls.make_controls() if c['name'] == name)
        arms = compare_pair(*controls.inputs(case), minimum_grade=1)['arms']
        for arm, expected in [('checked_v2', checked), ('mrz_metadata_asserted', asserted)]:
            self.assertEqual(tuple(arms[arm][e]['state'] for e in ('pointwise', 'relation')), expected)

    def test_body_removal_with_intact_valid_backup(self):
        self.exercise('TD3_id_number', ('FAULT', 'FAULT'), ('FAULT', 'FAULT'))

    def test_literal_only_defect(self):
        self.exercise('TD3_bad_checksum', ('UNKNOWN', 'UNKNOWN'), ('FAULT', 'FAULT'))

    def test_wrong_declared_value_splits_endpoints(self):
        self.exercise('TD3_wrong_value', ('UNKNOWN', 'UNKNOWN'), ('FAULT', 'UNKNOWN'))

    def test_date_full_rejected_by_both_arms(self):
        self.exercise('TD3_wrong_precision', ('UNKNOWN', 'UNKNOWN'), ('UNKNOWN', 'UNKNOWN'))

    def test_before_after_transition_is_relation_only(self):
        self.exercise('C2_main_not_removed', ('FAULT', 'UNKNOWN'), ('FAULT', 'UNKNOWN'))
