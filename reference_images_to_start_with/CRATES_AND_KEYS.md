# Crates, Keys and Events: how to make the next one

This is the working guide for adding a crate, a key, an event, or all three.
It covers the files you touch, the fields that matter, how the opening
animation is themed, and the design rules that make an opening feel like a
pull on a slot machine rather than a form submission.

Short version: **a new crate is mostly data.** One series entry, two
catalogue items (the crate and its key), the loot, and a theme for the
opening. The market, inventory, admin panel, live drop feed, odds display,
bundles and badges all pick it up from that data.

---

## 1. How the pieces fit

| Piece | Where | What it is |
|---|---|---|
| Crate item | `app/models/cosmetics.py`, `CRATES` | An ordinary inventory item (`slot: "crate"`) with a 3D model, a price and a `series`. Each copy has its own serial. |
| Key item | `app/models/cosmetics.py`, `KEYS` | An item (`slot: "key"`) whose `opens` lists the series it unlocks. |
| Series | `app/models/crates.py`, `SERIES` | Ties a crate to a key and holds the loot, grade odds, Unusual chance, effects, dates and theme. |
| Event | `app/models/crates.py`, `EVENTS` | A limited-time wrapper: name, blurb, dates, colours, the series it sells and the effect on its hero crate. |
| Offers | `app/models/crates.py`, `OFFERS` | Bundles (crate + key, five-packs) with a saving shown against buying them singly. |
| Unusual effects | `app/models/catalog.py`, `UNUSUAL_EFFECTS` | The particle effects a hat can roll. Event effects carry `"event": "<id>"`. |
| Particle shapes | `static/js/engine/particles.js` | New sprite shapes for new effects (ghost, candycorn, sweet...). |
| Opening theme | `static/js/ui/crates.js`, `THEMES` + `static/css/market.css` `.theme-<id>` | The sky, burst pieces, beam colour, the effect that seeps out of the crate and the backdrop art. |
| Sounds | `static/js/ui/crates.js`, `Sfx` | Synthesised with WebAudio, so there are no files to ship. `opts.theme` lets a theme detune or darken them. |
| Event badge | `app/models/badges.py` + `crates.open_crate` | Optional: a badge earned by opening the event's crates while the event runs. |

What happens when someone opens a crate:

1. The page calls `Crates.open({series, crateInv, keyInv})` (`crates.js`).
   Either inventory row may be left out, and the server picks one.
2. `POST /api/crates/open` runs `crates.open_crate` inside **one write
   transaction**. It checks ownership and that the key fits, deletes both
   rows, rolls the result (`roll`), grants the item, writes a
   `crate_openings` row and books badges. Then it builds the reel strip
   **around the result it already has** (`build_reel`).
3. The browser plays the show: crate drops, key flies into the lock, turns,
   the crate rattles, the lid blows, the reel spins, the hook overshoots and
   settles. The answer is already fixed; the animation only reveals it.
4. The reveal card offers **Wear it now** and **Open another (n left)**.
   The `crates:opened` event updates the market feed and the inventory shelf.

Nothing the browser does can change the outcome. Keep it that way: every
new feature that decides something belongs in `crates.py`.

---

## 2. The rolling hook: the design rules

Every opening is a short story with rising tension, a moment of release and
an immediate way to do it again. These are the levers and where each lives.
Use them for every new theme.

### Anticipation (build it up before the answer)

* **Ritual before reward.** The crate drops and lands with a thud. The key
  flies in and seats, turns (click), and then the crate *rattles* harder and
  harder. The steps are fixed and recognisable, so the player learns to feel
  them coming. (`Stage.prototype.run`: drop 0 to 0.9 s, key flight 0.9 to
  2.0 s, insert, turn, shake 2.75 to 3.9 s.)
* **Something escapes the lid.** The theme's `seep` effect leaks out while
  it shakes: sunbeams for the classic crate, haunted wisps for Halloween.
