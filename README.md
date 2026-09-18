# BLOCKHAVEN

A complete block-world game platform written in **pure Python 3 (standard
library only)** and **vanilla JavaScript**. It has two halves:

* **The UI** — the website: accounts, profiles with a live 3D character, an
  avatar editor with two body types, an item market with Unusual rolls, an
  inventory bound to your account, friends/followers/posts/comments/messages,
  a world browser and an administrator dashboard. It has a hand-built dark
  theme and a phone layout, because the site half is meant to work from a
  pocket even though the game half is not.
* **The Game View** — press **Load** on a world and you drop into a first- or
  third-person block shooter running in your browser, served from the same
  port on its own sub-page (`/burger_tycoon`, `/capture_the_flag`,
  `/fortress_team_2`).

No frameworks, no build step, no `pip install`, no asset files. Every texture,
sound, mesh and map is generated at runtime.

```
./run.sh
```

Then open **http://<your-ip>:8972/** on any machine on your network. The site
works on a phone; the Game View needs a desktop browser (pointer lock, a
keyboard and a mouse), so its Load buttons are hidden on small screens.

---

## Quick start

```bash
./run.sh                        # website + all three game hosts on port 8972
./run.sh --port 9000            # somewhere else
./run.sh --no-games             # website only
./run.sh --reset                # wipe the database and re-seed
./run.sh --debug                # verbose tracebacks, no static caching
./run.sh --status-interval 8    # slow the terminal read-out down (0 = off)
```

`run.sh` is a thin wrapper around `python3 main.py`; every flag works either
way. It leaves a live status block in the terminal, refreshed **every four
seconds**, carrying everything the admin dashboard does — traffic, accounts,
presence, the catalogue, the friend graph, the economy down to the ledger
transaction count and the number of market purchases, what each world is
carrying and whether the host processes are healthy.

It is drawn for a terminal rather than transcribed from the browser: numbers
that move get a sparkline of the last two minutes, counters that only climb
get a change arrow, anything with a ceiling gets a meter, and a braille wheel
in the title turns once per refresh so a glance says whether the read-out is
still live. It is **redrawn in place**: the cursor walks back up over the
previous copy instead of reprinting it, so the numbers change where they stand
and the start-up banner stays put above them. Sixteen-odd lines, so it fits a
portrait monitor or a phone-shaped SSH window whole, and it re-flows for the
width it is given — the sparklines, the meters and the softer words drop out
before anything carrying a number does. A terminal that cannot render the
block glyphs gets an ASCII understudy for each of them.

Requirements: Python 3.9+ and a browser with WebGL. That is the whole list.

### Accounts created on first run

| Account | Password | Notes |
| --- | --- | --- |
| `admin_system` | `passman69` | Administrator. Can open `/admin-dashboard`. Owns two Unusual hats. |
| `admin_test` | `passman69` | Ordinary player used to demonstrate the Unusual system (Unusual Propeller Beanie + Unusual Mohawk Spikes). |
| `builderman_x`, `RetroKid2007`, `BlockSmith`, `NoobSlayer99`, `PixelPatty`, `CartPusher`, `FlagRunner`, `GrillMaster` | `blockhaven` | Demo players so the social features have something to show. |

Everyone else who registers starts with **2,000 credits**, a Basic Pistol, a
Basic Shotgun and a Basic Stick.

---

## The worlds

| World | URL | Mode | Round size |
| --- | --- | --- | --- |
| **Burger Tycoon** | `/burger_tycoon` | Endless tycoon, 8 claimable plots, 4 players per plot | 24 |
| **Capture The Flag** | `/capture_the_flag` | First to 3 captures, then a shuffle vote | 16 |
| **Fortress Team 2** | `/fortress_team_2` | Payload push, teams swap each round, first to 3 round wins | 24 |

When a world's instance fills up the host opens another one, so the browser can
legitimately read "2 instances — 30 players" for a world whose round size is
24.

### Burger Tycoon
Claim one of eight plots, then grow a flat plate into a burger empire: floor,
grill, counter, walls, fry station, roof, neon sign, second grill, seating,
drive-thru, walk-in freezer, second floor, rooftop garden and finally the
Golden Arches. Idle machines drip coins into your plot's bank; the fry station
and freezer are hands-on (stand there and press **E**). Walk over the green
collector pad to bank the coins. Plot coins are a scratch currency that never
touches your site credits. When the last member of a crew leaves, the plot
resets to bare ground and the next player to arrive starts fresh.

