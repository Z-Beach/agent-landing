# Modpack Blueprint v0 — "magic-tech, many dimensions"
Working title: TBD (suggestions in Open Questions). Status: blueprint, no mods downloaded yet.

## 0. Non-negotiables
- **Core trio:** ProjectE (EMC economy) + chemistry (Minechem or successor) + NuclearCraft (nuclear), balanced together — chemistry is the mid-game gate into nuclear; EMC is the commodity/reconvenience layer, never the win button.
- **"Many dimensions to visit"** is the centerpiece (dimension ladder, section 5.4).
- Magic + tech both need real depth; neither should be a costume.
- **Distribution:** one client zip (whole instance folder) + one server zip, handed to a private group. Not published to CurseForge. Modified mods acceptable (private use) — prefer script/config/datapack modifications over jar-patching.
- Must boot reliably; violates nothing we already proved with the 1.320 `additionalJavaArgs` fix.

## 1. The one decision that gates everything: version + loader
### A. 1.21.1 NeoForge — RECOMMENDED
Stays on the user's known-good base (NeoForge 21.1.234 — exactly what Techmod Arena BR runs). Reuses perf stack, instance structure, ADB/CF-domain knowledge.
| system | mod | pin | status |
|---|---|---|---|
| economy | ProjectE | ProjectE-1.21.1-PE1.1.0 | VERIFIED (already installed today) |
| chemistry | Alchemistry | 1.21.1-2.4.5 (+ AlchemyLib 1.1.6, ChemLib 2.1.5) | VERIFIED (Jun 2026, stable, NeoForge) |
| nuclear | NuclearCraft: Neoteric | NuclearCraft-1.21.1-1.3.0-rc2 | VERIFIED (Modrinth API, NeoForge, release channel, pub 2026-09-06) |
- Era fit: a modern pack (Volts NG is modern too) — staying modern is in-keeping.

### B. 1.20.1 Forge — stable fallback / max mod volume
All three core systems have stable front-page builds on Forge 1.20.1: ProjectE PE1.0.1, Alchemistry 2.3.4, NC:Neoteric 1.20.1-1.2.4-rc3. 1.20.1 is the largest modern mod ecosystem → the easiest dimension catalog (everything in 5.4 is guaranteed here).

### C. 1.7.10 Forge — legacy contingency (TRUE Minechem)
The actual **Minechem v5** lives only on 1.7.10. Nuclear then = UE's Atomic Science + ICBM (the original Voltz stack) — **not** NuclearCraft. Old visuals, frozen ecosystem. Choose only if real-Minechem is non-negotiable.