* **Light beam on open.** The `beam` colour pours out when the lid goes, and
  the `burst` of themed pieces flies out of it.

### The reel (the roulette)

* **Speed curve.** The reel starts fast, eases out, and the **hook
  overshoots and snaps back** onto the winner. The ticks get slower as it
  slows, so the ear follows the eye (`stepReel`, `Sfx.play('tick')`).
* **Near misses** (`build_reel`). The best grade in the series sits **one
  tile past** the winner, and a good one sits just before it. It stings and
  it makes "one more" feel close.
* **Mystery Unusual tiles.** One or two `?` tiles in the Unusual colour go
  past during the fast part of the spin. Players learn that Unusuals live on
  this reel.
* **Grade colour everywhere.** Each tile is edged in its grade colour
  (`GRADES`), so a passing purple or red tile is read before its picture.

### Release (the reveal)

* **Grade-scaled celebration.** Confetti scales with grade and is biggest for
  Unusual and Mythic. The reveal sound changes with grade.
* **Show the thing, live.** The won item spins on a turntable with its
  Unusual effect running, not as a still picture.
* **Make it immediately useful.** "Wear it now" equips it in one click.

### The loop (make the next pull easy)

* **Open another (n left)** sits right on the reveal card.
* **The "Ready to open!" card** (`Crates.prompt`) slides in whenever a
  purchase leaves you holding a crate and a matching key.
* **Inventory key mode.** Clicking a key makes the matching crates glow, and
  the key follows the cursor until you drop it on one.
* **Bundles anchor the price.** The pair and five-pack show a crossed-out
  "bought singly" price and a SAVE pill.

### Social proof and scarcity

* **Live drop feed.** Every opening goes on the market ticker. Unusual pulls
  toast to everyone on the market page and appear in the site's news ticker.
* **Event countdown.** The hero counts down to the event's end, ticking every
  second.
* **Event-only effects and items.** Event crates carry effects and items
  that exist nowhere else, and the event badge can only be earned while the
  event runs.

### Fair play (non-negotiable)

* **Odds are published.** "What's inside?" shows every grade's chance and the
  Unusual chance, worked out from the same `SERIES` numbers the roll uses.
* **The result is decided first, on the server.** The reel is decoration
  built around it. Never fake an outcome client side.
* **Skip is always available**, and so is mute. `prefers-reduced-motion`
  stops the decorative motion.

---

## 3. Recipe: a new crate series

The example here adds a winter crate: `crate_frostfall`, opened by
`key_frostfall`, series id `frostfall`.

### Step 1: model the crate and the key (`cosmetics.py`)

Crates and keys are built like any other item, from parts placed with
`modeling.part` / `modeling.place` (see `_classic_crate`, `_hallowed_crate`).

The opening animation needs three things from a crate model:

* **`lid=1`** on every part that belongs to the lid (planks, straps, hasp).
* **`data.hinge`**: the point the lid swings about. The axis is X, so the
  hinge sits on the back top edge (e.g. `[0, 0.50, -0.56]`).
* **`lock=1`** on the lock plate, so the key knows where to fly.

Stencils and logos are **stickers**: a thin box with `alpha=-1` and a
`decal`. Only the decal is printed (`renderer.js` treats negative alpha as
sticker). New decals are painters in `static/js/engine/textures.js`
(`painter('crate_frost', function (ctx) {...})`).

```python
CRATES.append({
    "id": "crate_frostfall", "name": "Frostfall Crate", "slot": "crate",
    "price": 500, "rarity": "rare", "sort_order": 3, "series": "frostfall",
    "event": "winter",                       # leave out for an always-on crate
    "description": "One sentence that sells it.",
    "data": {"parts": _frostfall_crate(), "hinge": [0, 0.50, -0.56]}})
KEYS.append({
    "id": "key_frostfall", "name": "Frostfall Key", "slot": "key",
    "price": 600, "rarity": "rare", "sort_order": 3, "opens": ["frostfall"],
    "event": "winter",
    "description": "Unlocks one Frostfall Crate.",
    "data": {"parts": _frostfall_key()}})
```