### Capture The Flag
Crossroads-style: two stone forts across a green valley, a central arch, four
hill outposts and two wooden bridges. Grab the enemy flag, run it back to your
own (which must be at home), first to three wins. Killing a carrier drops the
flag; touching your own dropped flag returns it.

### Fortress Team 2
Dustworks: a desert payload map. Blue pushes the bomb cart along the rails
toward Red's pit; stand near it to move it, stand near it as Red to block it.
Three checkpoints add time and lock the cart's rollback. Teams swap ends after
each round, and the match ends at three round wins.

---

## Controls

| Key | Action |
| --- | --- |
| `W A S D` | Move |
| `Space` | Jump |
| `Shift` | Walk slowly |
| Mouse | Look; left button fires |
| Right mouse | Scope, or use the held item; anything else falls through to `E` |
| `1`–`5` | Hotbar slots |
| `R` | Reload |
| `E` | Interact (tycoon buttons, machines, plot claiming) |
| `G` | Toggle first / third person |
| `Y` | Chat &nbsp;&nbsp; `U` Team chat |
| `Tab` | Scoreboard |
| `Esc` | Pause menu → controls, display, quit |

Every one of those keys is rebindable, from **Controls** in the pause menu:
click a key, press the one you want, and it takes effect immediately. A key
can only do one job, so taking it from something else leaves that action
unbound (and saying so, rather than showing a blank). `Esc` while a row is
listening cancels the rebind, and **Reset key bindings** puts the whole set
back without touching anything else.

**Key bindings and aim settings live on the account**, not in the browser:
sensitivity, field of view, invert-Y, raw input and every binding follow the
player to any machine they sign in from. The pause menu's other screen —
render scale, view distance, particles, names, volume — stays per-device,
because a phone and a gaming desktop have no business sharing a render scale.
The account copy is on the page before the first frame, `localStorage` shadows
it so a dropped connection never loses a binding, and the Controls header says
plainly whether the last change reached the account.

Only what the player actually changed is stored, so a later change to a
default still reaches everybody who has never touched that particular row.
Everything posted back is validated server-side — unknown actions dropped, key
codes checked, numbers clamped to the range the sliders offer.

While the chat box is open every other binding is ignored so you can type
freely. **Double-click a name** in chat or on the scoreboard to open that
player's profile in a new tab.

**One `Esc` opens the pause menu**, and one closes it again. The browser owns
`Esc` while the pointer is locked — it eats the key and frees the mouse itself
— so the game reads the unlock as the key press rather than waiting for a
second one. Whether an unlock was `Esc` or a tab-away is settled a beat later
from the window's focus: still focused means `Esc` and pauses, focus gone means
the window went away and the round carries on. Resuming takes the mouse back
even though the browser refuses a fresh lock for about a second after `Esc`,
retrying until it lands and falling back to the "click to take the mouse back"
hint if it never does.

Loading a world takes the browser fullscreen and quitting hands it back exactly
as it was found. Alt-Tab, the Windows key and a click on another monitor
release the mouse without pausing the round — **only `Esc` pauses**. Quit
returns you to whichever page you launched from.

**One live game session per account.** Pressing Play in a second window pulls
the first one out of whatever it was in *before* the new connection is allowed
to join, so the same character can never be in two rounds at once. The web
server signals every host over a signed loopback control channel when it hands
out a join ticket, and the host the new socket lands on enforces the same rule
again locally, so a race between two windows pointed at the same world ends the
same way. The window that loses says so plainly rather than looking like a
dropped connection.

---

## Architecture