## 2. Current pack — good, bad, ugly (the refactor source)
**Good (keep/reuse):**
- Create family (incl. New Age, Additions, Diesel Generators, Connected); AE2 + AdvancedAE/ExtendedAE/AppliedFlux; Mekanism family; Immersive Engineering; PneumaticCraft; Powah/FluxNetworks.
- Iron's Spells, Ars Nouveau, Occultism (thin but real magic spine to build on).
- Apotheosis suite (gear progression); Quark+Zeta; strong build layer (Supplementaries, Chipped/Rechiseled, Handcrafted…).
- Performance stack (Sodium, Lithium, FerriteCore, ModernFix).
**Bad (remove/trim):**
- ~35 Create addons — grind + conflict surface; keep ~6 curated.
- Both RS **and** AE2 — KEEP both (user decision): RS is the cheap early-game storage, AE2 mid-late. They coexist fine; the pack keeps the RS-EMI integration.
- JEI **and** EMI both active — pick one (JEI is the safer default for Alchemistry/Neoteric recipe lookup depth).
- Cruft jars in the live folder: `DistantHorizons…jar.disabled`, `createoritechcompat-1.20.1-1.0` (a 1.20.1 jar inside a 1.21.1 pack).
**Ugly (the reason we're building new):**
- Wrong spine for the goal: tech-heavy, magic-light, and essentially zero dimension mods (no TF/Aether/Betweenlands/Undergarden/Ad Astra).
- No Minechem/Alchemistry, no NuclearCraft — the exact systems the user wants are absent.
- 364 jars = startup + fingerprint drag (the very surface that broke despite the args fix).

## 3. Era DNA legend (what we borrow)
- **FTB Unleashed (1.5.2):** EMC economy + Mystcraft writable dimensions + a clean magical-tech split.
- **Volts / Volts NG:** nuclear engineering as a pillar (Atomic Science/ICBM), space-travel dimension (Galacticraft/Ad Astra), Mekanism.
- **Project Space(e):** dimension-ladder structure with ProjectE as the economy **and** Alchemistry alongside — our recipe minus nuclear.
- **TrollCraft (1.7.10):** dense magic+tech chaos formula (Thaumcraft, Blood Magic, Botania, Draconic, EnderIO, RFTools dims) with a guide/quest book gluing it.

## 4. Reusable common core (lift straight from the current pack files)
Performance: Sodium, Lithium, FerriteCore, ModernFix, EntityCulling, (Optional: Distant Horizons — decide later, it was experimental).
UI/QoL: JEI (pick one recipe viewer), Jade/WTHIT? (Jade), Xaero's/JourneyMap, Appleskin, Mouse Tweaks.
Libraries: Already-loading NeoForge libs; add only what listed mods require (Architectury, Balm, Moonlight, etc. as dependents demand).

## 5. Mod skeleton — Option A (1.21.1 NeoForge)
> Status after 2026-09-07 verification pass (Modrinth API + CurseForge): all non-beta pins resolved for 1.21.1 NeoForge. `β` = only a beta build exists on 1.21.1 — usable, but gate on first-boot testing. Pins below are final unless a build-test fails.

| mod | pin | channel | source |
|---|---|---|---|
| ProjectE | PE1.1.0 | release | CF (already in current pack) |
| Project Expansion | projectexpansion-1.21.1-1.0.6 | release | Modrinth — **the Power Flower mod**: compact single-block power flowers, 16 tiers, mini collectors/relays, star-fuel tiers, Final Power Flower |
| Alchemistry (+ AlchemyLib + ChemLib) | 2.4.5 (+1.1.6 +2.1.5) | release | CF |
| NuclearCraft: Neoteric | 1.3.0-rc2 | release | Modrinth |
| Twilight Forest | 4.8.3345 (file 7797302) | release | CF |
| Aether | 1.21.1-1.5.10-neoforge | release | Modrinth |
| Ad Astra | 1.16.25 | release | Modrinth |
| The Bumblezone | 7.15.3+1.21.1-neoforge | release | Modrinth |
| L_Ender's Cataclysm | 3.33 | release | Modrinth |
| Mekanism | 10.7.19.85 | release | Modrinth |
| Create | 6.0.10+mc1.21.1 | release | Modrinth |
| Create: New Age / Connected | 1.2.0 / 1.3.3 | release | Modrinth |
| Immersive Engineering | 12.4.2-194 | release | Modrinth |
| Powah | 6.2.10-neoforge | release | Modrinth |
| Ars Nouveau | 5.13.1 | release | Modrinth |
| Thavma (Thaumcraft rewrite) | 1.21.1-0.12.4 | release | Modrinth — modern TC: vis/arcane machines, research progression (deps: GeckoLib, Kotlin) |
| Occultism | 1.224.4 | release | Modrinth |
| Iron's Spells 'n Spellbooks | 3.16.3 | release | Modrinth |
| Terralith / Tectonic | 2.6.2 / 3.0.26 | release | Modrinth |
| Biomes O' Plenty | (current pack pin) | release | CF |
| RFTools Dimensions | 1.21-12.0.4 | β | Modrinth |
| Dimensional Doors | 6.2.2 | β | Modrinth |
| Undergarden | 0.9.6 | β | Modrinth |
| EvilCraft | 1.21.1-1.2.95-1075 | β | Modrinth |
| Create: Additions | 1.7.0 | β | Modrinth |
| Create: Steam 'n' Rails | 0.3.0-beta.2 | β | Modrinth |
| Ender IO | v8.2.12-beta | β | Modrinth |
| Refined Storage | (current pack pin) | release | CF — **restored**: early-game storage; AE2 = mid-late |
| Deeper and Darker | 1.4.1 (file 8201775) | release | CF (official; earlier Modrinth-only lookup was wrong) |
| BetterNether "New Dawn" | 21.0.20 | release | CF (community continuation) |
| BetterEnd "New Dawn" | matching 21.x | release | CF (community continuation) |
| Alex's Caves (port) | 2.0.9 + Citadel (unofficial) | port | Modrinth — pick ONE of the competing ports, pin |
| Botania | 1.21.1-449-SNAPSHOT | snapshot | blamejared maven — expect bugs, replace when official lands |
| Blood Magic (NeoVitae) | latest | port | Modrinth/GitHub — modern recreation, active |

### 5.1 Core triad (the balance triangle)
- ProjectE + ProjectE Integration (EMC values for other mods' items) + **Project Expansion** (power flowers — passive EMC gen, 16 tiers).
- Alchemistry (2.4.5) + AlchemyLib (1.1.6) + ChemLib (2.1.5) — element decomposition/recombination, the fairest modern successor to Minechem.
- NuclearCraft: Neoteric — pin `NuclearCraft-1.21.1-1.3.0-rc2` — fission/fusion, irradiation, radiation, molten salt, QNP miner.

### 5.2 Tech spine
- Refined Storage (current pack pin) — **early-game storage**; AE2 + ExtendedAE + AppliedFlux — mid-late storage/logistics. Both intentionally kept (user call).
- Mekanism 10.7.19.85 — upgrade paths, ore tripling, its own mid-tier reactors ramping into NC.
- Create 6.0.10 — the fun-factor builder spine; **user decision: keep the full addon set** (curated tier + all optional: diesel gens, stuff-additions gadgets, big cannons, gunsmithing, food, lowheated, hypertube (α), ender-storage, dragons+, chimneys, bic_bit, rustic/arise/easy structures, things & misc, ltab, railways, Encased, central-kitchen, Sophisticated×2, immersive-aircraft compat). Cut only: `createoritechcompat-1.20.1` cruft, `createages` (we gate with KubeJS), the Aeronautics bundle (experimental airships), disabled `create_cold_sweat`.
- Immersive Engineering 12.4.2-194 — multiblock heavy-industry look, wire power.
- Powah 6.2.10 — compact mid-game power.
- Ender IO (β) — optional transfer/junction depth.

**Family hubs & linker mods (audited from the current pack — all carries):**
- `mods\AE2\`: AE2 core + **ExtendedAE, AdvancedAE, AppliedFlux, applied-generators, ae2wtlib, ae2jeiintegration + linkers: arseng** (Ars↔AE2), **createappliedkinetics** (Create↔AE2), **appliede** (ProjectE/EMC↔AE2).
- `mods\RefinedStorage\`: RS2 2.0.9 (early grid) + jei / mekanism / curios integrations.
- `mods\ProjectE\`: ProjectE core + appliede (AE2 child). **Add "ProjectE Integration"** (assign/override EMC for Alchemistry/NC items — required for the balance levers in §7).
- `mods\ArsNouveau\`: ars_nouveau + ars_creo / ars_elemental / ars_ocultas / ars_polymorphia / ars_technica / ars_unification (+ reliquified trifles — Reliquary children, not ProjectE).

### 5.3 Magic rack
- Ars Nouveau 5.13.1 — the primary spellcasting system.
- **Thavma 1.21.1-0.12.4** — the modern Thaumcraft (research/vis magic — slots in the classic TC slot from the TrollCraft DNA). Early-rewrite caveats; not official TC.
- Occultism 1.224.4 — ritual spirit-tech; bridges magic and logistics.
- Iron's Spells 'n Spellbooks 3.16.3 — combat casting.
- EvilCraft (β, optional) — spirit/possession depth.
- **Ported tier (unofficial for now):** Botania (snapshot 1.21.1-449-SNAPSHOT, blamejared maven) + Blood Magic via **NeoVitae** (modern NeoForge recreation). Expect bugs; swap to official when they land.
- Not available anywhere: Hex Casting, ElementalCraft — intentional gap (Ars glyphs cover spellcraft).

### 5.4 DIMENSION LADDER (the centerpiece — fantasy + sci-fi, all verified 1.21.1 NeoForge)
Purposeful tour; ladder gates enforce progress (see §7, lever 5):
- Overworld variety: Terralith 2.6.2 + Tectonic 3.0.26 + Biomes O' Plenty.
- Flagship adventure: Twilight Forest 4.8.3345 — progression-locked boss quests.
- Sky/legend: Aether 1.21.1-1.5.10.
- Deep/abyss: **Deeper and Darker 1.4.1 (official)** + optional Undergarden (β) 0.9.6.
- Beastial strata: **Alex's Caves (unofficial port 2.0.9)** if we pin ONE port — cave biomes full of bosses/resources.
- Hell/complement: **BetterNether + BetterEnd "New Dawn" 21.0.20 (community continuation, NeoForge)**.
- Insect realm: The Bumblezone 7.15.3 — hidden bee dimension, loot for mid-game.
- Space (locked pick): Ad Astra 1.16.25 — rocket ladder to other planets (Galacticraft rejected: no modern build). THE outer ring of the tour.
- Puzzle pockets: Dimensional Doors (β) 6.2.2 — Eldritch pocket-dungeon dimensions.
- Writable worlds: RFTools Dimensions (β) 1.21-12.0.4 — the dimension-writer sandbox (Mystcraft DNA, part of the sci-fi flex).
- Boss drama cross-links: L_Ender's Cataclysm 3.33 — Infernal structures ramp difficulty and link dimensions' bosses.
- Still out (no 1.21.1 anything): Blue Skies (stuck at 1.20.4 — revisit per "use modern when it pops up").

### 5.7 Glue & docs (the "modifications to the mods" layer)
- KubeJS + CraftTweaker: recipe/balance overlay (the safe kind of modding).
- Patchouli: a pack guidebook ("The Handbook," giving the dimension tour + balance rules).
- Optional Quest Book / FTB Quests for the group's guided goals (ask Open Questions).
- Server-side: a bundled `server` start script + `eula.txt` note + RAM/Java args template.

### 5.8 Thaumic Energistics — faithful rebuild (user-directed dev project)
- **Mission:** resurrect old Thaumic Energistics (1.12.2 Extended Life codebase, cloned to `thaumic-energistics-rebuild\source\`, analyzed in `port-analysis.md` + `port-mapping.md`) as a **NeoForge 1.21.1 mod** bridging **modern AE2 (`appliedenergistics2-19.2.17`)** and **Thavma `1.21.1-0.12.4`** — the modern Thaumcraft — with **feature parity to the old mod** as the goal.
- **Core insight (verified against both jars):** old `IStorageChannel`/`IAEStack`/`IMEInventoryHandler` are gone; modern equivalent is **`AEKeyType` + `EssentiaKey extends AEKey` + `KeyCounter` + `MEStorage`/`IStorageProvider`/`ExternalStorageStrategy`**; Thavma already ships an **`IAspectContainer` capability** (insert/extract with native `simulate`, per-aspect `capacity`) plus `SealingJar`, `WorkbenchRecipe`, `InfusionRecipe`, research entries — so old TC `Aspect`/`IAspectContainer`/arcane-infusion imports map nearly 1:1 (with the old sim-undo hack *simplified away*).
- **Runtime deps already satisfied by the pack:** Thavma needs KotlinForForge ≥ 5.10 (pack has 5.12.0) + GeckoLib NeoForge 4.x (pack has 4.9.1) + NeoForge ≥ 21.1.216 (pack base is 21.1.234). Add: `thavma-1.21.1-0.12.4.jar` (+ its resources), rebuild-jar `ThaumicEnergistics-Neo-*.jar`.
- **Skeleton features to port** (Features.md parity): essentia storage channel + cells 1k–64k/creative, import/export/storage buses, level emitter, essentia + wireless terminal, jars-as-network-storage, essentia interface (bridge + infusion feed), infusion provider, arcane terminal, arcane inscriber, arcane assembler, research tab/scan. **Deferred** (need Thavma features that don't exist yet): P2P vis, theorycraft cards/aids, tube-suction export.
- **Boot notification (required):** on world-join show a screen from packed `META-INF/rebuild-state.json` listing every feature as implemented/partial/deferred + pinned-compat line (MC/NeoForge/AE2/Thavma). Re-shows only when the rebuild build changes. Full spec: `thaumic-energistics-rebuild\boot-notification-spec.md`.
- **Update policy (required):** the rebuild mod hard-pins AE2/Thavma ranges (fails at menu on mismatch); **no per-mod auto-update** — the pack updates as a whole, versioned via pack manifest (§8).

## 6. Option B deltas (1.20.1 Forge)
Hold — 1.21.1 holds the whole skeleton. Option B exists only as the fallback if a β pin proves unusable at first-boot, or if the group demands a dropped classic (Botania/Blood Magic/Alex's Caves/Blue Skies — all guaranteed on 1.20.1, loader Forge).

## 7. Balance levers (the triangle conformance)
1. **Chemistry → nuclear gate:** Alchemistry's element work should be the cheapest path to NC's exotic fuels/isotope materials (recipes join alchemist output → NC machines), so chemistry is functionally "how you build up the periodic table the nuclear grid eats."
2. **EMC discipline:** set EMC values for NC isotopes/fuel/refined materials (ProjectE Integration / custom EMC: false where broken); keep Consumable/Transmutation as convenience, not self-printing bug (disable any known infinite-EMC loops, e.g. condenser-into-alchemist-into-EMC).
3. **Radiation vs EMC:** radiation armor/perk costs are EMC-priced; radiation zones are not condensed away (keeps nuclear risk real).
4. **Power curve:** Create (entry) → Mek/Powah/IE (mid) → NC fission/fusion (late), with Alchemistry pushing the exotic tier. No single line to infinite power before the dimension ladder is cleared.
5. **Dimension gates:** TF-style progression keys that need the ladder (a mid-dimension material gates EMC transmutation tiers).

> **Power Flower note (user request):** Project Expansion's flowers are the accepted economy layer — keep them enabled; tie flower tier unlocks to §7.5 dimension gates rather than disabling them. Their output feeds EMC, which remains the convenience (not win) layer per levers 2–3.

## 8. Distribution & packaging
**Client zip** (`<name>-client.zip`):
- Whole instance folder (mods, config, kubejs, datapacks, resourcepacks, defaultoptions) **minus**: logs, crash-reports, backups, `.disabled` cruft, saves (fresh world), shaderpacks (optional).
- **Mods are folder-sorted** (`mods\Create\`, `mods\AE2\`, `mods\RefinedStorage\`, `mods\ProjectE\`, `mods\ArsNouveau\`, `mods\Nuclear\`, `mods\Dimensions\`, rest flat) — NeoForge loads `mods\` recursively, so nested jars work in every launcher and keep the sort intact.
- Include `modlist.md` (version pins + checksums) and the Patchouli guide note.
- Launcher notes: extract into any launcher's `Instances\` (CF auto-imports folders found there; Prism/MultiMC import the zip directly). Ship the same `additionalJavaArgs` map fix note for any CF-created instance json.
**Server zip** (`<name>-server.zip`):
- mods + config + kubejs + datapacks, `eula.txt` (blank/EULA note), `start.bat`/`.sh` template with `-Xmx` + GC + `-XX` crash flags, README with port/whitelist/op instructions and RAM guidance (mirror the friends' server learnings).
- Both zips must carry the **same pinned versions** — freeze the pack, updates only via explicit re-builds.
- **Whole-pack update policy (user mandate):** **no mod is enabled to auto-update on its own.** Every rebuild of the Thaumic Energistics port hard-pins its AE2/Thavma deps (menu-time failure on mismatch) and its boot screen re-notifies on every changed build. Ship a `pack.json` manifest (pack version + jar sha256 list) in the zips; a bump = one new pack version applied to the whole instance, never piecemeal mod updates.

## 9. Build checklist (next runbook)
1. [x] User picks version/loader → **A (1.21.1 NeoForge)** + dimension theme → **fantasy + sci-fi (space included)**. ⚠ Name still TBD (Q3).
2. [ ] Standing up an isolated test instance (copy-a-folder approach; NOT touching Techmod Arena BR's live folder). Use the proven fix pattern (both DB record + folder `minecraftinstance.json` → `additionalJavaArgs` map) the moment it's created.
3. [ ] Download + pin every jar; record checksums in `modlist.md`. Approved add-on set (§11) staged from `pack-addons\` into the instance `mods\`; Krypton/Connectivity join-test decides the keeper.
4. [ ] First boot on the patched instance; confirm detection + Trace log flags (`--gameDir`, `-Xmx`, crash flags).
5. [ ] Balance pass (levers in §7) via KubeJS/CraftTweaker/EMC config.
6. [ ] Dimension ladder sanity tour (each dimension reachable + pulls on progress).
7. [ ] Build client zip + server zip; reinstall-test both from scratch.
8. [ ] Friend-server deploy after their power-outage recovery confirms back online.

## 10. Open questions
1. **Version/loader:** **RESOLVED → A (1.21.1 NeoForge)** — all three core systems verified on 1.21.1 (ProjectE PE1.1.0, Alchemistry 2.4.5, NC:Neoteric 1.3.0-rc2).
2. **Space strand:** **RESOLVED → include space; fantasy + sci-fi together** in the dimension ladder.
3. **Name:** working title TBD (suggest, e.g., "Crucible", "The Gadfly Worlds", "Polyatomic"…).
4. **Guide/quests:** Patchouli guidebook only, or also an FTB Quests book for guided goals?
5. **Difficulty posture:** standard, or harder (more radiation, tighter EMC) as the group's house style?

## 11. Performance & worth-adding supplement (verified 1.21.1 NeoForge on Modrinth, 2026-09-07)
**Already in the live pack (don't double-add):** ModernFix 5.27.14, FerriteCore 7.0.3, Lithium-NeoForge 0.15.4, Sodium-neoforge 0.8.12b + sodium-extra + Reese's + Iris + EuphoriaPatcher, ImmediatelyFast 1.6.10, entityculling 1.10.5, FastWorkbench 9.1.3 / FastFurnace 9.0.1 / FastSuite 6.0.7, createbetterfps, Noisium 2.7.0, ServerCore 1.5.19, chunksending 2.9, Chunky 1.4.23, connectivity 7.6, spark, alltheleaks, crashutilities, gpumemleakfix, structureessentials, toofast.
**Add (perf/loading):** BadOptimizations 2.4.1 · Krypton Reno 0.2.28.1 (caveat: overlaps Connectivity — keep the winner after a join test) · Dynamic FPS 3.11.4 (0-FPS when unfocused; good for the host) · Particle Core 0.3.3 · Sound Physics Remastered neoforge-1.21.1-1.5.1 (occlusion + audio CPU cut). ~~Distant Horizons 3.2.0-b (optional LOD beta)~~ REMOVED by user 2026-09-07.
**Not available on 1.21.1 (skip, covered elsewhere):** Memory Leak Fix (≤1.20.1; ModernFix+gpumemleakfix cover), Smooth Boot (dead), C2ME/Phosphor (fabric).
**Add (content/UX, classic-hardened):** Cooking for Blockheads 21.1.24 (the 2013 kitchen classic; pairs with Farmer's/Aquaculture Delight already present) · More Curios Slots 1.4 · Botania 1.21.1-449-SNAPSHOT from blamejared (official port WIP — snapshot caveat; slot beside Ars/Thavma). ~~AmbientSounds 6.3.8 · Presence Footsteps (pf-neoforge) 1.21.1-1.12.0-beta.1~~ REMOVED by user 2026-09-07.
**APPROVED ADD-ON SET (user-locked 2026-09-07):** BadOptimizations 2.4.1, Krypton Reno 0.2.28.1, Dynamic FPS 3.11.4, Particle Core 0.3.3, Sound Physics Remastered 1.5.1, Cooking for Blockheads 21.1.24, More Curios Slots 1.4, Botania 1.21.1-449-SNAPSHOT. Krypton vs Connectivity decision at first join test. Staged jars → `pack-addons\` (next to this doc); files are Modrinth CDN direct per-fetch, Botania from maven.blamejared.com (resolved via maven-metadata.xml).
**Old classics with NO modern build (don't chase):** Ice and Fire, Astral Sorcery, Pam's HarvestCraft 2, Thaumcraft (covered by our Thavma port), AST → cover evolutionary niches with Cataclysm/Mowzie's/CreeperOverhaul etc. already packed.

## 12. Unification & EMC economy (chemistry) — STAGED 2026-09-07
- MineChem has no 1.21.x build; successor is **Alchemistry 2.4.5** (+ AlchemyLib 1.1.6 + ChemLib 2.1.5, all CurseForge-only) — verified **NOT installed** in live pack; must be added for the chemical side to exist in-game.
- EMC model built from Alchemistry's real dissolver graph (685 recipes; 1 unit≈1 atom, 1 ingot=16 units). Element bases anchor-first from live `custom_emc.json` (Fe=16, Cu=8, Au=128, Sn=16, Pb=32, Ni=64, Ag=32, Al=8, Os=32, U=256, Pt=256, graphite=64; else round(mass×0.28651)). Verified: coal 128, iron 256, gold 2048, copper 128, diamond 8192.
- Overlap reconciliation (EMC-carrier wins) + material valuations → `pack-integration\emc-unification.md`, staged `custom-emc-additions.json`, `emc-element-bases.json`.
- Pending: fetch the Alchemistry trio (CF), tag-census AEU canonical ids, apply (live or test instance), netherite_scrap 896 override decision.