# Dynamic AI MP — Mod Changes

Running list of all differences from the base game. AI weight-only changes are summarized as "rework" rather than listed individually.

---

## Core Systems

### Defines (`DAI_defines.lua`)
- Division template costs reduced to 1 XP each (brigade group, brigade change, support slot)
- Ahead-of-time research penalty reduced (3 → 2)
- Vanilla automatic doctrine weighting disabled — DAI manages doctrine priorities manually
- AI desire to use XP on template updates greatly increased (2 → 100); naval/air equipment upgrades set to 100
- Army spirit unlock desire lowered (prioritizes templates over spirits)
- Module variant creation XP cutoffs set (50 land / 25 naval / 25 air)

### On-Actions (`DAI_on_actions.txt`)
- Custom daily/monthly update hooks for build orders, trade law evaluation, armor template progression

### Scripted Effects
- `DAI_set_build_order_GER` — Daily advisor/idea sequencing for Germany (Ludwig Erhard, Göring, Raeder, etc.)
- `DAI_set_wants_armor_flag` — Flags countries that should produce armor (majors or 40+ mil factories)
- `DAI_set_armor_template_flags` — Selects armor template tier (light → medium → improved → advanced) based on tech and date
- `DAI_set_desired_trade_law` — Resource deficit calculator comparing all 6 resources against consumption for optimal trade policy

### Scripted Triggers
- `DAI_should_build_planes` — Gated to majors + 30+ mil factory countries + CAN/HUN
- `DAI_should_build_tanks` — Flag-driven (`DAI_build_armor`)
- `DAI_should_build_paratroopers` — Disabled
- Naval research triggers split by role (general, anti-sub, cruiser, carrier, submarine) with country-specific conditions
- Historical vs alternate AI path detection for ENG, FRA, GER (historical/democratic/kaiser), SOV
- `DAI_should_upgrade_manpower_law` — Fires when reserves < 40% of deployed or < 100k

---

## Economy & Manpower Laws

### Economy Laws (`_economic.txt`)
- Rework of AI economy law transition weights
- Forces progression isolation → partial → war → total based on factory count, war support, and political situation
- Germany gated behind specific focus for low economic mobilisation

### Manpower Laws (`_manpower.txt`)
- Rework of AI conscription law weights
- Auto-rotates through tiers based on government type and war situation

### Law Upgrade Decisions (`DAI_decisions_laws.txt`)
- Currently disabled (commented out); designed to force AI law upgrades for non-majors

---

## AI Strategy — Country Overrides

### Germany (`GER.txt`)
- Army composition: 60/30/5/5 infantry/armor/garrison/mountaineer (vanilla: 75% infantry, negligible armor)
- Aggressive early air: +110% air factory balance pre-1937.6
- Accelerated rearmament: +50% mil/civ ratio 1937–1940
- Railway gun production at +100%
- Blitzkrieg Poland: force concentration on Warsaw/Łódź, front armor score 250
- Blocks antagonism of NED/BEL/LUX until "Around Maginot" focus
- Reduced early intelligence agency use
- Equipment stockpiling for transport planes and support equipment
- Market management: progressive equipment sale thresholds after Anschluss and Sudetenland
- Blitz air strategy: prevents air attacks on England before Fall Gelb; stops Blitz when pivoting east to focus on Barbarossa
- Barbarossa air focus: regional air concentration on Baltic, Eastern Poland, Southern Ukraine until border defenses broken
- Raiding: North Sea raids gated by war with NOR/SOV; Atlantic raids include CAN
- Espionage: collaboration government vs France, intel network construction
- Build order scripted effect: daily advisor/idea sequencing

### Soviet Union (`SOV.txt`)
- Army composition: 63/30/5 infantry/armor/mountaineer
- Medium tank production at +100% variant factor
- Air factory delay until "Foster Flying Clubs" focus
- Focus-dependent diplomatic activations (Southern Thrust, Poland Claims, Finland, Sinkiang)
- Paranoia management decisions auto-trigger at thresholds

### USA (`USA.txt`)
- Army composition: garrison (10%), marines (15%), armor (20%)
- Pre-war diplomacy: military access from ENG/FRA post-1940.9.9
- Theater deployment buffers: South England (20%), North Africa (15%), Atlantic (20%), Africa zones (10–15%)
- "Gang up on Germany" aligned with England
- Go-time: USA-only, date gate 1943.2.1, invade Japan 80, Pacific naval dominance across 9 regions

### England (`ENG.txt`)
- Defensive: 70/15/10/5 infantry/armor/garrison/marines
- Air floor: minimum 1 tactical + 1 strategic bomber factory after 30 mils

### Italy (`ITA.txt`)
- Naval bomber specialist: +100% naval bomber ratio
- Mountaineers (5%) + marines (5%) for Alpine/Mediterranean ops
- Contest-the-med: gated by war with FRA after 1939.9.1

### France (`FRA.txt`)
- Aggressive air: fighter +200, CAS +50
- Mountaineers +10% (Alpine defense)
- Area priorities: Europe +110, Africa -50, Asia +75
- Accepts USA military access post-1940.9.9
- Vichy French protection/antagonism rules

### Japan (`JAP.txt`)
- Faction-responsive building: army → mils, navy → dockyards, zaibatsu → civs
- Phase transitions: early 90% infantry + 10% marines → late balanced
- CAS focused: +500% early game

### China (`CHI.txt`)
- Pure infantry: 95% ratio
- Fighter focus: +75 (vs Japan air superiority)
- Blocks medium/large plane production before 1940
- Prioritizes industrial factories before 1937

