-- === --
-- DAI --
-- === --

-- =============== --
-- Non-AI Specific --
-- =============== --

-- Template Design: Base cost too high for AI (and humans too with XP use creep). --
NDefines.NMilitary.BASE_DIVISION_BRIGADE_GROUP_COST = 1
NDefines.NMilitary.BASE_DIVISION_BRIGADE_CHANGE_COST = 1
NDefines.NMilitary.BASE_DIVISION_SUPPORT_SLOT_COST = 1
NDefines.NMilitary.LAND_EQUIPMENT_BASE_COST = 3
NDefines.NMilitary.LAND_EQUIPMENT_RAMP_COST = 0
NDefines.NMilitary.NAVAL_EQUIPMENT_BASE_COST = 1
NDefines.NMilitary.AIR_EQUIPMENT_BASE_COST = 1
NDefines.NMilitary.AIR_EQUIPMENT_RAMP_COST = 0
NDefines.NMilitary.NAVAL_EQUIPMENT_RAMP_COST = 0

-- Production Licenses: remove civilian-factory costs from scripted and traditional licenses. --
NDefines.NProduction.BASE_LICENSE_IC_COST = 0
NDefines.NProduction.LICENSE_IC_COST_YEAR_INCREASE = 0


-- =========== --
-- AI Specific --
-- =========== --

-- Research --
-- I believe this is deprecated and does nothing.
NDefines.NAI.RESEARCH_LAND_DOCTRINE_NEED_GAIN_FACTOR = 0                      	-- Multiplies value based on relative military industry size / country size.
NDefines.NAI.RESEARCH_NAVAL_DOCTRINE_NEED_GAIN_FACTOR = 0                       -- Multiplies value based on relative naval industry size / country size.
NDefines.NAI.RESEARCH_AIR_DOCTRINE_NEED_GAIN_FACTOR = 0                         -- Multiplies value based on relative number of air base / country size.
NDefines.NAI.RESEARCH_NEW_DOCTRINE_RANDOM_FACTOR = 0

NDefines.NAI.RESEARCH_DAYS_BETWEEN_WEIGHT_UPDATE = 1
NDefines.NAI.RESEARCH_AHEAD_BONUS_FACTOR = 25.0
NDefines.NAI.RESEARCH_AHEAD_OF_TIME_FACTOR = 1.5
NDefines.NAI.RESEARCH_BONUS_FACTOR = 2
NDefines.NAI.MAX_AHEAD_RESEARCH_PENALTY = 8
--NDefines.NAI.RESEARCH_BASE_DAYS = 1000
NDefines.NAI.RESEARCH_YEARS_BEHIND_FACTOR = 0.20

-- Combat XP Usage --
NDefines.NAI.DESIRE_USE_XP_TO_UNLOCK_LAND_DOCTRINE = 1    -- How quickly is desire to unlock land doctrines accumulated?
NDefines.NAI.DESIRE_USE_XP_TO_UNLOCK_NAVAL_DOCTRINE = 1   -- How quickly is desire to unlock naval doctrines accumulated?
NDefines.NAI.DESIRE_USE_XP_TO_UNLOCK_AIR_DOCTRINE = 1     -- How quickly is desire to unlock air doctrines accumulated?

NDefines.NAI.DESIRE_USE_XP_TO_UPDATE_LAND_TEMPLATE = 100.0 --2.0    -- How quickly is desire to update/create templates accumulated?
NDefines.NAI.VARIANT_CREATION_XP_RESERVE_LAND = 10
NDefines.NAI.VARIANT_CREATION_XP_RESERVE_NAVY = 30
NDefines.NAI.VARIANT_CREATION_XP_RESERVE_AIR  = 30

NDefines.NAI.DESIRE_USE_XP_TO_UPGRADE_LAND_EQUIPMENT = 50.0  -- How quickly is desire to update/create land equipment variants accumulated?
NDefines.NAI.DESIRE_USE_XP_TO_UPGRADE_NAVAL_EQUIPMENT = 100.0 -- How quickly is desire to update/create naval equipment variants accumulated?
NDefines.NAI.DESIRE_USE_XP_TO_UPGRADE_AIR_EQUIPMENT = 100.0   -- How quickly is desire to update/create air equipment variants accumulated?

NDefines.NAI.DESIRE_USE_XP_TO_UNLOCK_ARMY_SPIRIT = 0.4    -- How quickly is desire to unlock army spirits accumulated?
NDefines.NAI.DESIRE_USE_XP_TO_UNLOCK_NAVY_SPIRIT = 0.4   -- How quickly is desire to unlock naval spirits accumulated?
NDefines.NAI.DESIRE_USE_XP_TO_UNLOCK_AIR_SPIRIT = 0.4     -- How quickly is desire to unlock air spirits accumulated?

NDefines.NAI.DEFAULT_LEGACY_VARIANT_CREATION_XP_CUTOFF_LAND = 20
NDefines.NAI.DEFAULT_MODULE_VARIANT_CREATION_XP_CUTOFF_LAND = 10
NDefines.NAI.DEFAULT_MODULE_VARIANT_CREATION_XP_CUTOFF_NAVY = 50
NDefines.NAI.DEFAULT_MODULE_VARIANT_CREATION_XP_CUTOFF_AIR = 25
NDefines.NAI.DEFAULT_LEGACY_VARIANT_CREATION_XP_CUTOFF_AIR = 20

-- Naval refits: keep AI yards on new ships instead of pulling existing ships out of service.
NDefines.NAI.REFIT_SHIP_RELUCTANCE = 5000
NDefines.NAI.REFIT_SHIP_PERCENTAGE_OF_FORCES = 0.0

-- Naval invasions: allow AI planning against countries with much stronger navies.
-- Naval supremacy and execution requirements still apply after an invasion plan is drawn.
NDefines.NAI.ENEMY_NAVY_STRENGTH_DONT_BOTHER = 1000

-- Buildings
NDefines.NAI.BUILDING_TARGETS_BUILDING_PRIORITIES = { -- Buildings in priority order when considering building_target strategies. First has the greatest priority; omitted has the lowest.
	'air_base',
	'infrastructure',
	'synthetic_refinery',
	'dockyard',
	'industrial_complex',
	'arms_factory',
}
NDefines.NAI.CONSTRUCTION_PRIO_SUPPLY_BUILDING = 3.50
NDefines.NAI.CONSTRUCTION_PRIO_RAILWAY = 20.0
NDefines.NAI.CONSTRUCTION_PRIO_FACTOR_OWNED_CORE = 5.0
NDefines.NAI.CONSTRUCTION_PRIO_FACTOR_OWNED_NONCORE = 3.0

-- Laws: If the values for these exceed ai_will_do, the AI will not change its laws unless the internal source code does it.
NDefines.NAI.MIN_AI_SCORE_TO_MOBILIZATION_LAW_OVERRIDE_HARD_CODED_SCORE = 1.0
NDefines.NAI.MIN_AI_SCORE_TO_ECONOMY_LAW_OVERRIDE_HARD_CODED_SCORE = 1.0
NDefines.NAI.MIN_AI_SCORE_TO_TRADE_LAW_OVERRIDE_HARD_CODED_SCORE = 1.0
NDefines.NAI.MIN_AI_SCORE_TO_ALL_LAWS_OVERRIDE_HARD_CODED_SCORE = 1.0
