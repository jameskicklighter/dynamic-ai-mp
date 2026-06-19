# Dynamic AI MP Patch Audit

- Generated: 2026-06-18 19:57
- Mod root: `C:\Users\james\OneDrive\Desktop\hoi4-ai-files\dynamic-ai-mp`
- Base repo: `C:\Users\james\OneDrive\Desktop\hoi4-ai-files\hoi4-ai-base`
- Base refs: `HEAD` -> `650b33c3b81c9f033d960769f93d8b644937b486`
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

- Base changed files: `395`
- Changed files overwritten by mod: `57`
- Changed files not overwritten by mod: `338`
- Skipped changed overwritten files: `14`

## Missing New Upstream Objects

### `common/ai_strategy/ENG.txt`
Missing: `1`
  - `object:ENG_med_invasion_phase` (base line 3366)

### `common/ai_strategy/GER.txt`
Missing: `2`
  - `object:GER_more_trains_after_barbarossa` (base line 3289)
  - `object:GER_build_tank_destroyers` (base line 5218)

### `common/ai_strategy/SOV.txt`
Missing: `3`
  - `object:SOV_later_unit_roles [1]` (base line 193)
  - `object:SOV_later_unit_roles [2]` (base line 229)
  - `object:SOV_build_tank_destroyers` (base line 2846)


## Changed Existing Upstream Objects

### `common/ai_navy/fleet/JAP_fleet_templates.txt`
Review candidates: `1`
  - `object:JAP_dominance_fleet_1` (base line 1)

### `common/ai_navy/taskforce/USA_taskforce_templates.txt`
Review candidates: `1`
  - `object:USA_StrikeForce_1` (base line 1)

### `common/ai_strategy/ENG.txt`
Review candidates: `3`
  - `object:ENG_the_adriatic_is_dangerous` (base line 1154)
  - `object:ENG_chill_on_the_pacific` (base line 2833)
  - `object:ENG_develop_mediterranean_supremacy` (base line 3334)

### `common/ai_strategy/FRA.txt`
Review candidates: `1`
  - `object:FRA_protect_vichy` (base line 326)

### `common/ai_strategy/GER.txt`
Review candidates: `3`
  - `object:GER_worry_about_barbarossa_before_africa` (base line 2105)
  - `object:GER_build_an_air_facility_in_penemunde` (base line 4813)
  - `object:GER_build_an_air_facility_anywhere` (base line 4836)

### `common/ai_strategy/ITA.txt`
Review candidates: `1`
  - `object:ITA_hold_africa` (base line 955)

### `common/ai_strategy/JAP.txt`
Review candidates: `1`
  - `object:JAP_leave_raj_a_bit` (base line 808)

### `common/ai_strategy/SOV.txt`
Review candidates: `1`
  - `object:SOV_unit_production` (base line 1)

### `common/ideas/_economic.txt`
Review candidates: `8`
  - `idea_category:economy` (base line 3)
  - `idea:economy/partial_economic_mobilisation` (base line 305)
  - `idea:economy/war_economy` (base line 481)
  - `idea_category:trade_laws` (base line 1136)
  - `idea:trade_laws/free_trade` (base line 1207)
  - `idea:trade_laws/export_focus` (base line 1307)
  - `idea:trade_laws/limited_exports` (base line 1409)
  - `idea:trade_laws/closed_economy` (base line 1644)

### `common/military_industrial_organization/organizations/GER_organization.txt`
Review candidates: `1`
  - `object:GER_henschel_organization` (base line 259)

### `common/military_industrial_organization/organizations/SOV_organization.txt`
Review candidates: `1`
  - `object:SOV_kirov_organization` (base line 826)


## Changed Existing Upstream Objects Absent From Mod

### `common/ai_navy/taskforce/USA_taskforce_templates.txt`
Changed upstream objects absent from mod: `1`
  - `object:USA_NavalInvasionSupport_1` (base line 95)

### `common/ai_strategy/ENG.txt`
These are strategy review notes only; do not merge automatically.
Changed upstream objects absent from mod: `2`
  - `object:ENG_naval_role_ratios_historical` (base line 968)
  - `object:ENG_naval_role_ratios_screens_focus` (base line 1115)