Add both to the `ALL_ITEMS` concatenation in `catalog.py` if you made new
lists, rather than appending to `CRATES`/`KEYS`. Crates and keys are
**stackable** (`market.STACKABLE`); the shelf and the buy dialog take a
quantity.

### Step 2: the loot

Loot is any catalogue item ids. Items that should **only** come out of
crates are automatically refused by the market: everything in any series'
`loot` is `CRATE_EXCLUSIVE`. Give each item a `rarity`, which is its drop
grade unless the series overrides it with `grade_of`.

Hats can roll Unusual. Other slots (weapons, back items) never do, but they
can be graded `mythic` to make them the chase items.

### Step 3: the series (`crates.py`, `SERIES`)

```python
"frostfall": {
    "id": "frostfall", "number": 3,                 # shown as "Series #3"
    "name": "Frostfall Crate",
    "crate": "crate_frostfall", "key": "key_frostfall",
    "tagline": "Packed in snow. Still cold inside.",
    "theme": "frostfall",                           # crates.js THEMES key
    "event": "winter",                              # optional
    "colors": {"accent": "#7fd1ff", "deep": "#0b1a2e", "glow": "#e8f8ff"},
    "starts": _date("2026-12-01"), "ends": _date("2027-01-08"),   # 0, 0 = always
    "grades": {"uncommon": 45, "rare": 38, "legendary": 12, "mythic": 5},
    "unusual_chance": 0.03,                         # 3% of hat pulls
    "effects": WINTER_EFFECTS,                      # Unusual effect ids
    "effect_weights": {"snowglobe": 3.0},           # optional favourites
    "loot": [...],
    "grade_of": {"use_icicle_bow": "mythic"},       # optional overrides
},
```

| Field | Meaning |
|---|---|
| `grades` | Relative weights per grade. Only grades that have loot are rolled. The odds bars and "What's inside?" are computed from these. |
| `unusual_chance` | Chance a **hat** pull comes out Unusual. |
| `effects` / `effect_weights` | Which Unusual effects can roll, and any that roll more often (weight > 1 also makes them the "featured" effects on the event hero). |
| `starts` / `ends` | UTC timestamps. Outside the window the crate and key cannot be bought, though crates people already own can still be opened. |
| `theme` | Which opening sequence plays. Falls back to `classic`. |

### Step 4: the event (optional, `EVENTS`)

```python
"winter": {
    "id": "winter", "name": "Frostfall", "title": "The Long Frost",
    "blurb": "Two or three sentences of mood for the market hero.",
    "starts": SERIES["frostfall"]["starts"], "ends": SERIES["frostfall"]["ends"],
    "colors": SERIES["frostfall"]["colors"],
    "series": "frostfall",            # what the hero sells
    "hero_effect": "frostbite",       # the Unusual effect round the hero crate
},
```

While an event runs, the market shows its hero (countdown, buy buttons, chase
items best-first, the Unusual tease), adds an event aisle, and puts the event
in the site news ticker. All of it comes from `crates.event_feature()`.

### Step 5: bundles (`OFFERS`)

```python
{"id": "offer_frostfall_pair", "name": "Frostfall Pair", "series": "frostfall",
 "contents": {"crate_frostfall": 1, "key_frostfall": 1}, "price": 1050,
 "blurb": "One crate, one key."},
```

Price a bundle **below** the singles total. The card shows the saving.
Offers only show while their series is on sale.

### Step 6: Unusual effects (optional)

Add to `catalog.UNUSUAL_EFFECTS` with `"event": "winter"`. If you need a new
sprite, add a shape to `particles.js` (`SHAPES`), then run
`python3 tools/checkeffects.py`, which checks that every effect names a
shape the renderer has.
Two new effects per event is a good number: enough to chase, few enough
that each one stays special.

### Step 7: the opening theme (`crates.js` + `market.css`)

