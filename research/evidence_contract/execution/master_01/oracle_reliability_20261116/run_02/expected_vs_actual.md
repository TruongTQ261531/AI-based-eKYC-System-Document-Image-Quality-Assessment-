# Authored policy expectations versus constructed truth

58 symbolic cases, 0 images/physical IDs. These are not model predictions or human judgments.
P/R/S means pointwise/relation/structure. T/F/NA below are authored task truth.
Matching a policy expectation does not establish correctness: retained poisoned-reference cases are false alarms.

| Case | Constructed truth P/R/S | Expected tier 1 P/R/S | Observed tier 1 P/R/S | Observed tier 2 P/R/S |
|---|---|---|---|---|
| C3_correct_to_correct | F / F / F | NO_FAULT / NO_FAULT / NO_FAULT | NO_FAULT / NO_FAULT / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| C3_correct_to_wrong | T / T / F | FAULT / FAULT / NO_FAULT | FAULT / FAULT / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| C3_correct_to_empty | T / T / F | FAULT / FAULT / NO_FAULT | FAULT / FAULT / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| C3_wrong_to_correct | F / NA / F | NO_FAULT / UNKNOWN / NO_FAULT | NO_FAULT / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| C3_wrong_to_wrong | T / NA / F | FAULT / UNKNOWN / NO_FAULT | FAULT / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| C3_wrong_to_empty | T / NA / F | FAULT / UNKNOWN / NO_FAULT | FAULT / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| C3_empty_to_correct | F / NA / F | NO_FAULT / UNKNOWN / NO_FAULT | NO_FAULT / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| C3_empty_to_wrong | T / NA / F | FAULT / UNKNOWN / NO_FAULT | FAULT / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| C3_empty_to_empty | T / NA / F | FAULT / UNKNOWN / NO_FAULT | FAULT / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| C4_unsupported_operator | T / NA / F | FAULT / UNKNOWN / NO_FAULT | FAULT / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| C4_identity | T / T / F | FAULT / FAULT / NO_FAULT | FAULT / FAULT / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| C1_complete_empty | F / F / F | NO_FAULT / NO_FAULT / NO_FAULT | NO_FAULT / NO_FAULT / NO_FAULT | NO_FAULT / UNKNOWN / NO_FAULT |
| C1_complete_emitted | T / T / F | FAULT / FAULT / NO_FAULT | FAULT / FAULT / NO_FAULT | FAULT / UNKNOWN / NO_FAULT |
| C1_partial_inventory | NA / NA / F | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| C1_missing_source_record | NA / NA / F | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| partial_but_supported | T / T / F | FAULT / FAULT / NO_FAULT | FAULT / FAULT / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| C2_main_not_removed | T / NA / F | FAULT / UNKNOWN / NO_FAULT | FAULT / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| C2_verified_duplicate_backup | T / T / F | FAULT / FAULT / NO_FAULT | FAULT / FAULT / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| C2_new_source_not_surviving_backup | T / NA / F | FAULT / UNKNOWN / NO_FAULT | FAULT / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| source_conflict | NA / NA / F | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| source_unresolved | NA / NA / F | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| semantic_link_False | NA / NA / F | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| semantic_link_None | NA / NA / F | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| integrity_False | NA / NA / F | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| integrity_None | NA / NA / F | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| context_present_False | NA / NA / F | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| context_present_None | NA / NA / F | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| bad_pixel | NA / NA / F | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| bad_field | NA / NA / F | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| bad_mutation | NA / NA / F | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| bad_source_semantic | NA / NA / F | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| bad_duplicate | NA / NA / F | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| bad_boolean_string | NA / NA / F | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| bad_schema | NA / NA / F | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| bad_hash | NA / NA / F | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| bad_unhashable_kind | NA / NA / F | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| bad_null_source | NA / NA / F | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| reference_unapproved | NA / NA / F | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| constructed_reference_actual_origin_probe | NA / NA / F | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| validity_INVALID_TEST | NA / NA / F | INVALID_TEST / INVALID_TEST / NO_FAULT | INVALID_TEST / INVALID_TEST / NO_FAULT | INVALID_TEST / INVALID_TEST / NO_FAULT |
| validity_INCONCLUSIVE | NA / NA / F | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| malformed_followup | NA / NA / T | UNKNOWN / UNKNOWN / STRUCTURAL_ERROR | UNKNOWN / UNKNOWN / STRUCTURAL_ERROR | UNKNOWN / UNKNOWN / STRUCTURAL_ERROR |
| malformed_original | T / NA / F | FAULT / UNKNOWN / NO_FAULT | FAULT / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| TD3_id_number | T / T / F | FAULT / FAULT / NO_FAULT | FAULT / FAULT / NO_FAULT | FAULT / FAULT / NO_FAULT |
| TD3_dob | T / T / F | FAULT / FAULT / NO_FAULT | FAULT / FAULT / NO_FAULT | FAULT / FAULT / NO_FAULT |
| TD3_expiry_date | T / T / F | FAULT / FAULT / NO_FAULT | FAULT / FAULT / NO_FAULT | FAULT / FAULT / NO_FAULT |
| TD3_bad_checksum | NA / NA / F | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| TD3_missing_literal | NA / NA / F | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| TD3_wrong_value | NA / NA / F | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| TD3_no_field_checksum | NA / NA / F | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| TD3_wrong_precision | NA / NA / F | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| TD3_invalid_date | NA / NA / F | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| invalid_or_ambiguous_date_2023-02-29 | NA / NA / F | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| invalid_or_ambiguous_date_000229 | NA / NA / F | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| typed_O_vs_zero | T / T / F | FAULT / FAULT / NO_FAULT | FAULT / FAULT / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| shared_wrong_reference | F / NA / F | FAULT / UNKNOWN / NO_FAULT | FAULT / UNKNOWN / NO_FAULT | UNKNOWN / UNKNOWN / NO_FAULT |
| corroborated_body | T / T / F | FAULT / FAULT / NO_FAULT | FAULT / FAULT / NO_FAULT | FAULT / FAULT / NO_FAULT |
| corroborated_shared_wrong_reference | F / NA / F | FAULT / UNKNOWN / NO_FAULT | FAULT / UNKNOWN / NO_FAULT | FAULT / UNKNOWN / NO_FAULT |

Flat states match B for every endpoint at both tiers. Their shared validation boundary is declared; this is not independent truth verification.

## Legacy projections (diagnostic, injected only)

| Case | v1 P/R | v2 P/R |
|---|---|---|
| C2_main_not_removed | FAULT / FAULT | FAULT / UNKNOWN |
| source_unresolved | FAULT / FAULT | UNKNOWN / UNKNOWN |
| TD3_bad_checksum | FAULT / FAULT | UNKNOWN / UNKNOWN |
| invalid_or_ambiguous_date_000229 | FAULT / UNKNOWN | UNKNOWN / UNKNOWN |