```
main.py                    entry point: seeds the DB, starts the web server and
                           supervises one game-host process per world
app/
  config.py                ports, tunables, secrets
  security.py              PBKDF2 passwords, HMAC tickets, CSRF, input cleaning
  db.py                    SQLite (WAL) with a thread-local connection pool
  bootstrap.py             idempotent first-run seeding + catalogue sync
  webapp.py                routing, sessions, CSRF, websocket backend resolver
  console.py               the live terminal read-out (traffic, worlds, hosts)
  http/
    server.py              threaded HTTP/1.1 server + websocket reverse proxy
    router.py              Request/Response and the pattern router
    templating.py          a small compiling template engine
  models/
    catalog.py             THE item catalogue (hats, faces, clothing, weapons,
                           tiers and Unusual particle effects)
    users.py avatars.py inventory.py economy.py market.py worlds.py
    events.py              the weekly home-page spotlight rotation
  social/
    friends.py follows.py posts.py comments.py messages.py feed.py
  views/                   one module per area of the site
  game/
    supervisor.py          spawns/restarts the per-world host processes
    host.py                a game host: accepts proxied websockets, runs ticks
    instance.py            the shared engine: players, movement validation,
                           hit detection, damage, chat, rounds, shuffle votes
    protocol.py            RFC 6455 websocket implementation
    registry.py            live host/instance stats for the website
    maps/                  builder.py + the three map generators
    worlds/                capture_the_flag.py fortress_team2.py burger_tycoon.py
static/
  js/engine/               WebGL renderer, geometry, textures, avatar rig,
                           particles, synthesised audio
  js/game/                 client, netcode, physics, HUD, settings
  js/ui/                   site behaviour, 3D thumbnails, per-page scripts
  css/                     site.css (Web 1.0 chrome, light + dark palettes and
                           the phone layout) and game.css (HUD)
  img/                     the topbar logo and the favicon
templates/                 server-rendered pages
tools/                     dev server helper, bot client, test suites
```

### Static assets

Every `/static` URL is rendered with a `?v=` stamp taken from the file's mtime
and size, and a stamped URL is served with a year of `immutable` caching. A
bare `/static` URL revalidates on every request instead (the ETag makes that a
304 with no body). That split is the point: without it a browser holds an asset
for as long as its `max-age` says and never asks again, so a phone that already
had the previous `site.js` kept running it against freshly rendered HTML — new
markup, old handlers, and buttons that quietly did nothing on one device while
working on another.

The topbar logo (`static/img/logo.png`) is the brand artwork lifted off the
black background it was delivered on. Because that artwork was composited on
black, every edge pixel of it is `alpha * colour`: colour-keying the black
would have left the darkened ring the anti-aliasing baked in, and dropping
dark pixels would have eaten the navy outline the wordmark is drawn with. So
the backdrop was found by flooding in from the borders — which cannot reach
the dark navy inside the logo — and the whole edge band was un-matted against
the artwork it belongs to, taking alpha from how much of that colour survived
and colour from the artwork itself. It is delivered at 720px wide for a ~190px
slot, and the bar is sized by padding around it rather than by a fixed height.

### Processes and ports

Everything the network sees is on **one port (8972)**. Internally:

```
browser ──HTTP──▶ web server (main process, port 8972)
        └─WS────▶ web server ──raw TCP──▶ game host process (127.0.0.1:899x)
```

The web server validates your session, mints a short-lived HMAC-signed join
ticket containing your avatar, and then reverse-proxies the websocket byte for
byte into the world's host process. Each world therefore simulates on its own
CPU core, and a busy match cannot slow the website down. Hosts push a heartbeat
(instances, players, kills, visits) back to the web server every 2.5 seconds,
and the supervisor restarts any host that dies.

### Server authority

* **Credits, items and inventory.** Clients send intents ("buy `hat_crown`"),
  never values. Prices come from the server-side catalogue, the Unusual roll
  happens on the server, and the charge plus the grant happen in one SQLite
  transaction with an append-only ledger.
* **Equipping.** Every slot change is checked against the inventory row's owner
  and the item's slot, so a forged request cannot wear something you do not
  own.
* **Movement.** The client simulates its own character for responsiveness, but
  the server caps distance per tick, rejects impossible climbs, snaps back
  players that never touch the ground, and its copy of your position is the one
  everybody else — and every hit test — sees.
* **Shooting.** Fire rate, ammunition, range, spread and line-of-sight are all
  resolved server-side from the server's own copy of the world.
* **Admin actions** run through exactly the same code paths (`economy.adjust`,
  `inventory.grant`) as normal play, so the dashboard cannot create state the
  game itself could not.

