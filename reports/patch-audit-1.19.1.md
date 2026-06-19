# Dynamic AI MP Patch Audit

- Generated: 2026-06-18 20:40
- Mod root: `C:\Users\james\OneDrive\Desktop\hoi4-ai-files\dynamic-ai-mp`
- Base repo: `C:\Users\james\OneDrive\Desktop\hoi4-ai-files\hoi4-ai-base`
- Base refs: `HEAD` -> `5a9158ad5d8510951e3ca9a8c22ede379ceb9d82`
- AI tuning helper dirs skipped: `True`
- `common/ai_strategy` changes are reviewed by default and are not automatic merge candidates.
- DAI files skipped: `True`

## Agent Use

- Treat `Missing new upstream objects` as the first merge queue.
- Treat `Changed existing upstream objects` as review-only; apply the A/B/C rule before merging values.
- Treat `Drift scan` as a long-term hygiene pass against current base, not necessarily a latest-patch diff.
- Treat new or changed `ai_strategy` content as something to call out for review, not an automatic merge.
- Keep new standalone objects in current-base order when adding them to the mod.

## Patch File Overlap

- Base changed files: `41`
- Changed files overwritten by mod: `2`
- Changed files not overwritten by mod: `39`
- Skipped changed overwritten files: `0`

## Missing New Upstream Objects

No missing `B - A` objects were found in changed overwritten files.

## Changed Existing Upstream Objects

No changed existing upstream objects need review after the default AI-block normalization.

## Changed Existing Upstream Objects Absent From Mod

No changed existing upstream objects were absent from the mod in changed overwritten files.

## Already Matching Upstream Changes

`3` changed existing upstream objects already match the mod after normalization.


## Drift Scan: Missing Current-Base Objects

No missing current-base objects were found in high-value overwritten files.

## Drift Scan: Base-Order Mismatches

No base-order mismatches were found for files with complete base object coverage.

## Diagnostics

- `common/doctrines/subdoctrines/sea/navy_submarine_doctrines.txt`: current base: unclosed block 'long_range_submarines' starting at line 297

## Skipped Changed Overwritten Files

None.

## Base Changed But Not Overwritten

- `common/ai_strategy_plans/AST_alternate_strategy_plan.txt`
- `common/ai_strategy_plans/AST_historical_strategy_plan.txt`
- `common/bookmarks/the_gathering_storm.txt`
- `common/characters/AST.txt`
- `common/characters/INS.txt`
- `common/characters/PHI.txt`
- `common/characters/RAJ.txt`
- `common/countries/cosmetic.txt`
- `common/country_leader/taog_traits.txt`
- `common/decisions/AST.txt`
- `common/decisions/HOL.txt`
- `common/decisions/INS.txt`
- `common/decisions/SIA.txt`
- `common/decisions/categories/INS_decision_categories.txt`
- `common/dynamic_modifiers/TAOG_dynamic_modifiers.txt`
- `common/game_rules/00_game_rules.txt`
- `common/ideas/australia.txt`
- `common/ideas/netherlands.txt`
- `common/ideas/siam.txt`
- `common/national_focus/abdacom_shared_branch.txt`
- `common/national_focus/australia_taog.txt`
- `common/national_focus/indonesia.txt`
- `common/national_focus/indonesia_joint.txt`
- `common/national_focus/netherlands.txt`
- `common/national_focus/siam.txt`
- `common/on_actions/16_taog_on_actions.txt`
- `common/raids/land_infiltration_custom.txt`
- `common/raids/naval_commando_raids.txt`
- `common/scripted_effects/AST_scripted_effects.txt`
- `common/scripted_effects/SIA_scripted_effects.txt`
- `common/scripted_triggers/AST_scripted_triggers.txt`
- `common/unit_leader/00_planning_skills.txt`
- `common/unit_leader/00_traits.txt`
- `events/MUN_Czechoslovakia.txt`
- `events/SEA_Philippines.txt`
- `events/TAOG_Australia.txt`
- `events/TAOG_Indonesia.txt`
- `events/TAOG_Siam.txt`
- `events/WarJustification.txt`