```js
frostfall: {
  sky: { top: '#06101e', horizon: '#1b3a5c', sun: [0.3, 0.9, 0.4], clouds: 0, tint: '#cfe8ff' },
  ambient: '#7a9cc0',
  burst: ['#ffffff', '#bfe9ff', '#7fd1ff'],
  pieces: [{ shape: 'star', colors: ['#ffffff', '#dff4ff'], blend: 'add' },
           { shape: 'spark', colors: ['#bfe9ff'], blend: 'add' }],
  seep: 'frostbite', after: 'snowglobe',
  beam: '#e8f8ff'
}
```

* `pieces`: what bursts out of the lid. Give each shape **its own palette**
  (white ghosts, black bats), or they all come out the same tint.
* `seep`: an Unusual effect id that leaks while the crate shakes. `after` is
  the one left hanging once it is open.
* CSS: `.theme-frostfall .cs-bg`, `.cs-rays`, and any extra backdrop art
  (the Halloween theme turns on `.cs-moon` and `.cs-bats`). The market's
  showcase card uses `.theme-frostfall .mk-show-art`, the hero uses
  `.mk-hero.theme-winter`, and the inventory shelf uses
  `.stash-card.theme-frostfall`.
* Sounds: `Sfx.play(name, { theme })`. Add a branch in `Sfx.play` if the
  theme should sound different (the Halloween theme pitches some of the
  tones lower, e.g. the whoosh).

### Step 8: an event badge (optional, `badges.py`)

Add a badge with `game: "event"`, `event: "winter"`, a stat such as
`ev_frostfall_2026`, a `moon`/`star` family and an emblem painter
(`em_snowflake` in `textures.js`). Then book the stat in
`crates.open_crate` next to the Hallowed Harvest one:

```python
if series.get("event") == "winter" and event_active("winter"):
    changes.append(("ev_frostfall_2026", 1, "add"))
```

Unearned event badges only appear in the Badge Inventory while their event
runs. Earned ones stay forever. See
`howto_readmes/badge_creation_and_implimentation_and_ceration.txt`.

---

## 4. Testing a new crate

* **Force events on:** `BLOCKHAVEN_EVENTS=all python3 main.py ...` keeps every
  event running whatever the date.
* **Drop A Crate** (admin dashboard): give any player any number of crates,
  with or without keys, and an optional note. They get a notification.
* **Grant an item** (admin dashboard): crates and keys are in their own
  groups in the picker.
* **Odds sanity:** `crates.contents("frostfall")` returns the per-grade
  chances and per-item chances the dialog shows.
* **Roll sanity:** in a Python shell, run
  `[crates.roll(crates.SERIES["frostfall"]) for _ in range(10000)]` and count
  the grades against the table.
* **Look at it:** open one from the market and from the inventory (key mode),
  try Skip at every phase, and check the reveal on a phone width.
* Run `python3 tools/sitetests.py`. It covers buying, stacking, bundles,
  opening, the feed and the refusal to sell crate-exclusive items.

---

## 5. Checklist

- [ ] Crate model: `lid=1` parts, `data.hinge`, `lock=1` plate, a sticker stencil
- [ ] Key model, with `opens: ["<series>"]`
- [ ] Loot items exist, with sensible rarities and `grade_of` for chase items
- [ ] `SERIES` entry (number, theme, colours, grades, Unusual chance, effects, dates)
- [ ] `EVENTS` entry if it is limited (series, hero_effect)
- [ ] One or two `OFFERS`
- [ ] New Unusual effects, plus shapes if needed
- [ ] `THEMES` entry and `.theme-<id>` CSS (stage, showcase, hero, shelf)
- [ ] Event badge and its `open_crate` hook (optional)
- [ ] Bot unboxing picks it up automatically (`crates.bot_unbox`) and bots
      price crate items at crate + key (`bots/factory.py`)
- [ ] Opened end to end, on desktop and phone width, with sound on and off