---

## Items, tiers and Unusuals

The catalogue lives in `app/models/catalog.py` and is mirrored into the
database on boot — adding a hat is one dict and a restart.

* **Normal** — yellow. Every item ships this way.
* **Unusual** — purple, with a permanent particle effect. Rolled at **0.5% on
  hat purchases only**. Eleven effects ship: Burning Flames, Scorching Flames,
  Starstruck, Void Mist, Frostbite, Circuitry, Bubbly, Ember Storm, Sunbeam,
  Toxic Haze and Static Charge.

Effects render on the hat in every world and on every avatar preview across the
site. Each owned copy of an item is its own database row, so an Unusual is a
specific copy with a serial number — not a flag on an item type.

## Avatars

Six independently colourable body parts (head, torso, both arms, both legs),
plus `face`, `hat`, `shirt`, `pants` and `back` cosmetic slots and five
**usable** hotbar slots. One rig drives the profile preview, the editor, the
market thumbnails and the game itself, so anything added to the catalogue shows
up everywhere at once.

Both builds are made the same way: rounded boxes rather than hard cubes — a
short neck, a tapered torso, softened limbs and feet — so a bare default
character has a silhouette instead of reading as a stack of blocks. The torso
segments overlap by more than their own bevels, which is what stops the joins
showing as grooves; the arms are rectangular in section rather than square
posts; and the head is wider than it is tall, sat down on the shoulders.

**Two body types** ship: `male`, the broader one, and `female`, the slighter
one — narrow shoulders, a real waist, hips back out to shoulder width and
slimmer, slightly longer limbs. The editor draws them as two buttons side by
side, each a figure at that build's proportions above its name.

**The female build has its own head**, in the same language as the male one —
a single rounded box, the same bevel in world units, the same flat face plate
— drawn to its own proportions: 1.34 across rather than 1.46, no wider than it
is deep, and slightly taller than it is wide (1.06:1 against 1.14:1), which is
most of what takes the blockiness out of it. Below 55% of its height the bake
pinches to 85% of its width, so the face narrows to a small round chin instead
of ending in the same square it started as.

That jaw is part of the head rather than a piece stuck under it: `roundedBox`
takes an optional taper and pinches the bake itself, so there is one surface,
one colour and one decal, with no seam across the chin. The pinch is confined
to the lower half, which leaves the crown — the part a hat actually sits on —
at full width. UVs stay on the undeformed grid, so a face decal still lands
square on the front and simply narrows with the surface it is printed on,
which is what a mouth on a tapered jaw should do; the normals are re-derived
from the pinch rather than estimated from the moved triangles, so the shading
across the jaw is exact.

The hat anchor at the top of the head, the eye height and the hitbox are
identical on both, which is what guarantees every hat, face, shirt, pair of
trousers and back item fits either with no per-type variant. Nothing in the
catalogue is tighter than 1.50 across, so every hat clears the narrower skull
too, and the face plate stays wide enough that the widest eyes in the
catalogue still sit on dead-flat, front-facing surface. Switching build in
the avatar editor never costs you an outfit. Cosmetics that colour the body —
shirt torsos and sleeves, trouser legs, cuffs and stripes — are driven from the
build's own measurements, so they follow whichever silhouette is in use.

**The female build walks differently.** On the male rig the limbs swing from a
trunk that stays put. On the female rig the pelvis is an animated part in its
own right: it slides across to sit over whichever leg is carrying the weight,
lifts on the side the swinging leg hangs from, and turns with the stride while
the shoulders turn against it. The feet track a little closer to the centre
line than the hips are wide and roll very slightly inwards; the arms swing less
and hang a touch further from the body; and the whole thing carries a smaller
vertical bounce. The idle is a held contrapposto that breathes rather than a
body swaying between two feet.

Every one of those is a small number on purpose. The gait was first authored
for a figure with a much wider hip than the build now uses, and at that size it
read as a catwalk rather than as walking; the pelvis channels are half what
they were, and the stance barely narrows at all, because these legs already
stand close together. Every field is an offset applied at build time, so
nothing about the geometry, the anchors or the hitbox moves and the same
animation runs safely on a character wearing anything in the catalogue.