### `common/ai_strategy/GER.txt`
These are strategy review notes only; do not merge automatically.
Changed upstream objects absent from mod: `3`
  - `object:GER_halt_light_armor_production_in_transitioning` (base line 362)
  - `object:GER_stock_up_on_trains_before_barbarossa` (base line 3263)
  - `object:GER_gotta_have_enough_light_tanks` (base line 4512)

### `common/ai_strategy/JAP.txt`
These are strategy review notes only; do not merge automatically.
Changed upstream objects absent from mod: `1`
  - `object:JAP_invade_burma` (base line 2379)

### `common/ai_strategy/USA.txt`
These are strategy review notes only; do not merge automatically.
Changed upstream objects absent from mod: `1`
  - `object:USA_ENG_sync_invasions_on_europe` (base line 534)

### `common/ai_strategy/default.txt`
These are strategy review notes only; do not merge automatically.
Changed upstream objects absent from mod: `2`
  - `object:default_major_SF_para` (base line 590)
  - `object:default_major_SF_marines` (base line 606)


## Already Matching Upstream Changes

`144` changed existing upstream objects already match the mod after normalization.


## Drift Scan: Missing Current-Base Objects

No missing current-base objects were found in high-value overwritten files.

## Drift Scan: Base-Order Mismatches

No base-order mismatches were found for files with complete base object coverage.

## Diagnostics

- `common/doctrines/grand_doctrines/special_forces_grand_doctrines.txt`: old base: file is absent
- `common/doctrines/subdoctrines/special_forces/special_forces_subdoctrines.txt`: old base: file is absent
- `common/doctrines/tracks/special_forces_tracks.txt`: old base: file is absent
- `common/doctrines/subdoctrines/sea/navy_submarine_doctrines.txt`: current base: unclosed block 'long_range_submarines' starting at line 297
- `common/doctrines/subdoctrines/sea/navy_submarine_doctrines.txt`: mod: unclosed block 'long_range_submarines' starting at line 297

## Skipped Changed Overwritten Files

- `common/ai_equipment/ENG_naval.txt`: AI tuning path; rerun with --include-ai to inspect
- `common/ai_equipment/SOV_tank.txt`: AI tuning path; rerun with --include-ai to inspect
- `common/ai_equipment/USA_tank.txt`: AI tuning path; rerun with --include-ai to inspect
- `common/ai_strategy_plans/ENG_historical_strategy_plan.txt`: AI tuning path; rerun with --include-ai to inspect
- `common/ai_strategy_plans/GER_alternate_strategy_plan.txt`: AI tuning path; rerun with --include-ai to inspect
- `common/ai_templates/generic.txt`: AI tuning path; rerun with --include-ai to inspect
- `common/ai_templates/templates_CHI.txt`: AI tuning path; rerun with --include-ai to inspect
- `common/ai_templates/templates_ENG.txt`: AI tuning path; rerun with --include-ai to inspect
- `common/ai_templates/templates_GER.txt`: AI tuning path; rerun with --include-ai to inspect
- `common/ai_templates/templates_HUN.txt`: AI tuning path; rerun with --include-ai to inspect
- `common/ai_templates/templates_ITA.txt`: AI tuning path; rerun with --include-ai to inspect
- `common/ai_templates/templates_JAP.txt`: AI tuning path; rerun with --include-ai to inspect
- `common/ai_templates/templates_SOV.txt`: AI tuning path; rerun with --include-ai to inspect
- `common/ai_templates/templates_USA.txt`: AI tuning path; rerun with --include-ai to inspect

## Base Changed But Not Overwritten

