# Code preferences for this project

Readable, clean code comes first. Behaviour changes are separate from tidy-ups: don't mix them.

## Layout
- `src/defense/`: wave defense only (waves, asteroids, fighters and cruisers).
- `src/mine/`: the mine and the demo room only (world, rules, robots).
- `src/dogfight/`: the multiplayer free-for-all only (match rules, rival ships, spawning, supplies).
- `src/capture/`: the team mode, capture the data (teams, discs, scoring, the capture screen).
- `src/flagship/`: the crew mode, flagship defense (the crew and its seats, turrets and their aim, shared ammo and energy, the crew HUD). It runs wave defense's waves inside its own state.
- `src/open_play/`: the persistent shared universe mode, Open Play. Folders are split by area (see `ralph/CONTRACTS.md`):
  - `contracts/`: the shared types and traits all three areas build against (ids, bodies, universe, cargo, mounts, ships, profile, prices, `OpenPlayWorld`).
  - `world/`: the universe catalog and generator, economy, host, saves.
  - `flight/`: ships, mounts, combat, mining, loot, crew, waves.
  - `interface/`: star map, station menus, HUD, menu entry.
- `src/server/`: the windowless server that hosts a match.
- `src/shared/`: everything both modes use (player, weapons, enemies, HUD, rendering, audio, menus).
- Mode-only code goes in its mode's folder. Shared code reaches mode state through `Game`'s `mode_state` accessors.

## Deor
Some code is written in Deor, not Rust (`*/deor/*.deor`). The `.rs` files beside them are generated, so edit the
`.deor` and run `scripts/build_deor.sh`. See `DEOR_CONVERSION.md` for the rules and the Deor docs in `deor_specification/`.

## Naming
- Use full, descriptive words. No `e`, `a`, `p`, `sw`, `sh`, `lp`, `cd`. Write `enemy`, `asteroid`, `player_pos`, `screen`, `collision_cooldown`.
- Booleans read like questions: `is_fighter`, `player_alive`, `has_key`.
- Functions say what they do: `apply_laser_hit`, `steer_around_obstacles`, not `do_hit` or `update2`.
- Name the unit when it isn't obvious: `seconds_left`, `fov_degrees`, `distance`.

## Functions
- Short, one job each. If a function needs "and" to describe it, split it.
- Deep nesting (3+ levels) is a sign to extract a function.
- Prefer early `return` / `continue` over nested `if`s.
- Don't repeat code. Shared helpers live in:
  - `shared/math.rs`: vectors, geometry, easing
  - `shared/lighting.rs`: lighting and flat-shaded drawing
  - `shared/ui.rs`: `Screen`, bars, centred text

## Spacing
`scripts/check_spacing.py` enforces these (`--fix` applies them); `cargo fmt` can't.
- Blank line after a closing `}` (unless the next line is another `}` or `else`).
- Blank line before `if`, `for`, `while`, `match`, `loop` (unless it is the first line of its block).
- Blank line before `return`, `break`, `continue` and before a block's final expression.
- Blank line between match arms when either one has a multi-line body. One-line arms stay packed.
- Consecutive `let`s don't need blank lines between them, but leave a blank line after a run of them.
- Blank line before a comment that starts a new step. A comment above a statement stays attached to it.

## Constants and data
- No magic numbers. Give them a named `const` at the top of the file, with a short comment for the unit or meaning.
- Game-wide tuning goes in `shared/consts.rs`. Weapon numbers go in `shared/weapons/*/specs.rs`. Mode-only numbers go in that mode's `consts.rs`.
- Group related fields in a struct instead of loose fields or tuples (see `Waves`, `Banner`, `ModeChoice`, `Row`).

## Files and folders
- Split a big file into a folder named after it: `mod.rs` for the main type or entry points, plus sibling files for each concern (see `defense/enemy_ai/`, `shared/hud/targeting/`).
- Each module starts with a comment saying what it is for when that isn't obvious.
- Prefer `pub(super)` / `pub(in path)` over `pub` unless the item is used outside its parent.

## Comments
- Explain why, not what. Don't narrate code that already reads clearly.
- Keep short comments on constants and on non-obvious maths.

## Before finishing any change
1. `cargo fmt` (config is in `rustfmt.toml`, max width 120)
2. `python3 scripts/check_spacing.py --fix` (the spacing rules above; `cargo fmt` can't enforce them)
3. `cargo build`: no warnings
4. `cargo test`
5. `cargo clippy`: no warnings
6. `python3 scripts/check_reuse.py`: Open Play copies of shared/other-mode code; real differences go in `scripts/reuse_allow.txt` with a reason
7. Summarize what changed in a few lines. No long recap.

## Deor conversion (Ralph loop)
- A conversion only counts when the hand-written Rust it replaces is deleted. Add Deor to replace Rust, not to sit beside it.
- Before committing, report the net change in hand-written Rust lines (tokei, leaving out generated Rust).
- If the net drop is under 50 lines, pick a bigger self-contained slice, or say why that isn't possible.
- Prefer converting whole files or modules over small helpers.
- In a Ralph loop round, commit at the end of the round. This overrides the global "never commit unless I ask".