`Avatar.pose` is a pure function of the animation state, so a character
changing state would otherwise snap from one pose to the next on a single
frame. Callers that can keep one object per character — the game client, for
every player it draws, and the live previews — run it through
`Avatar.smoothPose` instead. It is a cross-fade rather than a filter on the
output: while a change is in flight both states are evaluated at the live clock
and mixed over about a sixth of a second, so a steady walk or run comes through
exactly as authored — no lag, no damping — and only the crossing is smoothed.
Changing build resets it (`Avatar.resetPose`), because crossing between two
gaits on two different bodies is not a transition, it is a cut.

## Appearance and privacy

A dark theme ships alongside the light one. It is a second hand-built palette
rather than an inversion — the chrome keeps its bevels and gradient headers,
lit from a night sky instead of a white one.

The toggle is a sun that becomes a moon, and the moon shows **the phase
actually in the sky tonight** — a crescent on a crescent night, a full disc on
a full one. It is built the way the sky builds it: half the disc lit, half in
shadow, and an ellipse across the middle whose width is how far the terminator
has swung. Hovering it names the phase and how much of it is lit.

The choice is remembered in three independent places: on the account (so a
phone and a desktop signed in together agree), in a cookie (so the server can
stamp the right theme onto the first byte of HTML — no white flash — and so a
signed-out visitor keeps their choice) and in `localStorage` (so it survives a
browser that refuses cookies). Losing any one of them does not lose the
setting, and none of them lives in the server's memory, so restarting the
process changes nothing. `auto` follows the operating system, and choosing it
clears the cookie rather than pinning the browser to a stale choice.

The profile editor (`/profile-editor`) carries the description, three **pinned
items** that sit at the top of the profile, and per-field privacy: who can see
the friends list, the inventory, the deaths/K-D record, the server you are
currently in, when you are online, and who can leave profile comments. Every
setting is enforced on the server, including on the direct `/inventory/<name>`
URL.

Pinning is a drag: pull a piece out of your inventory into one of the three
slots, drop one on top of another to swap them, or drag a pinned item back down
to unpin it. It is driven by pointer events, so the identical gesture works
with a mouse, a trackpad and a finger, and a plain click still pins and unpins.

Pinned items are the one deliberate exception to the inventory privacy setting.
Pinning something is the owner saying "look at this", so the three pins stay on
the profile even when the rest of the collection is set to friends-only or
private — the strip, the counts and the `/inventory/<name>` page are still
gated. An Unusual in a pinned slot runs its effect live rather than as a still,
scaled to the piece it is sitting on, and so does the item preview you get by
clicking any item tile.

---

## The rest of the site

* **The friends panel on a profile** shows the first eight and folds the rest
  away behind one Expand button, which is centred on its own line so it lands
  under the thumb on a phone. The whole list is in the markup and the fold is
  only applied once the script has run, so a reader without JavaScript gets
  everything rather than a button that does nothing.
* **The hotbar is a drag**, the same gesture and the same ghost as the pinned
  items: pull an item out of the pool into one of the five seats, drop one seat
  on another to swap them, or drag a seat back down into the pool to empty it.
  Clicking still works exactly as it did. The Avatar Editor's cosmetic slots
  stay a click, because a hat either is or is not on your head and there is
  only one place it can go.
* **Home.** The weekly spotlight banner is a greeting rather than furniture: it
  is claimed once per sign-in and then stays gone until the next one, so
  reloading the page (or coming back to it from a profile) does not re-serve
  it. On a phone the side column runs profile → friend requests → who is
  online → an inbox button → your friends, because reaching people is what the
  phone layout is for.
* **The news strip** carries new sign-ups alongside the Unusual pulls and the
  notable finds, and scrolls slowly enough to read a headline on the way past.
  Hovering parks it.
* **People** (`/users`) is a "who has just arrived" board rather than a
  directory: newest accounts first, capped at sixty, with the join date on
  every card.
