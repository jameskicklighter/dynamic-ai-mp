#!/usr/bin/env python3
"""Validate and generate DAI small-aircraft licensing and targeting data.

The A/B/C variants remain authored in DAI_license_plane_effects.txt. This tool
never rewrites that catalog. It builds exact/native triggers, provider creation,
recipient-local delivery, diagnostics, and marked AI-equipment target regions.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
VARIANT_SOURCE = ROOT / "common/scripted_effects/DAI_license_plane_effects.txt"
TRIGGER_OUTPUT = ROOT / "common/scripted_triggers/DAI_license_plane_role_triggers.txt"
CREATE_OUTPUT = ROOT / "common/scripted_effects/DAI_license_plane_role_effects.txt"
DELIVERY_OUTPUT = ROOT / "common/scripted_effects/DAI_license_plane_delivery_effects.txt"
DIAGNOSTIC_OUTPUT = ROOT / "common/scripted_effects/DAI_license_plane_diagnostics.txt"
AI_EQUIPMENT_OUTPUT = ROOT / "common/ai_equipment/DAI_planes.txt"
MIO_TOKEN_SOURCE = ROOT / "common/synchronized_dynamic_tokens/DAI_license_tokens.txt"
MIO_ORGANIZATION_ROOT = ROOT / "common/military_industrial_organization/organizations"
TECHNOLOGY_ROOT = ROOT / "common/technologies"


@dataclass(frozen=True)
class Role:
    key: str
    variant_label: str
    mio_helper: str


@dataclass(frozen=True)
class Tier:
    key: str
    log_key: str
    year: int
    frame_tech: str
    better_engine: str
    chassis_type: str
    roles: tuple[Role, ...]


@dataclass(frozen=True)
class Variant:
    name: str
    equipment_type: str
    modules: tuple[tuple[str, str], ...]


TARGET_ORDER = ("A", "B", "ANY", "C")
TARGET_OFFSETS = {"A": 0, "B": 100, "ANY": 200, "C": 300}
TIER_TARGET_BASE = {
    "basic_small_airframe": 900,
    "improved_small_airframe": 1900,
    "advanced_small_airframe": 2900,
}

ROLE_TYPE_PREFIX = {
    "fighter": "small_plane_airframe",
    "cas": "small_plane_cas_airframe",
    "naval_bomber": "small_plane_naval_bomber_airframe",
    "carrier_fighter": "cv_small_plane_airframe",
    "carrier_naval_bomber": "cv_small_plane_naval_bomber_airframe",
}

WEAPON_SLOT_COUNT = {1936: 2, 1940: 3, 1944: 4}
SPECIAL_SLOT_COUNT = {1936: 2, 1940: 3, 1944: 4}
CARRIER_SPECIAL_SLOT_COUNT = {1936: 2, 1940: 3, 1944: 3}

# Static BBA values used only to reject an invalid authored exact catalog.
# The game still performs its own designer legality checks for flexible ANY targets.
AIRFRAME_WEIGHT = {
    1936: {"land": 4.0, "carrier": 5.0},
    1940: {"land": 5.0, "carrier": 6.0},
    1944: {"land": 6.0, "carrier": 6.0},
}
MODULE_WEIGHT = {
    "empty": 0.0,
    "light_mg_2x": 1.0,
    "light_mg_4x": 2.0,
    "heavy_mg_2x": 2.5,
    "heavy_mg_4x": 5.0,
    "aircraft_cannon_1_1x": 3.0,
    "aircraft_cannon_1_2x": 6.0,
    "bomb_locks": 4.0,
    "torpedo_mounting": 5.0,
    "torpedo_mounting_2": 8.0,
    "torpedo_mounting_3": 11.0,
    "tank_buster_1": 8.0,
    "tank_buster_2": 12.0,
    "engine_1_1x": 0.0,
    "engine_2_1x": 0.0,
    "engine_3_1x": 0.0,
    "engine_4_1x": 0.0,
    "armor_plate_small": 2.0,
    "self_sealing_fuel_tanks_small": 1.0,
    "fuel_tanks_small": 2.0,
    "drop_tanks": 3.0,
    "dive_brakes_small": 2.0,
}
ENGINE_THRUST = {
    "engine_1_1x": 11.0,
    "engine_2_1x": 16.0,
    "engine_3_1x": 25.0,
    "engine_4_1x": 30.0,
}

FIGHTER_ANY_WEAPONS = (
    "aircraft_cannon_1_2x",
    "heavy_mg_4x",
    "light_mg_4x",
)

# Keep flexible native targets aware of useful intermediate modules even when
# the exact A/B/C catalog does not use every step in an upgrade chain.
ANY_SLOT_OVERRIDES = {
    (
        "improved_small_airframe",
        "naval_bomber",
        "fixed_main_weapon_slot",
    ): (
        "torpedo_mounting_3",
        "torpedo_mounting_2",
        "torpedo_mounting",
    ),
}


SMALL_ROLES = (
    Role("fighter", "Fighter", "DAI_set_air_design_team_fighter"),
    Role("cas", "CAS", "DAI_set_air_design_team_cas"),
    Role("naval_bomber", "Naval Bomber", "DAI_set_air_design_team_naval_bomber"),
    Role("carrier_fighter", "Carrier Fighter", "DAI_set_air_design_team_carrier_fighter"),
    Role(
        "carrier_naval_bomber",
        "Carrier Naval Bomber",
        "DAI_set_air_design_team_carrier_naval_bomber",
    ),
)

# Exact equipment coverage is defined by each organization's included archetype
# (plus any local equipment_type override). This allow-list makes an accidental
# cross-role MIO mapping a generator error rather than a runtime-only surprise.
ROLE_MIO_COMPATIBLE_TOKENS = {
    "fighter": frozenset(
        {
            "GER_focke_wulf_organization",
            "GER_messerschmitt_organization",
            "ENG_supermarine_organization",
            "USA_north_american_aviation_organization",
            "USA_lockheed_organization",
            "SOV_mig_design_bureau_organization",
            "FRA_morane_saulnier_organization",
            "FRA_SNCAC_organization",
            "ITA_fiat_aviazione_organization",
            "ITA_savoia_marchetti_organization",
            "JAP_aichi_organization",
            "JAP_mitsubishi_organization",
        }
    ),
    "cas": frozenset(
        {
            "GER_focke_wulf_organization",
            "GER_junkers_organization",
            "ENG_supermarine_organization",
            "ENG_hawker_organization",
            "USA_north_american_aviation_organization",
            "USA_douglas_aircraft_company_organization",
            "SOV_mig_design_bureau_organization",
            "FRA_morane_saulnier_organization",
            "FRA_SNCAC_organization",
            "ITA_fiat_aviazione_organization",
            "ITA_caproni_organization",
            "JAP_aichi_organization",
            "JAP_tachikawa_aircraft_company_organization",
        }
    ),
    "naval_bomber": frozenset(
        {
            "GER_focke_wulf_organization",
            "GER_fieseler_organization",
            "ENG_supermarine_organization",
            "ENG_fairey_aviation_organization",
            "USA_north_american_aviation_organization",
            "USA_grumman_organization",
            "SOV_yakovlev_design_bureau_organization",
            "FRA_levasseur_organization",
            "FRA_SNCAC_organization",
            "ITA_fiat_aviazione_organization",
            "ITA_crda_cant_organization",
            "JAP_aichi_organization",
            "JAP_yokosuka_organization",
        }
    ),
    "carrier_fighter": frozenset(
        {
            "GER_focke_wulf_organization",
            "GER_fieseler_organization",
            "ENG_supermarine_organization",
            "ENG_fairey_aviation_organization",
            "USA_north_american_aviation_organization",
            "USA_grumman_organization",
            "SOV_yakovlev_design_bureau_organization",
            "SOV_mig_design_bureau_organization",
            "FRA_levasseur_organization",
            "FRA_morane_saulnier_organization",
            "ITA_fiat_aviazione_organization",
            "ITA_crda_cant_organization",
            "JAP_aichi_organization",
            "JAP_yokosuka_organization",
        }
    ),
    "carrier_naval_bomber": frozenset(
        {
            "GER_focke_wulf_organization",
            "GER_fieseler_organization",
            "ENG_supermarine_organization",
            "ENG_fairey_aviation_organization",
            "USA_north_american_aviation_organization",
            "USA_grumman_organization",
            "SOV_yakovlev_design_bureau_organization",
            "FRA_levasseur_organization",
            "FRA_SNCAC_organization",
            "ITA_fiat_aviazione_organization",
            "ITA_crda_cant_organization",
            "JAP_aichi_organization",
            "JAP_yokosuka_organization",
        }
    ),
}

PROFILES = ("C", "B", "A")

TIERS = (
    Tier("basic_small_airframe", "basic_small", 1936, "basic_small_airframe", "engines_2", "small_plane_airframe_1", SMALL_ROLES),
    Tier("improved_small_airframe", "improved_small", 1940, "improved_small_airframe", "engines_3", "small_plane_airframe_2", SMALL_ROLES),
    Tier("advanced_small_airframe", "advanced_small", 1944, "advanced_small_airframe", "engines_4", "small_plane_airframe_3", SMALL_ROLES),
)


MODULE_TECH = {
    "light_mg_2x": "aa_lmg",
    "light_mg_4x": "aa_lmg",
    "heavy_mg_2x": "aa_hmg",
    "heavy_mg_4x": "aa_hmg",
    "aircraft_cannon_1_1x": "aa_cannon_1",
    "aircraft_cannon_1_2x": "aa_cannon_1",
    "bomb_locks": "early_bombs",
    "torpedo_mounting": "air_torpedoe_1",
    "torpedo_mounting_2": "air_torpedoe_2",
    "torpedo_mounting_3": "air_torpedoe_3",
    "tank_buster_1": "interwar_antitank",
    "tank_buster_2": "antitank2",
    "engine_1_1x": "engines_1",
    "engine_2_1x": "engines_2",
    "engine_3_1x": "engines_3",
    "engine_4_1x": "engines_4",
    "armor_plate_small": "survivability_studies",
    "self_sealing_fuel_tanks_small": "survivability_studies",
    "fuel_tanks_small": "range_improvements",
    "drop_tanks": "range_improvements",
    "dive_brakes_small": "aircraft_construction",
}

# A recipient-local licensed design can contain a module whose technology the
# recipient does not own. Track that exact module access separately from chassis
# access so a weak Engine-II A profile cannot accidentally unlock Engine III.
LICENSED_MODULE_ACCESS = {
    ("improved_small_airframe", "engines_3"): (
        "DAI_improved_small_airframe_engine_3_profile_access",
        "DAI_has_improved_small_airframe_engine_3_profile_access",
        "DAI_can_use_improved_small_airframe_engine_3",
    ),
}


def extract_braced(text: str, opening_brace: int) -> tuple[str, int]:
    depth = 0
    in_quote = False
    escaped = False
    for index in range(opening_brace, len(text)):
        char = text[index]
        if in_quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_quote = False
            continue
        if char == '"':
            in_quote = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[opening_brace : index + 1], index + 1
    raise ValueError("Unbalanced create_equipment_variant block")


def load_variants() -> dict[str, Variant]:
    text = VARIANT_SOURCE.read_text(encoding="utf-8-sig")
    variants: dict[str, Variant] = {}
    cursor = 0
    marker = "create_equipment_variant = {"
    while True:
        start = text.find(marker, cursor)
        if start < 0:
            break
        brace = text.find("{", start)
        block, cursor = extract_braced(text, brace)
        name_match = re.search(r'\bname\s*=\s*"([^"]+)"', block)
        type_match = re.search(r"\btype\s*=\s*([^\s#}]+)", block)
        modules_start = re.search(r"\bmodules\s*=\s*\{", block)
        if not name_match or not type_match or not modules_start:
            continue
        if not re.search(r"\bparent_version\s*=\s*0\b", block):
            raise ValueError(f"{name_match.group(1)} must use parent_version = 0")
        if not re.search(r"\ballow_without_tech\s*=\s*yes\b", block):
            raise ValueError(f"{name_match.group(1)} must use allow_without_tech = yes")
        module_brace = block.find("{", modules_start.start())
        module_block, _ = extract_braced(block, module_brace)
        modules = tuple(
            re.findall(r"^\s*([A-Za-z0-9_]+)\s*=\s*([A-Za-z0-9_]+)", module_block[1:-1], re.MULTILINE)
        )
        name = name_match.group(1)
        if name in variants:
            raise ValueError(f"Duplicate source variant: {name}")
        variants[name] = Variant(name, type_match.group(1), modules)

    expected = {
        f"{role.variant_label} {tier.year} {profile}"
        for tier in TIERS
        for role in tier.roles
        for profile in PROFILES
    }
    missing = sorted(expected - variants.keys())
    if missing:
        raise ValueError(f"Missing source variants: {', '.join(missing)}")
    unexpected = sorted(variants.keys() - expected)
    if unexpected:
        raise ValueError(f"Unexpected source variants: {', '.join(unexpected)}")
    validate_catalog(variants)
    return variants


def capability(tier: Tier, role: Role, profile: str) -> str:
    return f"DAI_can_create_{tier.key}_{role.key}_{profile.lower()}_design"


def best_profile(tier: Tier, role: Role, profile: str) -> str:
    return f"DAI_best_{tier.key}_{role.key}_{profile.lower()}_design"


def possession(tier: Tier, role: Role, profile: str) -> str:
    return f"DAI_has_{tier.key}_{role.key}_{profile.lower()}_profile"


def native_profile(tier: Tier, role: Role, profile: str) -> str:
    return f"DAI_can_natively_build_{tier.key}_{role.key}_{profile.lower()}_design"


def native_any(tier: Tier, role: Role) -> str:
    return f"DAI_can_natively_build_{tier.key}_{role.key}_any_design"


def design_flag(tier: Tier, role: Role, profile: str) -> str:
    return f"DAI_{tier.key}_{role.key}_design_{profile.lower()}"


def receipt_flag(tier: Tier, role: Role, profile: str) -> str:
    return f"DAI_{tier.key}_{role.key}_profile_{profile.lower()}_licensed"


def mio_pending_flag(tier: Tier, role: Role, profile: str) -> str:
    return f"{design_flag(tier, role, profile)}_mio_pending"


def need_role(tier: Tier, role: Role) -> str:
    return f"DAI_needs_{tier.key}_{role.key}_design_from_root"


def better_provider(tier: Tier, role: Role, profile: str) -> str:
    return f"DAI_has_better_{tier.key}_{role.key}_{profile.lower()}_provider_for_prev"


def exact_variant(variants: dict[str, Variant], tier: Tier, role: Role, profile: str) -> Variant:
    return variants[f"{role.variant_label} {tier.year} {profile}"]


def expected_slots(tier: Tier, role: Role) -> tuple[str, ...]:
    weapon_count = WEAPON_SLOT_COUNT[tier.year]
    special_counts = (
        CARRIER_SPECIAL_SLOT_COUNT if role.key.startswith("carrier_") else SPECIAL_SLOT_COUNT
    )
    return (
        "fixed_main_weapon_slot",
        *(f"fixed_auxiliary_weapon_slot_{index}" for index in range(1, weapon_count)),
        "engine_type_slot",
        *(f"special_type_slot_{index}" for index in range(1, special_counts[tier.year] + 1)),
    )


def expected_equipment_type(tier: Tier, role: Role) -> str:
    suffix = {1936: 1, 1940: 2, 1944: 3}[tier.year]
    return f"{ROLE_TYPE_PREFIX[role.key]}_{suffix}"


def validate_catalog(variants: dict[str, Variant]) -> None:
    errors: list[str] = []
    for tier in TIERS:
        for role in tier.roles:
            slots = expected_slots(tier, role)
            for profile in PROFILES:
                variant = exact_variant(variants, tier, role, profile)
                if variant.equipment_type != expected_equipment_type(tier, role):
                    errors.append(
                        f"{variant.name}: type {variant.equipment_type}, expected "
                        f"{expected_equipment_type(tier, role)}"
                    )

                slot_names = [slot for slot, _ in variant.modules]
                duplicates = sorted({slot for slot in slot_names if slot_names.count(slot) > 1})
                missing = sorted(set(slots) - set(slot_names))
                extras = sorted(set(slot_names) - set(slots))
                if duplicates:
                    errors.append(f"{variant.name}: duplicate slots {', '.join(duplicates)}")
                if missing:
                    errors.append(
                        f"{variant.name}: missing explicit slots {', '.join(missing)} "
                        "(write unused slots as empty)"
                    )
                if extras:
                    errors.append(f"{variant.name}: unexpected slots {', '.join(extras)}")
                if slot_names != list(slots):
                    errors.append(f"{variant.name}: slots are not in canonical chassis order")

                modules = dict(variant.modules)
                engine = modules.get("engine_type_slot")
                if engine not in ENGINE_THRUST:
                    errors.append(f"{variant.name}: invalid or missing engine {engine}")
                    continue
                unknown_weights = sorted(
                    {module for module in modules.values() if module not in MODULE_WEIGHT}
                )
                if unknown_weights:
                    errors.append(
                        f"{variant.name}: no static weight for {', '.join(unknown_weights)}"
                    )
                    continue
                kind = "carrier" if role.key.startswith("carrier_") else "land"
                weight = AIRFRAME_WEIGHT[tier.year][kind] + sum(
                    MODULE_WEIGHT[module] for module in modules.values()
                )
                thrust = ENGINE_THRUST[engine]
                if weight > thrust:
                    errors.append(
                        f"{variant.name}: weight {weight:g} exceeds thrust {thrust:g}"
                    )

                try:
                    variant_techs(variant)
                except ValueError as error:
                    errors.append(str(error))

    registered_token_lines = [
        line.strip()
        for line in MIO_TOKEN_SOURCE.read_text(encoding="utf-8-sig").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    duplicate_registered_tokens = sorted(
        token
        for token in set(registered_token_lines)
        if registered_token_lines.count(token) > 1
    )
    if duplicate_registered_tokens:
        errors.append(
            "duplicate registered MIO tokens: "
            + ", ".join(duplicate_registered_tokens)
        )
    registered_tokens = set(registered_token_lines)
    helper_source = VARIANT_SOURCE.read_text(encoding="utf-8-sig")
    referenced_tokens = set(re.findall(r"\btoken:([A-Za-z0-9_]+)", helper_source))
    expected_mio_tags = {"GER", "ENG", "USA", "SOV", "FRA", "ITA", "JAP"}

    for role in SMALL_ROLES:
        helper_match = re.search(
            rf"(?m)^{re.escape(role.mio_helper)}\s*=\s*\{{", helper_source
        )
        if not helper_match:
            errors.append(f"missing MIO helper {role.mio_helper}")
            continue
        helper_brace = helper_source.find("{", helper_match.start())
        helper_block, _ = extract_braced(helper_source, helper_brace)
        helper_tokens = set(re.findall(r"\btoken:([A-Za-z0-9_]+)", helper_block))
        mapped_tags = re.findall(r"\boriginal_tag\s*=\s*([A-Z]{3})\b", helper_block)
        if set(mapped_tags) != expected_mio_tags or len(mapped_tags) != len(expected_mio_tags):
            errors.append(
                f"{role.mio_helper}: expected one primary mapping for each of "
                "GER, ENG, USA, SOV, FRA, ITA, and JAP"
            )
        incompatible = sorted(helper_tokens - ROLE_MIO_COMPATIBLE_TOKENS[role.key])
        if incompatible:
            errors.append(
                f"{role.mio_helper}: role-incompatible MIO tokens "
                + ", ".join(incompatible)
            )
        if "DAI_air_design_team_alternate" not in helper_block:
            errors.append(f"{role.mio_helper}: missing alternate MIO mapping variable")

    missing_tokens = sorted(referenced_tokens - registered_tokens)
    if missing_tokens:
        errors.append(f"unregistered MIO tokens: {', '.join(missing_tokens)}")

    organization_source = "\n".join(
        path.read_text(encoding="utf-8-sig")
        for path in sorted(MIO_ORGANIZATION_ROOT.glob("*.txt"))
    )
    defined_organizations = set(
        re.findall(r"(?m)^([A-Za-z0-9_]+)\s*=\s*\{", organization_source)
    )
    missing_organizations = sorted(referenced_tokens - defined_organizations)
    if missing_organizations:
        errors.append(
            "MIO tokens without loaded organization definitions: "
            + ", ".join(missing_organizations)
        )

    technology_source = "\n".join(
        path.read_text(encoding="utf-8-sig")
        for path in sorted(TECHNOLOGY_ROOT.glob("*.txt"))
    )
    defined_technologies = set(
        re.findall(r"(?m)^\s*([A-Za-z0-9_]+)\s*=\s*\{", technology_source)
    )
    required_technologies = set(MODULE_TECH.values()) | {
        tier.frame_tech for tier in TIERS
    }
    missing_technologies = sorted(required_technologies - defined_technologies)
    if missing_technologies:
        errors.append(
            "module/frame technology ids without loaded definitions: "
            + ", ".join(missing_technologies)
        )

    for module in FIGHTER_ANY_WEAPONS:
        if module not in MODULE_TECH:
            errors.append(f"ANY fighter module {module} has no technology mapping")
        if module not in MODULE_WEIGHT:
            errors.append(f"ANY fighter module {module} has no static weight")

    tier_by_key = {tier.key: tier for tier in TIERS}
    for (tier_key, role_key, slot), modules in ANY_SLOT_OVERRIDES.items():
        tier = tier_by_key.get(tier_key)
        if tier is None:
            errors.append(f"ANY slot override has unknown tier {tier_key}")
            continue
        role = next((item for item in tier.roles if item.key == role_key), None)
        if role is None:
            errors.append(
                f"ANY slot override has unknown role {role_key} for tier {tier_key}"
            )
            continue
        if slot not in expected_slots(tier, role):
            errors.append(
                f"ANY slot override has invalid slot {slot} for {tier_key}/{role_key}"
            )
        for module in modules:
            if module not in MODULE_TECH:
                errors.append(f"ANY slot override module {module} has no technology mapping")
            if module not in MODULE_WEIGHT:
                errors.append(f"ANY slot override module {module} has no static weight")

    if errors:
        raise ValueError("Catalog validation failed:\n- " + "\n- ".join(errors))


def variant_techs(variant: Variant) -> tuple[str, ...]:
    technologies: list[str] = []
    unknown: set[str] = set()
    for _, module in variant.modules:
        if module == "empty":
            continue
        technology = MODULE_TECH.get(module)
        if technology is None:
            unknown.add(module)
        elif technology not in technologies:
            technologies.append(technology)
    if unknown:
        raise ValueError(f"No technology mapping for {variant.name}: {', '.join(sorted(unknown))}")
    return tuple(technologies)


def licensed_module_access(tier: Tier, technology: str) -> tuple[str, str, str] | None:
    return LICENSED_MODULE_ACCESS.get((tier.key, technology))


def licensed_receipt_flags_for_technology(
    variants: dict[str, Variant], tier: Tier, technology: str
) -> list[str]:
    flags: list[str] = []
    profiles: set[str] = set()
    for role in tier.roles:
        for profile in PROFILES:
            variant = exact_variant(variants, tier, role, profile)
            if technology not in variant_techs(variant):
                continue
            profiles.add(profile)
            flags.append(receipt_flag(tier, role, profile))

    # Preserve access for saves written by the aggregate pre-role system.
    if "C" in profiles:
        flags.append(f"DAI_{tier.key}_profile_full_licensed")
    if "B" in profiles:
        flags.append(f"DAI_{tier.key}_profile_engine_licensed")
    if "A" in profiles:
        flags.extend(
            [
                f"DAI_{tier.key}_profile_base_licensed",
                f"DAI_{tier.key}_profile_weapon_licensed",
            ]
        )
    return list(dict.fromkeys(flags))


def render_or(items: list[str], indent: str = "\t") -> list[str]:
    lines = [f"{indent}OR = {{"]
    lines.extend(f"{indent}\t{item}" for item in items)
    lines.append(f"{indent}}}")
    return lines


def generate_triggers(variants: dict[str, Variant]) -> str:
    lines = [
        "# Generated by tools/generate_plane_role_licensing.py.",
        "# Native AI-target checks use real technologies only. Scripted licensing",
        "# capability checks remain separate and may use licensed profile access.",
        "",
    ]

    for tier in TIERS:
        for (tier_key, technology), (access_flag, access_trigger, usable_trigger) in LICENSED_MODULE_ACCESS.items():
            if tier.key != tier_key:
                continue
            receipt_flags = licensed_receipt_flags_for_technology(variants, tier, technology)
            lines.append(f"{access_trigger} = {{")
            lines.extend(
                render_or(
                    [f"has_country_flag = {access_flag}"]
                    + [f"has_country_flag = {flag}" for flag in receipt_flags]
                )
            )
            lines.extend(["}", ""])
            lines.append(f"{usable_trigger} = {{")
            lines.append("\tOR = {")
            lines.append(f"\t\thas_tech = {technology}")
            lines.append(f"\t\t{access_trigger} = yes")
            lines.extend(["\t}", "}", ""])

    for tier in TIERS:
        for role in tier.roles:
            for profile in PROFILES:
                variant = exact_variant(variants, tier, role, profile)
                lines.append(f"{native_profile(tier, role, profile)} = {{")
                lines.append(f"\thas_tech = {tier.frame_tech}")
                lines.extend(f"\thas_tech = {technology}" for technology in variant_techs(variant))
                lines.extend(["}", ""])

            lines.append(f"{native_any(tier, role)} = {{")
            lines.extend(
                render_or(
                    [f"{native_profile(tier, role, profile)} = yes" for profile in PROFILES]
                )
            )
            lines.extend(["}", ""])

            for profile in PROFILES:
                variant = exact_variant(variants, tier, role, profile)
                lines.append(f"{capability(tier, role, profile)} = {{")
                lines.append(f"\tDAI_can_share_{tier.key}_license = yes")
                for technology in variant_techs(variant):
                    access = licensed_module_access(tier, technology)
                    if access is None:
                        lines.append(f"\thas_tech = {technology}")
                    else:
                        lines.append(f"\t{access[2]} = yes")
                lines.extend(["}", ""])

            ordered = list(PROFILES)
            for index, profile in enumerate(ordered):
                lines.append(f"{best_profile(tier, role, profile)} = {{")
                lines.append(f"\t{capability(tier, role, profile)} = yes")
                if index:
                    stronger = [f"{capability(tier, role, item)} = yes" for item in ordered[:index]]
                    lines.append("\tNOT = {")
                    lines.extend(render_or(stronger, "\t\t"))
                    lines.append("\t}")
                lines.extend(["}", ""])

            for profile in ordered:
                lines.append(f"{possession(tier, role, profile)} = {{")
                lines.append(f"\thas_country_flag = {design_flag(tier, role, profile)}")
                lines.extend(["}", ""])

            for index, profile in enumerate(ordered[1:], start=1):
                lines.append(f"{better_provider(tier, role, profile)} = {{")
                lines.append("\tany_other_country = {")
                lines.append("\t\tDAI_is_air_license_provider_for_prev = yes")
                stronger = [f"{capability(tier, role, item)} = yes" for item in ordered[:index]]
                lines.extend(render_or(stronger, "\t\t"))
                lines.extend(["\t}", "}", ""])

            lines.append(f"{need_role(tier, role)} = {{")
            lines.append("\tOR = {")
            for index, profile in enumerate(ordered):
                lines.append("\t\tAND = {")
                lines.append(f"\t\t\tROOT = {{ {best_profile(tier, role, profile)} = yes }}")
                if index:
                    lines.append(f"\t\t\tNOT = {{ {better_provider(tier, role, profile)} = yes }}")
                possessed = [f"{possession(tier, role, item)} = yes" for item in ordered[: index + 1]]
                lines.append("\t\t\tNOT = {")
                lines.extend(render_or(possessed, "\t\t\t\t"))
                lines.append("\t\t\t}")
                lines.append("\t\t}")
            lines.extend(["\t}", "}", ""])

        all_capabilities = [
            f"{capability(tier, role, profile)} = yes"
            for role in tier.roles
            for profile in PROFILES
        ]
        lines.append(f"DAI_can_share_{tier.key}_role_design = {{")
        lines.extend(render_or(all_capabilities))
        lines.extend(["}", ""])

        lines.append(f"DAI_needs_{tier.key}_local_role_design = {{")
        lines.append("\tOR = {")
        for role in tier.roles:
            for index, profile in enumerate(PROFILES):
                lines.append("\t\tAND = {")
                lines.append(f"\t\t\t{best_profile(tier, role, profile)} = yes")
                possessed = [
                    f"{possession(tier, role, item)} = yes" for item in PROFILES[: index + 1]
                ]
                lines.append("\t\t\tNOT = {")
                lines.extend(render_or(possessed, "\t\t\t\t"))
                lines.append("\t\t\t}")
                lines.append("\t\t}")
        lines.extend(["\t}", "}", ""])

        lines.append(f"DAI_needs_{tier.key}_role_design_from_root = {{")
        lines.extend(render_or([f"{need_role(tier, role)} = yes" for role in tier.roles]))
        lines.extend(["}", ""])

        lines.append(f"DAI_has_deliverable_{tier.key}_role_design_from_root = {{")
        lines.append("\tOR = {")
        for role in tier.roles:
            lines.append("\t\tAND = {")
            lines.append(f"\t\t\t{need_role(tier, role)} = yes")
            lines.append("\t\t\tROOT = {")
            lines.append("\t\t\t\tOR = {")
            for profile in PROFILES:
                lines.extend(
                    [
                        "\t\t\t\t\tAND = {",
                        f"\t\t\t\t\t\t{best_profile(tier, role, profile)} = yes",
                        f"\t\t\t\t\t\thas_country_flag = {design_flag(tier, role, profile)}",
                        "\t\t\t\t\t}",
                    ]
                )
            lines.extend(["\t\t\t\t}", "\t\t\t}", "\t\t}"])
        lines.extend(["\t}", "}", ""])

    return "\n".join(lines)


def render_variant_block(variant: Variant, indent: str, with_mio: bool) -> list[str]:
    lines = [
        f'{indent}name = "{variant.name}"',
        f"{indent}type = {variant.equipment_type}",
        f"{indent}parent_version = 0",
        f"{indent}allow_without_tech = yes",
    ]
    if with_mio:
        lines.append(f"{indent}design_team = mio:[x]")
    lines.append(f"{indent}modules = {{")
    lines.extend(f"{indent}\t{slot} = {module}" for slot, module in variant.modules)
    lines.append(f"{indent}}}")
    return lines


def target_value(tier: Tier, target: str) -> int:
    return TIER_TARGET_BASE[tier.key] + TARGET_OFFSETS[target]


def ordered_unique(items: list[str] | tuple[str, ...]) -> list[str]:
    return list(dict.fromkeys(items))


def any_slot_modules(
    variants: dict[str, Variant], tier: Tier, role: Role, slot: str
) -> list[str]:
    override = ANY_SLOT_OVERRIDES.get((tier.key, role.key, slot))
    if override is not None:
        return list(override)

    alternatives: list[str] = []
    for profile in PROFILES:
        alternatives.append(dict(exact_variant(variants, tier, role, profile).modules)[slot])
    alternatives = ordered_unique(alternatives)
    if (
        role.key in {"fighter", "carrier_fighter"}
        and slot.startswith("fixed_")
        and any(module != "empty" for module in alternatives)
    ):
        nonempty = [module for module in alternatives if module != "empty"]
        alternatives = ordered_unique(nonempty + list(FIGHTER_ANY_WEAPONS))
        if any(
            dict(exact_variant(variants, tier, role, profile).modules)[slot] == "empty"
            for profile in PROFILES
        ):
            alternatives.append("empty")
    return alternatives


def render_target_slot(slot: str, alternatives: list[str], indent: str) -> list[str]:
    if len(alternatives) == 1:
        return [f"{indent}{slot} = {alternatives[0]}"]
    lines = [f"{indent}{slot} = {{"]
    if "empty" in alternatives:
        lines.extend(f"{indent}\tmodule = {module}" for module in alternatives)
    else:
        lines.append(f"{indent}\tany_of = {{")
        lines.extend(f"{indent}\t\t{module}" for module in alternatives)
        lines.append(f"{indent}\t}}")
    lines.append(f"{indent}}}")
    return lines


def target_allowed_modules(
    variants: dict[str, Variant], tier: Tier, role: Role, target: str
) -> list[str]:
    if target in PROFILES:
        modules = [module for _, module in exact_variant(variants, tier, role, target).modules]
    else:
        modules = []
        for slot in expected_slots(tier, role):
            modules.extend(any_slot_modules(variants, tier, role, slot))
    return ordered_unique([module for module in modules if module != "empty"])


def render_ai_target(
    variants: dict[str, Variant], tier: Tier, role: Role, target: str
) -> list[str]:
    value = target_value(tier, target)
    target_key = f"DAI_{tier.year}_{role.key}_{target.lower()}"
    lines = [f"\t{target_key.upper()} = {{", "\t\tpriority = {", "\t\t\tbase = 0", "\t\t\tmodifier = {"]
    lines.append(f"\t\t\t\tadd = {value}")
    if target == "ANY":
        lines.append(f"\t\t\t\t{native_any(tier, role)} = yes")
    elif target == "C":
        lines.extend(
            [
                "\t\t\t\tOR = {",
                f"\t\t\t\t\thas_country_flag = {design_flag(tier, role, 'C')}",
                f"\t\t\t\t\t{native_profile(tier, role, 'C')} = yes",
                "\t\t\t\t}",
            ]
        )
    else:
        lines.append(f"\t\t\t\thas_country_flag = {design_flag(tier, role, target)}")
    lines.extend(["\t\t\t}", "\t\t}", "", "\t\ttarget_variant = {"])
    lines.append(f"\t\t\ttype = {expected_equipment_type(tier, role)}")
    lines.append(f"\t\t\tmatch_value = {value}")
    lines.extend(["", "\t\t\tmodules = {"])
    if target == "ANY":
        for slot in expected_slots(tier, role):
            lines.extend(render_target_slot(slot, any_slot_modules(variants, tier, role, slot), "\t\t\t\t"))
    else:
        variant = exact_variant(variants, tier, role, target)
        lines.extend(f"\t\t\t\t{slot} = {module}" for slot, module in variant.modules)
    lines.extend(["\t\t\t}", "\t\t}", "", "\t\tallowed_modules = {"])
    lines.extend(
        f"\t\t\t{module}" for module in target_allowed_modules(variants, tier, role, target)
    )
    lines.extend(["\t\t}", "\t}", ""])
    return lines


def generate_role_ai_targets(variants: dict[str, Variant], role: Role) -> str:
    lines = [
        "\t# Generated from the 45-profile DAI small-aircraft catalog.",
        "\t# Hierarchy within each tier: exact C > native ANY > owned B > owned A.",
        "",
    ]
    for tier in TIERS:
        lines.extend([f"\t##################", f"\t### {tier.year}", f"\t##################", ""])
        for target in TARGET_ORDER:
            lines.extend(render_ai_target(variants, tier, role, target))
    return "\n".join(lines).rstrip()


def generate_ai_equipment(variants: dict[str, Variant]) -> str:
    source = AI_EQUIPMENT_OUTPUT.read_text(encoding="utf-8-sig")
    for role in SMALL_ROLES:
        begin = f"\t# DAI_GENERATED_SMALL_AIR_TARGETS_BEGIN {role.key}"
        end = f"\t# DAI_GENERATED_SMALL_AIR_TARGETS_END {role.key}"
        if source.count(begin) != 1 or source.count(end) != 1:
            raise ValueError(f"Expected one generated target marker pair for {role.key}")
        start = source.index(begin) + len(begin)
        finish = source.index(end, start)
        generated = "\n" + generate_role_ai_targets(variants, role) + "\n"
        source = source[:start] + generated + source[finish:]
    return source.rstrip() + "\n"


def build_effect_name(tier: Tier, role: Role, profile: str) -> str:
    return f"DAI_build_{tier.key}_{role.key}_{profile.lower()}_design"


def provider_create_effect_name(tier: Tier, role: Role, profile: str) -> str:
    return f"DAI_create_{tier.key}_{role.key}_{profile.lower()}_design"


def render_mio_attempt(
    variant: Variant, team_variable: str, selection: int
) -> list[str]:
    return [
        "\tif = {",
        "\t\tlimit = {",
        "\t\t\tcheck_variable = { DAI_air_design_created = 0 }",
        '\t\t\thas_dlc = "Arms Against Tyranny"',
        f"\t\t\tNOT = {{ check_variable = {{ {team_variable} = 0 }} }}",
        "\t\t}",
        "\t\tmeta_effect = {",
        "\t\t\ttext = {",
        "\t\t\t\tif = {",
        "\t\t\t\t\tlimit = {",
        "\t\t\t\t\t\tmio:[x] = { is_mio_available = yes }",
        "\t\t\t\t\t}",
        "\t\t\t\t\tcreate_equipment_variant = {",
        *render_variant_block(variant, "\t\t\t\t\t\t", True),
        "\t\t\t\t\t}",
        "\t\t\t\t\tset_temp_variable = { DAI_air_design_team_added = 1 }",
        "\t\t\t\t\tset_temp_variable = { DAI_air_design_created = 1 }",
        f"\t\t\t\t\tset_temp_variable = {{ DAI_air_design_team_selection = {selection} }}",
        "\t\t\t\t}",
        "\t\t\t}",
        f'\t\t\tx = "[?{team_variable}.GetTokenKey]"',
        "\t\t}",
        "\t}",
    ]


def render_build_effect(tier: Tier, role: Role, profile: str, variant: Variant) -> list[str]:
    pending = mio_pending_flag(tier, role, profile)
    lines = [
        f"{build_effect_name(tier, role, profile)} = {{",
        f"\t{role.mio_helper} = yes",
        "\tset_temp_variable = { DAI_air_design_created = 0 }",
        "\tset_temp_variable = { DAI_air_design_team_added = 0 }",
        "\tset_temp_variable = { DAI_air_design_team_selection = 0 }",
    ]
    lines.extend(render_mio_attempt(variant, "DAI_air_design_team", 1))
    lines.extend(render_mio_attempt(variant, "DAI_air_design_team_alternate", 2))
    lines.extend(
        [
            "\tif = {",
            "\t\tlimit = {",
            "\t\t\tcheck_variable = { DAI_air_design_created = 0 }",
            "\t\t\tOR = {",
            "\t\t\t\tcheck_variable = { DAI_air_design_team = 0 }",
            '\t\t\t\tNOT = { has_dlc = "Arms Against Tyranny" }',
            "\t\t\t}",
            "\t\t}",
            "\t\tcreate_equipment_variant = {",
        ]
    )
    lines.extend(render_variant_block(variant, "\t\t\t", False))
    lines.extend(
        [
            "\t\t}",
            "\t\tset_temp_variable = { DAI_air_design_created = 1 }",
            "\t\tif = {",
            "\t\t\tlimit = { check_variable = { DAI_air_design_team = 0 } }",
            f'\t\t\tlog = "[GetYear] [GetMonth] | DAI_PLANE_MIO_FALLBACK | owner=[THIS.GetName] tier={tier.log_key} role={role.key} profile={profile} variant={variant.name} reason=unmapped_country"',
            "\t\t}",
            "\t\telse = {",
            f'\t\t\tlog = "[GetYear] [GetMonth] | DAI_PLANE_MIO_FALLBACK | owner=[THIS.GetName] tier={tier.log_key} role={role.key} profile={profile} variant={variant.name} reason=aat_not_active"',
            "\t\t}",
            "\t}",
            "\tif = {",
            "\t\tlimit = { check_variable = { DAI_air_design_created = 1 } }",
            "\t\tif = {",
            "\t\t\tlimit = { check_variable = { DAI_air_design_team_added = 1 } }",
            "\t\t\tif = {",
            f"\t\t\t\tlimit = {{ has_country_flag = {pending} }}",
            "\t\t\t\tif = {",
            "\t\t\t\t\tlimit = { check_variable = { DAI_air_design_team_selection = 2 } }",
            f'\t\t\t\t\tlog = "[GetYear] [GetMonth] | DAI_PLANE_MIO_RETRY | owner=[THIS.GetName] tier={tier.log_key} role={role.key} profile={profile} variant={variant.name} result=created_with_mio mapping=alternate mio=[?DAI_air_design_team_alternate.GetTokenKey]"',
            "\t\t\t\t}",
            "\t\t\t\telse = {",
            f'\t\t\t\t\tlog = "[GetYear] [GetMonth] | DAI_PLANE_MIO_RETRY | owner=[THIS.GetName] tier={tier.log_key} role={role.key} profile={profile} variant={variant.name} result=created_with_mio mapping=primary mio=[?DAI_air_design_team.GetTokenKey]"',
            "\t\t\t\t}",
            "\t\t\t}",
            "\t\t\tif = {",
            "\t\t\t\tlimit = { check_variable = { DAI_air_design_team_selection = 2 } }",
            f'\t\t\t\tlog = "[GetYear] [GetMonth] | DAI_PLANE_MIO_ASSIGNMENT | owner=[THIS.GetName] tier={tier.log_key} role={role.key} profile={profile} variant={variant.name} status=assigned mapping=alternate mio=[?DAI_air_design_team_alternate.GetTokenKey]"',
            "\t\t\t}",
            "\t\t\telse = {",
            f'\t\t\t\tlog = "[GetYear] [GetMonth] | DAI_PLANE_MIO_ASSIGNMENT | owner=[THIS.GetName] tier={tier.log_key} role={role.key} profile={profile} variant={variant.name} status=assigned mapping=primary mio=[?DAI_air_design_team.GetTokenKey]"',
            "\t\t\t}",
            "\t\t}",
            f"\t\tclr_country_flag = {pending}",
            "\t}",
            "\telse = {",
            "\t\tif = {",
            f"\t\t\tlimit = {{ NOT = {{ has_country_flag = {pending} }} }}",
            f"\t\t\tset_country_flag = {pending}",
            "\t\t\tif = {",
            "\t\t\t\tlimit = { check_variable = { DAI_air_design_team_alternate = 0 } }",
            f'\t\t\t\tlog = "[GetYear] [GetMonth] | DAI_PLANE_MIO_PENDING | owner=[THIS.GetName] tier={tier.log_key} role={role.key} profile={profile} variant={variant.name} action=defer_and_retry reason=primary_unavailable primary=[?DAI_air_design_team.GetTokenKey] alternate=unmapped no_mio_variant_created=no"',
            "\t\t\t}",
            "\t\t\telse = {",
            f'\t\t\t\tlog = "[GetYear] [GetMonth] | DAI_PLANE_MIO_PENDING | owner=[THIS.GetName] tier={tier.log_key} role={role.key} profile={profile} variant={variant.name} action=defer_and_retry reason=primary_and_alternate_unavailable primary=[?DAI_air_design_team.GetTokenKey] alternate=[?DAI_air_design_team_alternate.GetTokenKey] no_mio_variant_created=no"',
            "\t\t\t}",
            "\t\t}",
            "\t}",
            "}",
            "",
        ]
    )
    return lines


def render_provider_create_effect(tier: Tier, role: Role, profile: str, variant: Variant) -> list[str]:
    lines = [
        f"{provider_create_effect_name(tier, role, profile)} = {{",
        f"\t{build_effect_name(tier, role, profile)} = yes",
        "\tif = {",
        "\t\tlimit = { check_variable = { DAI_air_design_created = 1 } }",
    ]
    weaker = PROFILES[PROFILES.index(profile) + 1 :]
    if weaker:
        lines.extend(["\t\tif = {", "\t\t\tlimit = {", "\t\t\t\tOR = {"])
        lines.extend(
            f"\t\t\t\t\thas_country_flag = {design_flag(tier, role, weaker_profile)}"
            for weaker_profile in weaker
        )
        lines.extend(
            [
                "\t\t\t\t}",
                "\t\t\t}",
                f'\t\t\tlog = "[GetYear] [GetMonth] | DAI_PLANE_PROFILE_UPGRADE | owner=[THIS.GetName] source_provider=[THIS.GetName] tier={tier.log_key} role={role.key} new_profile={profile} prior_profile=weaker_exact_owned"',
                "\t\t}",
            ]
        )
    lines.extend(
        [
            f"\t\tset_country_flag = {design_flag(tier, role, profile)}",
            "\t\tif = {",
            f"\t\t\tlimit = {{ has_tech = {tier.frame_tech} }}",
            f'\t\t\tlog = "[GetYear] [GetMonth] | DAI_PLANE_DESIGN_CREATE | owner=[THIS.GetName] source_provider=[THIS.GetName] tier={tier.log_key} role={role.key} profile={profile} variant={variant.name} source=real_tech"',
            "\t\t}",
            "\t\telse = {",
            f'\t\t\tlog = "[GetYear] [GetMonth] | DAI_PLANE_DESIGN_CREATE | owner=[THIS.GetName] source_provider=[THIS.GetName] tier={tier.log_key} role={role.key} profile={profile} variant={variant.name} source=licensed_frame"',
            f'\t\t\tlog = "[GetYear] [GetMonth] | DAI_PLANE_REEXPORT_CREATE | provider=[THIS.GetName] tier={tier.log_key} role={role.key} profile={profile} variant={variant.name}"',
            "\t\t}",
        ]
    )
    if profile == "B":
        lines.append(
            f'\t\tlog = "[GetYear] [GetMonth] | DAI_PLANE_PROFILE_FALLBACK | provider=[THIS.GetName] tier={tier.log_key} role={role.key} profile=B missing_profile=C"'
        )
    elif profile == "A":
        lines.append(
            f'\t\tlog = "[GetYear] [GetMonth] | DAI_PLANE_PROFILE_FALLBACK | provider=[THIS.GetName] tier={tier.log_key} role={role.key} profile=A missing_profiles=C,B"'
        )
    lines.extend(["\t}", "}", ""])
    return lines


def generate_creation_effects(variants: dict[str, Variant]) -> str:
    lines = [
        "# Generated by tools/generate_plane_role_licensing.py.",
        "# Small-airframe variants are created independently by role and strongest constructible profile.",
        "",
    ]
    for tier in TIERS:
        for (tier_key, technology), (access_flag, access_trigger, _) in LICENSED_MODULE_ACCESS.items():
            if tier.key != tier_key:
                continue
            lines.extend(
                [
                    f"DAI_update_{tier.key}_{technology}_profile_access = {{",
                    "\tif = {",
                    "\t\tlimit = {",
                    f"\t\t\tNOT = {{ has_country_flag = {access_flag} }}",
                    f"\t\t\t{access_trigger} = yes",
                    "\t\t}",
                    f"\t\tset_country_flag = {access_flag}",
                    f'\t\tlog = "[GetYear] [GetMonth] | DAI_PLANE_MODULE_ACCESS | country=[THIS.GetName] tier={tier.log_key} technology={technology} module_profile={technology.replace("engines_", "engine_")}_1x source=existing_licensed_profile action=backfill"',
                    "\t}",
                    "}",
                    "",
                ]
            )
    for tier in TIERS:
        for role in tier.roles:
            for profile in PROFILES:
                variant = exact_variant(variants, tier, role, profile)
                lines.extend(render_build_effect(tier, role, profile, variant))
                lines.extend(render_provider_create_effect(tier, role, profile, variant))

        lines.append(f"DAI_create_{tier.key}_role_designs = {{")
        for role in tier.roles:
            role_lines: list[str] = []
            for index, profile in enumerate(PROFILES):
                keyword = "if" if index == 0 else "else_if"
                role_lines.extend([f"\t{keyword} = {{", "\t\tlimit = {"])
                role_lines.append(f"\t\t\t{best_profile(tier, role, profile)} = yes")
                role_lines.append("\t\t\tNOT = {")
                role_lines.extend(
                    render_or(
                        [f"{possession(tier, role, item)} = yes" for item in PROFILES[: index + 1]],
                        "\t\t\t\t",
                    )
                )
                role_lines.extend(
                    [
                        "\t\t\t}",
                        "\t\t}",
                        f"\t\t{provider_create_effect_name(tier, role, profile)} = yes",
                        "\t}",
                    ]
                )
            lines.extend(role_lines)
        lines.extend(["}", ""])
    return "\n".join(lines)


def receive_effect_name(tier: Tier, role: Role, profile: str) -> str:
    return f"DAI_receive_{tier.key}_{role.key}_{profile.lower()}_design_from_root"


def render_receive_effect(tier: Tier, role: Role, profile: str, variant: Variant) -> list[str]:
    lines = [
        f"{receive_effect_name(tier, role, profile)} = {{",
        f"\t{build_effect_name(tier, role, profile)} = yes",
        "\tif = {",
        "\t\tlimit = { check_variable = { DAI_air_design_created = 1 } }",
    ]
    weaker = PROFILES[PROFILES.index(profile) + 1 :]
    if weaker:
        lines.extend(["\t\tif = {", "\t\t\tlimit = {", "\t\t\t\tOR = {"])
        lines.extend(
            f"\t\t\t\t\thas_country_flag = {design_flag(tier, role, weaker_profile)}"
            for weaker_profile in weaker
        )
        lines.extend(
            [
                "\t\t\t\t}",
                "\t\t\t}",
                f'\t\t\tlog = "[GetYear] [GetMonth] | DAI_PLANE_PROFILE_UPGRADE | owner=[THIS.GetName] source_provider=[ROOT.GetName] tier={tier.log_key} role={role.key} new_profile={profile} prior_profile=weaker_exact_owned"',
                "\t\t}",
            ]
        )
    lines.extend(
        [
            f"\t\tset_country_flag = {design_flag(tier, role, profile)}",
            f"\t\tset_country_flag = {receipt_flag(tier, role, profile)}",
            f"\t\tset_country_flag = {receipt_flag(tier, role, profile)}_from_@ROOT",
            f'\t\tlog = "[GetYear] [GetMonth] | DAI_PLANE_DESIGN_CREATE | owner=[THIS.GetName] source_provider=[ROOT.GetName] tier={tier.log_key} role={role.key} profile={profile} variant={variant.name} source=licensed_delivery ownership=recipient_local diplomatic_license=chassis_only"',
        ]
    )
    for technology in variant_techs(variant):
        access = licensed_module_access(tier, technology)
        if access is None:
            continue
        access_flag, _, _ = access
        lines.extend(
            [
                "\t\tif = {",
                f"\t\t\tlimit = {{ NOT = {{ has_country_flag = {access_flag} }} }}",
                f"\t\t\tset_country_flag = {access_flag}",
                f'\t\t\tlog = "[GetYear] [GetMonth] | DAI_PLANE_MODULE_ACCESS | country=[THIS.GetName] provider=[ROOT.GetName] tier={tier.log_key} role={role.key} profile={profile} technology={technology} module_profile={technology.replace("engines_", "engine_")}_1x source=licensed_delivery"',
                "\t\t}",
            ]
        )
    lines.extend(
        [
            "\t\tif = {",
            f"\t\t\tlimit = {{ NOT = {{ has_country_flag = DAI_{tier.key}_licensed }} }}",
            f"\t\t\tset_country_flag = DAI_{tier.key}_licensed",
            f'\t\t\tlog = "[GetYear] [GetMonth] | DAI_PLANE_FRAME_ACCESS | recipient=[THIS.GetName] provider=[ROOT.GetName] tier={tier.log_key} role={role.key} profile={profile}"',
            "\t\t}",
            "\t}",
            "}",
            "",
        ]
    )
    return lines


def chassis_effect_name(tier: Tier) -> str:
    return f"DAI_ensure_{tier.key}_chassis_license_from_root"


def render_chassis_effect(tier: Tier) -> list[str]:
    return [
        f"{chassis_effect_name(tier)} = {{",
        "\tif = {",
        f"\t\tlimit = {{ NOT = {{ has_country_flag = DAI_{tier.key}_frame_license_from_@ROOT }} }}",
        "\t\tDAI_set_license_relation_recipient_to_provider = yes",
        f'\t\tlog = "[GetYear] [GetMonth] | DAI_PLANE_CHASSIS_LICENSE_ATTEMPT | provider=[ROOT.GetName] recipient=[THIS.GetName] tier={tier.log_key} equipment={tier.chassis_type} license_scope=chassis_only recipient_design_mode=local_copy provider_design_gate=passed"',
        "\t\tROOT = {",
        "\t\t\tcreate_production_license = {",
        "\t\t\t\ttarget = PREV",
        "\t\t\t\tcost_factor = 0",
        "\t\t\t\tnew_prioritised = no",
        f"\t\t\t\tequipment = {{ type = {tier.chassis_type} }}",
        "\t\t\t}",
        "\t\t}",
        f"\t\tset_country_flag = DAI_{tier.key}_frame_license_from_@ROOT",
        "\t}",
        "}",
        "",
    ]


def generate_delivery_effects(variants: dict[str, Variant]) -> str:
    lines = [
        "# Generated by tools/generate_plane_role_licensing.py.",
        "# Called from recipient scope with ROOT as provider. One type-only chassis license",
        "# supports independently generated recipient-local role designs.",
        "",
    ]
    for tier in TIERS:
        lines.extend(render_chassis_effect(tier))
        for role in tier.roles:
            for profile in PROFILES:
                lines.extend(render_receive_effect(tier, role, profile, exact_variant(variants, tier, role, profile)))

        lines.append(f"DAI_deliver_{tier.key}_licenses_from_root = {{")
        lines.append("\tif = {")
        lines.append(f"\t\tlimit = {{ DAI_has_deliverable_{tier.key}_role_design_from_root = yes }}")
        lines.append(f"\t\t{chassis_effect_name(tier)} = yes")
        for role in tier.roles:
            lines.extend(["\t\tif = {", f"\t\t\tlimit = {{ {need_role(tier, role)} = yes }}"])
            for index, profile in enumerate(PROFILES):
                keyword = "if" if index == 0 else "else_if"
                lines.extend(
                    [
                        f"\t\t\t{keyword} = {{",
                        "\t\t\t\tlimit = {",
                        "\t\t\t\t\tROOT = {",
                        f"\t\t\t\t\t\t{best_profile(tier, role, profile)} = yes",
                        f"\t\t\t\t\t\thas_country_flag = {design_flag(tier, role, profile)}",
                        "\t\t\t\t\t}",
                        "\t\t\t\t}",
                        f"\t\t\t\t{receive_effect_name(tier, role, profile)} = yes",
                        "\t\t\t}",
                    ]
                )
            lines.append("\t\t}")
        lines.extend(["\t}", "}", ""])
    return "\n".join(lines)


def target_transition_effect_name(tier: Tier, role: Role) -> str:
    return f"DAI_log_{tier.key}_{role.key}_target_transition"


def target_state_flag(tier: Tier, role: Role, state: str) -> str:
    return f"DAI_{tier.key}_{role.key}_target_state_{state}"


TARGET_STATES = ("c_exact", "c_native", "any", "b", "a", "none", "no_carrier")


def render_missing_c_requirements(tier: Tier, role: Role, variant: Variant) -> list[str]:
    requirements = [("frame", tier.frame_tech, "chassis")]
    seen_technologies: set[str] = set()
    for _, module in variant.modules:
        if module == "empty":
            continue
        technology = MODULE_TECH[module]
        if technology in seen_technologies:
            continue
        seen_technologies.add(technology)
        requirements.append(("module_tech", technology, module))
    lines: list[str] = []
    for kind, technology, module in requirements:
        lines.extend(
            [
                "\t\t\tif = {",
                f"\t\t\t\tlimit = {{ NOT = {{ has_tech = {technology} }} }}",
                f'\t\t\t\tlog = "[GetYear] [GetMonth] | DAI_PLANE_TARGET_MISSING | country=[THIS.GetName] tier={tier.log_key} role={role.key} target=C_ULTIMATE requirement={kind} technology={technology} module_profile={module} activation_path=native_full_real_tech"',
                "\t\t\t}",
            ]
        )
    return lines


def any_options_log(variants: dict[str, Variant], tier: Tier, role: Role) -> str:
    slots = []
    for slot in expected_slots(tier, role):
        alternatives = ",".join(any_slot_modules(variants, tier, role, slot))
        slots.append(f"{slot}:{alternatives}")
    return (
        f'log = "[GetYear] [GetMonth] | DAI_PLANE_TARGET_ANY_OPTIONS | '
        f'country=[THIS.GetName] tier={tier.log_key} role={role.key} '
        f'accepted_slots={";".join(slots)} prebuilt_match_possible=yes '
        'exact_loadout_not_guaranteed=yes final_variant_selection=engine_internal_not_script_visible"'
    )


def render_target_transition_body(
    variants: dict[str, Variant],
    tier: Tier,
    role: Role,
    state: str,
    target: str,
    activation: str,
    priority: int,
    c_variant: Variant,
    include_missing: bool,
) -> list[str]:
    active_flag = target_state_flag(tier, role, state)
    lines = [
        "\t\tif = {",
        f"\t\t\tlimit = {{ NOT = {{ has_country_flag = {active_flag} }} }}",
    ]
    lines.extend(f"\t\t\tclr_country_flag = {target_state_flag(tier, role, item)}" for item in TARGET_STATES)
    lines.extend(
        [
            f"\t\t\tset_country_flag = {active_flag}",
            f'\t\t\tlog = "[GetYear] [GetMonth] | DAI_PLANE_TARGET_SELECT | country=[THIS.GetName] tier={tier.log_key} role={role.key} target={target} priority={priority} match_value={priority} activation={activation} production_line_selection=engine_internal_not_script_visible"',
        ]
    )
    if include_missing:
        lines.extend(render_missing_c_requirements(tier, role, c_variant))
    if state == "any":
        lines.append(f"\t\t\t{any_options_log(variants, tier, role)}")
    if state == "none":
        lines.append(
            f'\t\t\tlog = "[GetYear] [GetMonth] | DAI_PLANE_TARGET_MISSING | country=[THIS.GetName] tier={tier.log_key} role={role.key} target=fallback requirement=exact_B_or_A_ownership_or_native_ANY result=none"'
        )
    lines.append("\t\t}")
    return lines


def render_target_transition_effect(
    variants: dict[str, Variant], tier: Tier, role: Role
) -> list[str]:
    c_variant = exact_variant(variants, tier, role, "C")
    branches = [
        (
            "if",
            [f"has_country_flag = {design_flag(tier, role, 'C')}"],
            "c_exact",
            "C_ULTIMATE",
            "exact_local_ownership",
            target_value(tier, "C"),
            False,
        ),
        (
            "else_if",
            [f"{native_profile(tier, role, 'C')} = yes"],
            "c_native",
            "C_ULTIMATE",
            "native_full_real_tech",
            target_value(tier, "C"),
            False,
        ),
        (
            "else_if",
            [f"{native_any(tier, role)} = yes"],
            "any",
            "ANY",
            "native_real_tech",
            target_value(tier, "ANY"),
            True,
        ),
        (
            "else_if",
            [f"has_country_flag = {design_flag(tier, role, 'B')}"],
            "b",
            "B",
            "exact_local_ownership",
            target_value(tier, "B"),
            True,
        ),
        (
            "else_if",
            [f"has_country_flag = {design_flag(tier, role, 'A')}"],
            "a",
            "A",
            "exact_local_ownership",
            target_value(tier, "A"),
            True,
        ),
    ]
    lines = [f"{target_transition_effect_name(tier, role)} = {{"]
    relevance_keyword = "if"
    if role.key.startswith("carrier_"):
        lines.extend(
            [
                "\tif = {",
                "\t\tlimit = {",
                "\t\t\thas_navy_size = {",
                "\t\t\t\tunit = carrier",
                "\t\t\t\tsize < 1",
                "\t\t\t}",
                "\t\t}",
            ]
        )
        lines.extend(
            render_target_transition_body(
                variants,
                tier,
                role,
                "no_carrier",
                "NONE",
                "carrier_count_zero",
                0,
                c_variant,
                False,
            )
        )
        lines.append("\t}")
        relevance_keyword = "else_if"

    lines.extend(
        [
            f"\t{relevance_keyword} = {{",
            "\t\tlimit = {",
            "\t\t\tOR = {",
        ]
    )
    lines.extend(
        [
            f"\t\t\t\thas_tech = {tier.frame_tech}",
            f"\t\t\t\thas_country_flag = DAI_{tier.key}_licensed",
            f"\t\t\t\thas_country_flag = {design_flag(tier, role, 'C')}",
            f"\t\t\t\thas_country_flag = {design_flag(tier, role, 'B')}",
            f"\t\t\t\thas_country_flag = {design_flag(tier, role, 'A')}",
            "\t\t\t}",
            "\t\t}",
        ]
    )
    for keyword, conditions, state, target, activation, priority, include_missing in branches:
        lines.extend([f"\t\t{keyword} = {{", "\t\t\tlimit = {"])
        lines.extend(f"\t\t\t\t{condition}" for condition in conditions)
        lines.append("\t\t\t}")
        body = render_target_transition_body(
            variants,
            tier,
            role,
            state,
            target,
            activation,
            priority,
            c_variant,
            include_missing,
        )
        lines.extend("\t" + line for line in body)
        lines.append("\t\t}")
    lines.append("\t\telse = {")
    body = render_target_transition_body(
        variants, tier, role, "none", "NONE", "blocked", 0, c_variant, True
    )
    lines.extend("\t" + line for line in body)
    lines.extend(["\t\t}", "\t}", "}", ""])
    return lines


def generate_diagnostics(variants: dict[str, Variant]) -> str:
    lines = [
        "# Generated by tools/generate_plane_role_licensing.py.",
        "# Logs target eligibility transitions; the engine's production-line choice is not script-visible.",
        "",
    ]
    for tier in TIERS:
        for role in tier.roles:
            lines.extend(render_target_transition_effect(variants, tier, role))

    lines.extend(
        [
            "DAI_log_small_aircraft_target_transitions = {",
            "\tif = {",
            "\t\tlimit = {",
            "\t\t\tis_ai = yes",
            "\t\t\tOR = {",
            "\t\t\t\tis_major = yes",
            "\t\t\t\toriginal_tag = GER",
            "\t\t\t\toriginal_tag = ENG",
            "\t\t\t\toriginal_tag = USA",
            "\t\t\t\toriginal_tag = SOV",
            "\t\t\t\toriginal_tag = FRA",
            "\t\t\t\toriginal_tag = ITA",
            "\t\t\t\toriginal_tag = JAP",
            "\t\t\t}",
            "\t\t}",
        ]
    )
    for tier in TIERS:
        for role in tier.roles:
            lines.append(f"\t\t{target_transition_effect_name(tier, role)} = yes")
    lines.extend(["\t}", "}", ""])

    # Compatibility wrappers retained for existing decisions and older log identifiers.
    lines.extend(
        [
            "DAI_log_basic_fighter_design_diagnostics = {",
            f"\t{target_transition_effect_name(TIERS[0], SMALL_ROLES[0])} = yes",
            "}",
            "",
            "DAI_log_basic_fighter_creation_result = {",
            f"\t{target_transition_effect_name(TIERS[0], SMALL_ROLES[0])} = yes",
            "}",
            "",
            "DAI_log_improved_fighter_design_diagnostics = {",
            f"\t{target_transition_effect_name(TIERS[1], SMALL_ROLES[0])} = yes",
            "}",
            "",
            "DAI_log_improved_fighter_creation_result = {",
            f"\t{target_transition_effect_name(TIERS[1], SMALL_ROLES[0])} = yes",
            "}",
            "",
        ]
    )
    return "\n".join(lines)


def generated_outputs(variants: dict[str, Variant]) -> dict[Path, str]:
    return {
        TRIGGER_OUTPUT: generate_triggers(variants).rstrip() + "\n",
        CREATE_OUTPUT: generate_creation_effects(variants).rstrip() + "\n",
        DELIVERY_OUTPUT: generate_delivery_effects(variants).rstrip() + "\n",
        DIAGNOSTIC_OUTPUT: generate_diagnostics(variants).rstrip() + "\n",
        AI_EQUIPMENT_OUTPUT: generate_ai_equipment(variants),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate and generate DAI small-aircraft licensing and targeting data."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="write changed generated outputs")
    mode.add_argument("--check", action="store_true", help="validate without writing; fail if stale")
    arguments = parser.parse_args()

    variants = load_variants()
    outputs = generated_outputs(variants)
    stale: list[Path] = []
    for path, expected in outputs.items():
        actual = path.read_text(encoding="utf-8-sig") if path.exists() else None
        if actual != expected:
            stale.append(path)

    if arguments.check:
        if stale:
            for path in stale:
                print(f"stale: {path.relative_to(ROOT)}", file=sys.stderr)
            raise SystemExit(1)
        print(f"OK: 45 profiles and {len(outputs)} generated outputs are current")
        return

    for path in stale:
        path.write_text(outputs[path], encoding="utf-8", newline="\n")
        print(f"wrote: {path.relative_to(ROOT)}")
    if not stale:
        print("No generated files changed")


if __name__ == "__main__":
    main()