### Siam (`SIA.txt`)
- Japan-conditional: war prep only if Japan fascist post-1941.12.6
- Jungle warfare: -20% inf, +10% marines, +10% mountaineers

### Manchukuo (`MAN_ai_strategies.txt`)
- Blocks Axis alliance, prevents European guarantees

### Naval Strategy — All Nations (`DAI_naval_strategy.txt`)
- Convoy production tiers (100 → 800 stockpile targets)
- Adaptive role ratios by navy size: small (submarine), medium (balanced), large (capital ship)
- Force concentration for large armies (50+ divisions)

### Default Strategies (`default.txt`)
- Modified default naval/production weights for generic countries

---

## AI Strategy Plans

### Germany — Historical (`GER_historical_strategy_plan.txt`)
- Custom focus order with precise date-driven scheduling
- Economic growth → Rhineland → war economy → panzer doctrine → air → Italy alliance → Molotov-Ribbentrop → Danzig → Weserübung → Around Maginot → Barbarossa
- Blocked focuses: no Rosenberg puppets, no monarchist sentiment, no alliances with USSR/China/Turkey
- Machine tools & excavation research boosted

### Germany — Alternate (`GER_alternate_strategy_plan.txt`)
- Democratic Weimar restoration path
- Monarchist Kaiser restoration path (Götterdämmerung DLC)

### Soviet Union — Historical (`SOV_historical_strategy_plan.txt`)
- Custom focus order: heavy industrialization → purges → Baltic security → Bessarabia/Poland → military reorganization → move industry to Urals → Iran → specialist units

### Other Countries
- Italy, France, Romania, Ethiopia: custom historical focus sequences
- Siam: triggers when Japan goes fascist

---

## AI Templates

### Philosophy
- Simplified infantry templates, armor templates disabled to prevent AI tank spam
- Standardized 18.0 width infantry

### Country-Specific
- **Germany**: 9 inf + 3 support (engineer, artillery, anti-air); late-war adds field hospital. Armor commented out.
- **Soviet Union**: 9 inf + 5 support (engineer, artillery, anti-air, anti-tank, signal) — heaviest support load. Armor commented out.
- **USA**: 2 templates (isolation → post-isolation with anti-tank + recon). Armor commented out.
- **England**: 9 inf + engineer, artillery, anti-air.
- **Italy**: Includes recon support (unique). Armor disabled.

### Generic Fallback (`generic.txt`)
- Armor progression via `DAI_default_armor_template` flag (0–3): light → light-medium → medium → advanced medium with SP anti-air/TDs
- Majors excluded (use country-specific templates)

---

## AI Equipment Designs

- Custom light/medium tank designs with specific module layouts (`DAI_light_armor.txt`, `DAI_medium_armor.txt`)
- Country-specific designs for GER (Daimler-Benz team), SOV, USA, ENG, FRA, ITA, JAP, HUN

---

## Technology & Doctrine AI Weights

- Rework of all technology research AI weights using DAI conditional triggers
- Research gated by country capabilities (`should_build_tanks`, `should_build_planes`, `should_research_navy`)
- Date-based progression windows with large multipliers for experienced AI
- Rework of all doctrine research AI weights
- Germany: 25x armored spearhead preference; ENG/FRA: 25x armored infantry support
- Non-majors discouraged from spreading XP thin

---

## Continuous Focuses (`generic.txt`)
- Naval production: Japan gets 10x AI priority
- Air production: GER, ENG, FRA, USA, ITA each get 10x AI priority

---

## Characters

### France (`FRA.txt`)
- Added characters and modified visibility/traits for alternate government paths

### Italy (`ITA.txt`)
- Rework of advisor AI hire weights (Graziani priority increased, Ambrosio disabled)

### Soviet Union (`SOV.txt`)
- Rework of field commander AI hire weights (Rokossovsky, Vasilevsky, Konev, Timoshenko increased)

---

## Decisions

### Military — Template Spawning (`DAI_decisions_military.txt`)
- `AI_Infantry_Filler_Spawn_18w` — Mandatory for all AI
- `AI_Light_Armor_Prototype_1–2`, `AI_Medium_Armor_Prototype_1–2` — Flag-gated template creation

### Military — Starting Division Cleanup (`DAI_decisions_military.txt`)
- ENG/FRA/GER/POL: disband useless starting divisions (cavalry, light tanks)

### Soviet Decisions (`SOV.txt`)
- Rework of paranoia decision AI weights (auto-trigger at paranoia thresholds)

### Italy Decisions (`ITA.txt`)
- Ethiopia withdrawal date changed (1937.01.01 → 1937.03.01)
- AI weights modified for communist/socialist paths

### Political Decisions (`political_decisions.txt`)
- Minor AI weight adjustments (improved_worker_conditions threshold, fascism support gating)

---

## Ideas

### Germany (`GER.txt`)
- `general_staff`: army org +5%, planning speed +25%
- Ideas for alternate government paths (kaiserreich, democracy, national revitalization)

### Economy Laws (`_economic.txt`)
- Rework of economy law AI weights and availability conditions

### Manpower Laws (`_manpower.txt`)
- Rework of conscription law AI weights and availability conditions

---

## National Focus

### Soviet Union (`soviet.txt`)
- Custom `SOV_infrastructure_effort_nsb` — NSB-compatible infrastructure scaling with instant 2-level construction

---

## Events

### Germany (`WUW_Germany.txt`)
- MEFO Bills economic system with branching choices
- Inner circle character events (Todt, Speer, Göring, Himmler, Goebbels, Hess, Bormann)
- Dynamic economic modifiers with intelligence penalties
- Historical incident events (Franz Stigler mercy event)
- Götterdämmerung compatibility events