* **The floating messenger** is two screens behind one bubble — the
  conversation list, and a direct-message view that slides in over it. Writing
  a note never costs you the page you were reading, and Back walks you straight
  out of the conversation. The "To" box has the same type-ahead the compose
  page does. A switch in `/settings` turns the whole bubble off; it is on by
  default. On a phone, opening a conversation raises the window — a list of
  names reads fine in a short box and a conversation does not — and closing it
  puts the box back. Both are capped by what is actually on screen rather than
  by `vh`, because a phone keyboard does not resize the window: it covers the
  bottom of it, and a `position: fixed` bubble stays happily underneath.
  `visualViewport` is the only thing that knows, so its height and its offset
  drive the panel's size and lift, and the conversation stays pinned to its
  last message as the keyboard comes and goes.
* **Character previews keep their own sky** in both themes — the profile
  preview, the welcome character and every avatar thumbnail in the friends,
  people and message lists. The rig is lit for a dark background, so an avatar
  that changed colour with the theme toggle read as a rendering fault rather
  than as a theme. It is a lifted slate rather than near-black, so a
  dark-haired or dark-clothed character still has something to stand against.
* **An ordinary item tile has a grey rim.** An Unusual announces itself with a
  purple edge and a glint, so a Normal needs an edge of its own — most visible
  in the light theme, where the old hairline all but disappeared.
* **Compose** (`/messages/compose`) remembers where you came from and sends you
  back there — the profile, the home page, the inbox, wherever it was.
* **Removing a friend** asks first, in the page's own dialog. Cancelling a
  request you sent still goes straight through, because that one has no cost.
* **The welcome screen** shows one character rather than a shelf of them, and
  that character is alive: it poses, it changes its whole outfit every few
  seconds (or on demand), and it can be dragged around. Every look is rolled
  out of the live catalogue with the same 3D rig the profile and the game use,
  so a hat added to the catalogue can turn up on the front page the same day.

## The admin dashboard

`/admin-dashboard` has two tabs. **Overview** is the live numbers: worlds,
instances, host processes, player management, the credit ledger and the audit
log, refreshed every three seconds.

**Connections** is the same data drawn as a graph — every account as a node,
every friendship, pending request and follow as an edge. It is a plain 2D
canvas running a force-directed layout: connected nodes repel and their edges
pull like springs, while accounts with no connections at all are seated on a
slowly turning ring just outside the cluster. That last part matters — left in
the same simulation the unconnected accounts have nothing pulling them
anywhere, so they drift into a wide halo that the auto-fit then has to hold,
squeezing the part of the graph anybody reads into a corner.

**Auto-fit** keeps every node in frame as accounts arrive and links form: it
eases the view onto the graph's bounds, at the same pace whatever the frame
rate, and fits around the floating toolbar, key, totals and node card rather
than parking nodes underneath them. Panning or zooming switches it off (the
button dims with it); **Recentre** is a one-off glide back that leaves the
switch where you set it. Node size is the friend count and node colour is the
account's state (administrator, in a world, online, registered, unconnected);
clicking one pins it and lists who it reaches. It rides the dashboard's own
three-second heartbeat and merges each refresh into the layout already on
screen rather than restarting the simulation, and the key, the names and the
unconnected accounts can each be toggled off.

On a phone the Connections tab is a whole screen away from the numbers, so
**Show connection map** on the Overview panel folds the same live graph in at
the bottom of the dashboard instead.

## Development tools

```bash
tools/devserver.sh start --port 8972    # start/stop/restart/log helper
tools/sitetests.py                      # HTTP-level tests for the website
tools/checkmaps.py                      # static map validation
tools/simclient.py --world capture_the_flag --bots 4 --seconds 20
tools/gametests.py                      # full gameplay test suite
tools/gametests.py ctf combat tycoon    # or a subset
```

`BLOCKHAVEN_TYCOON_COINS=200000 python3 main.py` starts every Burger Tycoon
crew with a large float, which is handy when you want to look at a finished
restaurant without building one first.

`gametests.py` drives real websocket clients against the running servers and
asserts on what the servers broadcast: flag captures, damage and the kill feed,
fire-rate clamping, movement correction, cart pushing, tycoon buying and
income, instance overflow, visit accounting and the end-of-round shuffle vote.

## Data

Everything lives in `data/blockhaven.sqlite3` (WAL mode). Delete it, or run
with `--reset`, to start over. `data/secret.key` holds the HMAC secret used for
sessions and join tickets.