- `common/abilities/CHI_abilities.txt`
- `common/abilities/JAP_abilities.txt`
- `common/abilities/PHI_abilities.txt`
- `common/abilities/SWE_abilities.txt`
- `common/achievements.txt`
- `common/ai_areas/default.txt`
- `common/ai_faction_theaters/ai_faction_theaters.txt`
- `common/ai_strategy/HOL.txt`
- `common/ai_strategy/INS.txt`
- `common/ai_strategy_plans/AST_alternate_strategy_plan.txt`
- `common/ai_strategy_plans/AST_historical_strategy_plan.txt`
- `common/ai_strategy_plans/AUS_alternate_strategy_plan.txt`
- `common/ai_strategy_plans/ENG_alternate_strategy_plan.txt`
- `common/ai_strategy_plans/GUAY_historical_strategy_plan.txt`
- `common/ai_strategy_plans/HOL_TAOG_alternate_strategy_plan.txt`
- `common/ai_strategy_plans/HOL_TAOG_historical_strategy_plan.txt`
- `common/ai_strategy_plans/HOL_alternate_strategy_plan.txt`
- `common/ai_strategy_plans/HOL_historical_strategy_plan.txt`
- `common/ai_strategy_plans/HUN_ww_alternate.txt`
- `common/ai_strategy_plans/INS_alternate_strategy_plan.txt`
- `common/ai_strategy_plans/INS_historical_strategy_plan.txt`
- `common/ai_strategy_plans/JAP_alternate_strategy_plan.txt`
- `common/ai_strategy_plans/JAP_historical_strategy_plan.txt`
- `common/ai_strategy_plans/MAN_TSR_alternate_strategy_plan.txt`
- `common/ai_strategy_plans/MAN_TSR_historical_strategy_plan.txt`
- `common/ai_strategy_plans/MAN_alternate_strategy_plan.txt`
- `common/ai_strategy_plans/MAN_historical_strategy_plan.txt`
- `common/ai_strategy_plans/MEX.txt`
- `common/ai_strategy_plans/NOR_alternate_strategy_plan.txt`
- `common/ai_strategy_plans/NZL_alternate_strategy_plan.txt`
- `common/ai_strategy_plans/NZL_historical_strategy_plan.txt`
- `common/ai_strategy_plans/RAJ_GOE_historical_strategy_plan.txt`
- `common/ai_strategy_plans/RNG_historical_strategy_plan.txt`
- `common/ai_strategy_plans/SIA_alternate_strategy_plan.txt`
- `common/ai_strategy_plans/SIA_historical_strategy_plan.txt`
- `common/ai_templates/templates_INS.txt`
- `common/ai_templates/templates_IRQ.txt`
- `common/ai_templates/templates_PRC.txt`
- `common/ai_templates/templates_SIA.txt`
- `common/ai_templates/templates_SWI.txt`
- `common/autonomous_states/dominion.txt`
- `common/autonomous_states/supervised_state.txt`
- `common/autonomous_states/taog_associated_dominion_puppet.txt`
- `common/autonomous_states/taog_indonesian_union_state.txt`
- `common/bookmarks/blitzkrieg.txt`
- `common/bookmarks/the_gathering_storm.txt`
- `common/buildings/00_buildings.txt`
- `common/characters/AST.txt`
- `common/characters/BRA.txt`
- `common/characters/CHI.txt`
- `common/characters/CHL.txt`
- `common/characters/CPS.txt`
- `common/characters/HOL.txt`
- `common/characters/INS.txt`
- `common/characters/JAP.txt`
- `common/characters/LEB.txt`
- `common/characters/MAL.txt`
- `common/characters/NZL.txt`
- `common/characters/PER.txt`
- `common/characters/PHI.txt`
- `common/characters/PRC.txt`
- `common/characters/RAJ.txt`
- `common/characters/SIA.txt`
- `common/characters/SWE.txt`
- `common/characters/SYR.txt`
- `common/characters/_documentation.md`
- `common/collections/generic_collections.txt`
- `common/combat_tactics.txt`
- `common/countries/Atjeh.txt`
- `common/countries/Bali.txt`
- `common/countries/Bougainville.txt`
- `common/countries/Champasak.txt`
- `common/countries/Gowa.txt`
- `common/countries/Indonesia.txt`
- `common/countries/Pontianak.txt`
- `common/countries/Siak.txt`
- `common/countries/Ternate.txt`
- `common/countries/Vanuatu.txt`
- `common/countries/colors.txt`
- `common/countries/cosmetic.txt`
- `common/country_leader/taog_traits.txt`
- `common/country_tags/00_countries.txt`
- `common/decisions/AFG.txt`
- `common/decisions/AST.txt`
- `common/decisions/CHI_decisions.txt`
- `common/decisions/ENG.txt`
- `common/decisions/FRA.txt`
- `common/decisions/GER.txt`
- `common/decisions/HOL.txt`
- `common/decisions/INS.txt`
- `common/decisions/IRQ.txt`
- `common/decisions/JAP.txt`
- `common/decisions/MAL.txt`
- `common/decisions/NOR.txt`
- `common/decisions/NZL.txt`
- `common/decisions/PER.txt`
- `common/decisions/POR.txt`
- `common/decisions/PRC.txt`
- `common/decisions/RAJ_GOE.txt`
- `common/decisions/SIA.txt`
- `common/decisions/_debug_decisions.txt`
- `common/decisions/categories/00_decision_categories.txt`
- `common/decisions/categories/00_formable_categories.txt`
- `common/decisions/categories/AST_decision_categories.txt`
- `common/decisions/categories/INS_decision_categories.txt`
- `common/decisions/categories/SIA_decision_categories.txt`
- `common/decisions/foreign_influence.txt`
- `common/decisions/formable_nation_decisions.txt`
- `common/decisions/resource_prospecting.txt`
- `common/defines/00_defines.lua`
- `common/defines/00_graphics.lua`
- `common/dynamic_modifiers/ABDA_dynamic_modifiers.txt`
- `common/dynamic_modifiers/GoE_dynamic_modifiers.txt`
- `common/dynamic_modifiers/TAOG_dynamic_modifiers.txt`
- `common/equipment_groups/mio_equipment_groups.txt`
- `common/factions/goals/faction_goals_long_term.txt`
- `common/factions/goals/faction_goals_medium_term.txt`
- `common/factions/goals/faction_goals_short_term.txt`
- `common/factions/rules/call_to_war_rules.txt`
- `common/factions/rules/joining_rules.txt`
- `common/factions/templates/unique_minor_factions.txt`
- `common/focus_inlay_windows/ast_right_vs_left_campaign_empty_inlay_window.txt`
- `common/focus_inlay_windows/ast_right_vs_left_campaign_inlay_window.txt`
- `common/focus_inlay_windows/documentation.md`
- `common/focus_inlay_windows/sia_khana_ratsadon_inlay_window.txt`
- `common/frontend/backgrounds/base_backgrounds.txt`
- `common/game_rules/00_game_rules.txt`
- `common/ideas/ABDA_ideas.txt`
- `common/ideas/SOV.txt`
- `common/ideas/_event.txt`
- `common/ideas/afghanistan.txt`
- `common/ideas/australia.txt`
- `common/ideas/brazil.txt`
- `common/ideas/britain.txt`
- `common/ideas/british_raj_goe.txt`
- `common/ideas/canada.txt`
- `common/ideas/comchina.txt`
- `common/ideas/france.txt`
- `common/ideas/indonesia.txt`
- `common/ideas/malaysia.txt`
- `common/ideas/manchukou.txt`
- `common/ideas/netherlands.txt`
- `common/ideas/new_zealand.txt`
- `common/ideas/portugal.txt`
- `common/ideas/siam.txt`
- `common/ideas/usa.txt`
- `common/ideas/zzz_generic.txt`
- `common/intelligence_agencies/00_intelligence_agencies.txt`
- `common/medals/00_medals.txt`
- `common/military_industrial_organization/organizations/00_generic_organization.txt`
- `common/military_industrial_organization/organizations/AST_organization.txt`
- `common/military_industrial_organization/organizations/CHI_organization.txt`
- `common/military_industrial_organization/organizations/HUN_organization.txt`
- `common/military_industrial_organization/organizations/INS_organization.txt`
- `common/military_industrial_organization/organizations/NZL_organization.txt`
- `common/military_industrial_organization/organizations/PRC_organization.txt`
- `common/military_industrial_organization/organizations/RAJ_GOE_organization .txt`
- `common/military_industrial_organization/organizations/SIA_organization.txt`
- `common/names/00_names.txt`
- `common/national_focus/00_titlebar_styles.txt`
- `common/national_focus/abdacom_shared_branch.txt`
- `common/national_focus/afghanistan.txt`
- `common/national_focus/australia.txt`
- `common/national_focus/australia_taog.txt`
- `common/national_focus/austria.txt`
- `common/national_focus/baltic_shared.txt`
- `common/national_focus/belgium.txt`
- `common/national_focus/brazil.txt`
- `common/national_focus/canada.txt`
- `common/national_focus/chile.txt`
- `common/national_focus/china_communist_sea.txt`
- `common/national_focus/china_nationalist_sea.txt`
- `common/national_focus/china_nationalist_warlord_TSR.txt`
- `common/national_focus/china_shared.txt`
- `common/national_focus/china_shared_TSR.txt`
- `common/national_focus/china_warlord_sea.txt`
- `common/national_focus/congo.txt`
- `common/national_focus/congo_shared.txt`
- `common/national_focus/czechoslovakia_mu.txt`
- `common/national_focus/denmark.txt`
- `common/national_focus/estonia.txt`
- `common/national_focus/finland.txt`
- `common/national_focus/france.txt`
- `common/national_focus/india_goe.txt`
- `common/national_focus/indonesia.txt`
- `common/national_focus/indonesia_joint.txt`
- `common/national_focus/iraq.txt`
- `common/national_focus/italy.txt`
- `common/national_focus/japan.txt`
- `common/national_focus/manchukuo_TSR.txt`
- `common/national_focus/netherlands.txt`
- `common/national_focus/new_zealand.txt`
- `common/national_focus/nordic_shared.txt`
- `common/national_focus/norway.txt`
- `common/national_focus/persia.txt`
- `common/national_focus/philippines.txt`
- `common/national_focus/poland.txt`
- `common/national_focus/portugal.txt`
- `common/national_focus/siam.txt`
- `common/national_focus/sweden.txt`
- `common/national_focus/toa_shared_military_branch.txt`
- `common/national_focus/turkey.txt`
- `common/national_focus/uk.txt`
- `common/national_focus/usa.txt`
- `common/occupation_laws/occupation_laws.txt`
- `common/on_actions/00_on_actions.txt`
- `common/on_actions/01_tfv_on_actions.txt`
- `common/on_actions/04_mtg_on_actions.txt`
- `common/on_actions/08_bba_on_actions.txt`
- `common/on_actions/13_goe_on_actions.txt`
- `common/on_actions/14_sea_on_actions.txt`
- `common/on_actions/16_taog_on_actions.txt`
- `common/on_actions/_documentation.md`
- `common/operation_phases/taog_free_general.txt`
- `common/operations/00_operations.txt`
- `common/operations/LaR_FRA_operations.txt`
- `common/opinion_modifiers/taog_opinion_modifiers.txt`
- `common/peace_conference/ai_peace/JAP.txt`
- `common/peace_conference/ai_peace/RAJ.txt`
- `common/peace_conference/cost_modifiers/AST_peace.txt`
- `common/peace_conference/cost_modifiers/JAP_peace.txt`
- `common/raids/_documentation.md`
- `common/raids/air_raids.txt`
- `common/raids/air_raids_custom.txt`
- `common/raids/categories/raid_categories.txt`
- `common/raids/land_infiltration_custom.txt`
- `common/raids/land_infiltration_raids.txt`
- `common/raids/naval_commando_raids.txt`
- `common/ribbons/00_ribbons.txt`
- `common/script_constants/propaganda_campaigns.txt`
- `common/scripted_effects/00_scripted_effects.txt`
- `common/scripted_effects/AST_scripted_effects.txt`
- `common/scripted_effects/FRA_scripted_effects.txt`
- `common/scripted_effects/INS_scripted_effects.txt`
- `common/scripted_effects/RAJ_GOE_scripted_effects.txt`
- `common/scripted_effects/SIA_scripted_effects.txt`
- `common/scripted_guis/AST_cabinet_trust_scripted_gui.txt`
- `common/scripted_guis/INS_revolution_scripted_gui.txt`
- `common/scripted_guis/SIA_movie_theater_campaigns_scripted_gui.txt`
- `common/scripted_localisation/00_scripted_localisation_countries_RU_loc.txt`
- ... 98 more
