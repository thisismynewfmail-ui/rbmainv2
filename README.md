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
  `/fortress_team_2`, `/blackout_relay`).

Around both runs an optional population of **synthetic players** — accounts
with personas that log in on a daily curve, make friends, comment, answer
messages and play the worlds alongside real people, written by any
OpenAI-compatible language model, and cheap enough to keep a hundred thousand
of them online: a round with nobody real in it costs nothing. See
[Bots](#bots).

No frameworks, no build step, no `pip install`, no asset files. Every texture,
sound, mesh and map is generated at runtime.

```
./run.sh
```

Then open **http://<your-ip>/** on any machine on your network — it serves on
port 80, so there is no port to type. Install a certificate and the same
command serves **HTTPS on 443** with port 80 redirecting to it, reading the
site's name out of the certificate — no flags, see
[HTTPS](#https). The site works on a phone; the Game View needs a desktop
browser (pointer lock, a keyboard and a mouse), so its Load buttons are hidden
on small screens.

---

## Quick start

```bash
./run.sh                        # website + all three game hosts, HTTPS if a
                                #   certificate is installed, else port 80
./run.sh --tls-check            # which certificate is in use, and why not
./run.sh --domain example.com   # name the site explicitly
./run.sh --self-signed          # HTTPS with a throwaway certificate
./run.sh --no-https             # plain HTTP only
./run.sh --port 8972 --no-https # unprivileged: no sudo needed
./run.sh --no-games             # website only
./run.sh --no-bots              # leave the synthetic players offline
./run.sh --reset                # wipe the database and re-seed
./run.sh --debug                # verbose tracebacks, no static caching
./run.sh --status-interval 8    # slow the terminal read-out down (0 = off)

python3 tools/install_cert.py mysite-ssl-bundle.zip   # install a certificate
```

80 and 443 are privileged, so `run.sh` re-runs itself under sudo when it needs
to and then drops back to your account once the sockets are bound.

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
| `admin_system` | see `app/config.py` | Administrator. Can open `/admin-dashboard`. Owns two Unusual hats. |
| `admin_test` | see `app/config.py` | Ordinary player used to demonstrate the Unusual system (Unusual Propeller Beanie + Unusual Mohawk Spikes). |
| `builderman_x`, `RetroKid2007`, `BlockSmith`, `NoobSlayer99`, `PixelPatty`, `CartPusher`, `FlagRunner`, `GrillMaster` | see `app/bootstrap.py` | Demo players so the social features have something to show. |

Everyone else who registers starts with **2,000 Noogets**, a Basic Pistol, a
Basic Shotgun and a Basic Stick.

---

## The worlds

| World | URL | Mode | Round size |
| --- | --- | --- | --- |
| **Burger Tycoon** | `/burger_tycoon` | Endless tycoon, 8 claimable plots, 4 players per plot | 24 |
| **Capture The Flag** | `/capture_the_flag` | First to 3 captures, then a shuffle vote | 16 |
| **Fortress Team 2** | `/fortress_team_2` | Payload push, teams swap each round, first to 3 round wins | 24 |
| **Blackout Relay** | `/blackout_relay` | Capture the flag at dusk: a long valley, deploy waves, outpost lockdown, tunnels, overtime | 24 |

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
touches your site Noogets. When the last member of a crew leaves, the plot
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

### Blackout Relay
Ironvale Relay: a capture-the-flag valley at dusk, built around the concrete
relay station in the middle of it. It is a long map -- 904 by 400 units, with
roughly two hundred units of open country between the Relay and each keep --
and a flag run end to end takes about thirty-five seconds at a dead sprint.
First to five captures, or thirty minutes.

Both teams deploy from muster halls bolted onto the Relay -- red out of the
west doors, blue out of the east -- with a door onto your own half and a back
door into the atrium, so the middle of the building is the shortest way across
and the busiest room on the map. Between the Relay and each keep the road runs
through a town: a freight yard, a cutting spanned by a bridge you can fight on
top of or under, a fuel depot, pillboxes and bunkers covering the lanes, and
tree cover on the flanks for anyone going round. Each compound has three ways
in: the gate off the road, a sally port on each flank, and the postern at the
back that the lane outside the wall leads to. A hatch behind each keep drops
into a tunnel that runs the length of the valley to the undercroft below the
Relay, surfacing inside all four bunkers, both pump houses and both cisterns on
the way.

Four rules of its own on top of ordinary capture the flag:

* **Muster waves.** The dead come back together on a five-second wave rather
  than trickling in one at a time (never sooner than two seconds after dying).
* **Outpost lockdown.** While your own flag is off its pedestal your team
  stops spawning at the Relay and spawns in the two bunkers on your half --
  right across the carrier's way home. Losing your flag moves you into the
  way rather than burying you; the counter is to take the bunkers first.
* **Overtime.** The clock cannot end a round while a flag is away from home.
* **Sudden death.** Level when the clock finally stops: both flags reset and
  the next capture wins, or three minutes later it is honours even.

A dropped flag falls where the carrier did -- the pole topples, the cloth
settles, and a disc on the ground drains over the forty-five seconds you have
to reach it before it goes home by itself. Only your own team's health shows
above their heads here; an enemy's name tag is a name and a colour, nothing
more.

Points go to the escort as well as the runner -- staying within thirty units
of your own carrier pays, as does killing an attacker near your own flag.

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
  bots/                    the synthetic players (see "Bots" below)
    director.py            presence, world choice, sleeping rounds, the clock
    dormant.py             a sleeping round as a closed-form model
    personas.py            the tag catalogue and the traits tags produce
    factory.py             bot creation: names, personas, profiles, history
    chatter.py gamechat.py friends, wall comments, posts, DMs, in-game replies
    llm.py template.py     the language-model client and chat-template renderer
    prompts.py names.py    prompt builders and the fallback name generator
    config.py storage.py   every setting, and each bot's folder of logs
  views/                   one module per area of the site
  game/
    supervisor.py          spawns/restarts the per-world host processes
    host.py                a game host: accepts proxied websockets, runs ticks
    instance.py            the shared engine: players, movement validation,
                           hit detection, damage, chat, rounds, shuffle votes
    protocol.py            RFC 6455 websocket implementation
    registry.py            live host/instance stats for the website
    maps/                  builder.py + the four map generators
    bots/                  nav.py (nav grid, flow fields, A*), brain.py (one
                           bot's senses and choices), runner.py (all bots in
                           a round: detail levels, objectives, chat)
    worlds/                capture_the_flag.py fortress_team2.py
                           burger_tycoon.py blackout_relay.py
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

Everything the network sees is on **the two ports a browser tries by
itself** — 80 and 443. Internally:

```
browser ──HTTPS─▶ web server :443 (TLS terminated here)
        └─WSS───▶ web server ──raw TCP──▶ game host process (127.0.0.1:899x)
browser ──HTTP──▶ web server :80  ──301──▶ https://…
game host ─HTTP─▶ web server :80 /internal/… (loopback only)
Let's Encrypt ──▶ web server :80 /.well-known/acme-challenge/… (plain, by design)
```

TLS is terminated in the web server itself, in the connection's own thread
rather than in the accept loop, so a client that opens a socket and then says
nothing costs one thread instead of holding up every other connection. That
the site and the game share a listener is what makes `wss://` work with no
second port and no second certificate: the upgrade arrives already decrypted
on the same socket the pages came from.

The plain listener has three jobs once TLS is up. It redirects everything to
HTTPS, keeping the path and query. It answers `/.well-known/acme-challenge/`
itself, because HTTP-01 validation will not follow a redirect and there is no
certificate to redirect to the first time anyway. And it accepts `/internal/`
from the loopback, which is how the game hosts report in — they talk plain
HTTP to 127.0.0.1 and never leave the machine.

Cookies pick up `Secure` automatically as soon as TLS is listening, so the
session token cannot travel in clear. `Strict-Transport-Security` is opt-in
(`--hsts`): a browser that has seen it refuses plain HTTP for the whole
max-age, which is unpleasant if a certificate later lapses.

### HTTPS

There are two ways to have a certificate and the server takes either one
without being told which. Nothing needs a flag: `certs/` and
`/etc/letsencrypt/live/` are both searched on every start, and the name the
site answers to is read out of the certificate that wins, so `--domain` is a
convenience rather than a requirement.

**A. You already have one**, from your registrar or your host. Porkbun,
Namecheap, cPanel and ZeroSSL all hand out a zip; they all name the files
differently. Install it once:

```
python3 tools/install_cert.py ~/Downloads/example.com-ssl-bundle.zip
sudo ./run.sh
```

Copying the zip up to the server and installing it from where it landed works
the same way — `python3 tools/install_cert.py certs/mybundle.zip`. The archive
is read rather than moved, and leaving it in `certs/` afterwards does not
confuse the search: archives are skipped, so the certificate that gets served
is the installed one. It does still hold a copy of your private key, so delete
it once HTTPS is up.

The installer takes the zip, the folder it was unpacked into, or the files
themselves (`--cert`/`--key`). It works out which file is the certificate and
which is the private key by reading them rather than by their names — so
`public.key.pem`, which ships in most bundles and is not a private key, is not
mistaken for one — assembles the chain if the intermediates came in a separate
file, puts it leaf-first if the download did not, and refuses to install
anything expired, mismatched or issued for another name. The result lands in
`certs/` as `fullchain.pem` and `privkey.pem`, mode 600 on the key, with the
previous pair kept as `.1` so a bad renewal can be backed out.

**`certs/` is in `.gitignore` and must stay there.** A private key that has
ever been committed has to be reissued, even if the commit is deleted
afterwards.

**B. Let's Encrypt issues one here**, over port 80. The registrar does not
matter — only that the domain's A record points at the machine and that port
80 reaches it. Start the site, ask certbot while it runs, and restart:

```
sudo ./run.sh --domain example.com                  # :80 answers, no cert yet
sudo certbot certonly --webroot -w data/acme -d example.com
sudo ./run.sh                                       # now HTTPS on :443
```

The server serves the challenge from `data/acme` itself, so certbot needs no
web server of its own and renewals need nothing from you as long as port 80
stays open — the redirector answers `/.well-known/acme-challenge/` in plain
HTTP by design.

**When a browser still says "Not secure."** `./run.sh --tls-check` reads every
certificate it can find and says which one would be served, what each covers,
when it expires and why any of them were passed over. It binds nothing, so it
is safe to run against a live server:

```
$ ./run.sh --tls-check
Certificates found:
  certs/fullchain.pem
      source    bundle in certs
      covers    *.example.com, example.com
      expires   Dec 16 10:47:36 2026 GMT (88 days)
      chain     4 certificates
      verdict   usable

HTTPS will use certs/fullchain.pem
and the site will answer as https://example.com
```

The four things it catches are the four that are invisible until a visitor
hits them: a key that belongs to a different certificate, a chain that is
missing its intermediates or has them before the leaf (desktop browsers
paper over both by fetching the intermediate themselves — phones do not), a
certificate that has expired, and one that does not cover the name the site
is reached by. A wildcard is matched the way browsers match it, so
`*.example.com` covering `www` but not the apex is reported rather than
discovered in production.

`--self-signed` makes a throwaway certificate for local work, and `--no-https`
keeps the plain-HTTP behaviour.

**Privileges.** 80 and 443 need root to *bind*, not to serve. `run.sh`
re-runs itself under sudo when it has to, and then `--user` hands the server
back to the account that called sudo as soon as the sockets are open, so a bug
in a request handler is not a bug with root behind it. `--stay-root` turns that
off, and `--port 8972 --no-https` needs no privileges at all.

The web server validates your session, mints a short-lived HMAC-signed join
ticket containing your avatar, and then reverse-proxies the websocket byte for
byte into the world's host process. Each world therefore simulates on its own
CPU core, and a busy match cannot slow the website down. Hosts push a heartbeat
(instances, players, kills, visits) back to the web server every 2.5 seconds,
and the supervisor restarts any host that dies.

### Server authority

* **Noogets, items and inventory.** Clients send intents ("buy `hat_crown`"),
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

Seven independently colourable body parts (head, torso, hips, both arms, both
legs), plus `face`, `hair`, `hat`, `shirt`, `pants`, `belt` and `back` cosmetic
slots and five **usable** hotbar slots. One rig drives the profile preview, the
editor, the market thumbnails and the game itself, so anything added to the
catalogue shows up everywhere at once.

The **hips** are their own colour rather than borrowing the left leg's, which
is what they did before. Trousers still cover them exactly as they did, so the
colour is what shows when the trousers do not; an avatar saved before the hips
were colourable keeps the character it had, because a stored palette with no
hips entry falls back to its left leg on the way out.

**Hair** is the one cosmetic that has to fit the skull rather than sit on top
of it, and the two builds have different heads. So a style is authored in *head
units* — 1.0 is the head's own width, height and depth, the origin is the
middle of the head, +Z is the face — and the renderer scales it to whichever
head is wearing it. One style fits both builds with no per-type variant, and a
style added later needs no variant either. Nine ship, from a short crop to a
bob, and anyone can wear any of them.

A **belt** is a band round the waist with an optional buckle, so it is
described by colours and a width rather than by parts: the renderer sizes it
from whichever build is wearing it, the same way a shirt or a pair of trousers
is sized, which is what makes one belt fit both builds. It is drawn outside the
hips and rides the pelvis, so it sits over the trousers rather than instead of
them and turns and drops with the hips through the stride. `pouch` hangs two
pouches off the front of the band, `metal` and `glow` give the buckle its
material. Its market and inventory tiles draw the whole character but fit the
camera to the waist, which is what `frame` does in the thumbnail renderer.

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

### Textures

Every texture in the project is drawn at runtime on a 2D canvas into one
1280×1280 atlas, so the platform ships without a single image asset. A decal
normally lands on a part's own +Z face in object space, which is what keeps a
face on the front of a head and a graphic on the front of a shirt however the
character turns.

A part can instead ask for the decal to be **wrapped**, and then it is printed
over the whole surface through the mesh's own UVs. That is what carries a
pattern all the way round a cone, a cap or a can rather than leaving it a
sticker on one side: the birthday cone's stars, the beanie's knit, the candy
stripes, the fur, the camo on a pair of trousers. Wrapped patterns are painted
on transparency rather than on a background, so the shader mixes them over the
part's own colour and one `knit` serves a blue beanie and a red one — an item
stays described by its colours. They also tile horizontally, because U runs
0..1 once around a mesh and anything crossing that edge has to be drawn again
on the other side or there is a seam down the back of the hat.

Garments name their cloth with `weave`, which is printed over the whole
garment — the sleeves and the legs too, not just the chest. A part carries one
decal, so on a shirt the segment a graphic is printed on keeps the graphic and
the rest of the shirt carries the weave.

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

`/admin-dashboard` has three tabs. **Overview** is the live numbers: worlds,
instances, host processes, player management, the Nooget ledger and the audit
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
the bottom of the dashboard instead. Bots are drawn in violet on the graph and
carry a violet **bot** pill in the player table; real people keep the usual
colours, and when the graph has to be trimmed people are kept first.

**Bots Zone** is the control room for the synthetic players, described next.

## Bots

BLOCKHAVEN can fill itself with synthetic players. A bot is a real account
(`users.is_bot = 1`, with a row in `bot_profiles`): it has a name, an about-me,
a join date, an avatar and an inventory, friends, a comment wall, game stats
and a presence, and everywhere a player can see it, it looks like anyone else.
Only the admin dashboard and the terminal tell them apart.

### How 100,000 bots cost almost nothing

The whole design rests on one observation: **a round nobody real is watching
does not need to be simulated, only to be believable when somebody arrives.**
So there are two tiers.

- **The director** (`app/bots/director.py`) runs in the web process, once a
  second, and holds every bot's presence in flat arrays — state, world,
  instance, next wake-up, a handful of trait floats — rather than objects. Bots
  are woken by a timing wheel keyed by second, so a tick touches only the bots
  whose moment has come. It keeps the online count on the peak curve, picks a
  world and an instance for bots that want to play, and sends them home when
  their session ends. Measured on a desktop-class CPU:

  | Bots | Load (background thread) | Held in memory | Tick, steady state | Snapshot |
  | --- | --- | --- | --- | --- |
  | 100,000 | ~3 s | ~34 MB | ~0.5–3 ms | 6 MB |
  | 200,000 | ~6 s | ~100 MB | ~7 ms, worst ~70 ms | 12 MB |

  The loop runs once a second, so even 200,000 bots use under 1% of a core;
  a Raspberry Pi 3 is several times slower per core and still mostly idle.
  The site serves normally while the director loads (see `bottests.py
  scale`).
- **Sleeping rounds.** An instance holding only bots never reaches a game
  host. It lives in the director as a closed-form model (`dormant.py`): the
  flag captures, the cart's progress and round wins, the Burger Tycoon plots'
  income and upgrades all advance from elapsed time when anyone looks, not
  tick by tick. It shows in every player count, the world list, "Now Playing"
  and the world page's player list exactly like a live round, and its numbers
  move when bots leave or arrive — it just costs nothing.
- **Waking mid-round.** When a real player presses Join, the director picks
  the instance (it pulls people towards populated rounds), and if that round
  is asleep it is **hydrated** on the game host: the score, the timer, a flag
  already out, the cart part-way up the track, restaurants already built, and
  the bots spread across the map rather than stacked on a spawn. Once the last
  real player leaves, the round keeps running for `Sleep after` seconds (45 by
  default) and then goes back to sleep, bots and score included.
- **Live bots** (`app/game/bots/`) only exist in rounds with a real player.
  Each has a brain that perceives, keeps goals scored by utility and its
  persona, and moves on a nav grid built once per map (cached in
  `data/navcache/`) with flow fields to the objectives and a budgeted A* for
  everything else. Bots near a real player think at full rate and aim for
  real; bots far away think a few times a second and settle their fights by
  odds, so a busy round with 20 bots stays well inside the 20 Hz tick.
- **Bodies.** A person's movement is simulated in their own browser
  (`static/js/game/physics.js`): their box is moved one axis at a time
  against the map's solid parts, stepping up low ledges, landing on floors and
  bumping heads on ceilings. A bot has no browser, so `app/game/bots/body.py`
  is that same routine on the server, fed the solids the server already keeps
  for hit detection, and split into sub-steps short enough that a 20 Hz tick
  cannot carry a body through a thin floor or wall. Bots jump for a ledge the
  way a player does -- up the side, then over -- and one that falls short
  twice gives up on that way round. The nav graph only links a jump or a drop
  when there is headroom above the lower spot, so no path asks a bot to jump
  through a roof; a path always starts from the floor the bot is standing on
  (never the walkway above it); a chase aims at where the other player is
  standing rather than where they are mid-jump; and a bot steps round the rim
  of a shaft its path brushes instead of walking off it. The browser physics
  sub-steps the same way on a slow frame, so a long fall during a stutter
  cannot skip a floor either, and a spawn point with no room for a body (two
  of Fortress Team 2's forward spawns were inside a staircase) is moved to the
  nearest clear spot in the same room.

Nothing is written to the database per tick. Presence is written when a bot
logs in or out; game stats are written when a bot leaves a round; the
director snapshots itself to `data/bots/state.json` every few minutes so a
restart comes back mid-game instead of everyone logging in at once, and bots
whose time away ran out while the server was down drift back over a quarter
of an hour rather than in one burst.

On disk a bot costs what a player costs — about 3.5 KB, most of it the items
in its inventory — so 100,000 bots add roughly 360 MB to the database and
200,000 about 725 MB.

### Presence and the peak curve

The **Presence & Schedule** tab sets a daily curve: the share online at the
peak (90% by default), the share at the quietest hour, the peak window, how
long the ramp in and out takes, and a weekend boost. Each bot's own schedule
shifts that curve — night owls come on later, early birds earlier — and the
controller wakes whichever bots suit the moment. A bot that goes offline stays
away for a time drawn from `Offline for` (1–48 h), comes back for a session
from `Online session`, and after logging in waits `Online delay` (1–4 min)
before it joins a world or answers anyone. Messages sent to an offline bot
wait until it is online and past that delay.

### Personas

Every bot draws one tag from each core group — schedule, skill, focus, social,
voice — and a few extras (temper, weapon, age, favourite worlds, interests,
and your own custom tags). The tags *are* the bot: they set its traits, which
set when it plays, which worlds it queues for, how it fights and whether it
plays the objective, how often it goes off on a tangent or gets tilted, who it
befriends, how it types, and each tag's line goes into the persona block the
language model sees. The Personas tab shows every tag with how many bots carry
it and lets you weight how often new bots draw it.

Settings carry a scope badge so it is clear how each is applied:

| Badge | Meaning |
| --- | --- |
| Universal | one value for the whole platform |
| Per-bot range | each bot draws its own value from the range, nudged by its persona |
| Base × persona | the value is a baseline that each bot's tags raise or lower |

### Social behaviour

- **Friends.** Two bots need `Friend depth` shared tags (2 by default) before
  either sends a request; each bot aims for a friend count inside
  `Max friends`, social butterflies near the top and loners near the bottom.
  Candidates come from an inverted tag index, so finding them does not scan
  the population.
- **Chatter.** Online bots comment on the walls of bots they share tags with,
  each at its own pace inside `Comment interval` (1–5 h by default), reply
  when someone writes on their own wall, post status updates and like
  friends' posts. A global per-minute budget keeps the model free for chat.
- **Direct messages.** A bot answers DMs once it is online, after a
  human-looking delay -- shorter once the two of them are actually talking
  (see Dynamic Modifiers below).
- **In-game chat.** In a live round bots answer when they are spoken to or
  named, greet people who join, react to what happens in the round and to
  each other, and fire off quick reactions (a kill, a death) without the
  model. Every line they write has the round's state underneath it as
  background -- the score, where both flags are and who has them, the cart's
  progress and checkpoints, the clock, the restaurants, and the bot's own
  team, job and kills -- which it may bring up or not, the way a player knows
  the score without announcing it in every message.

### Dynamic Modifiers

Short-lived boosts that start when a conversation does and fade once it goes
quiet, each on its own switch on the **Dynamic Modifiers** subtab, which also
shows what is active right now.

| Modifier | What it does | Defaults |
| --- | --- | --- |
| Conversation momentum (DMs) | After two back-and-forths the bot's reply delay is cut by 30%, 10% more per further turn, never more than 70%. How quickly the person answered decides how much of it is left: straight back keeps all of it, a pause fades it, and after the decay time it is gone and the count starts again. A bot mid-conversation also puts off logging off. | 2 turns, 30% + 10%/turn, 70% max, 60 s decay |
| Chat heat (in-game) | Each of a player's recent lines adds 35% to the chance a bot answers them, fading over the decay time, up to +150%. The bot they were just talking with is favoured to answer again, and a hot chat can pull in a second voice. | +35%/line, +150% max, 60 s decay, 60% partner, 20% second voice |
| Bots answer each other | A bot's line can draw an answer from another bot (70% when it names them), each further bot-only line half as likely, and the exchange drops after three bot lines in a row until a real player speaks. | 22%, halving, 3 lines |

### Speech Events

Things that happen in a round are reported by the game host (from rounds a
real player is in, over the channel its chat already uses) and give the bots
there something to say. Each bot is told what happened *from its own side* --
"an enemy, Fox, just grabbed YOUR team's flag" for one team, "your teammate
Fox just grabbed the enemy flag" for the other -- and the side decides who is
likeliest to speak. The chance for each event is a slider on the **Speech
Events** subtab, grouped by world:

| Worlds | Events |
| --- | --- |
| Every world | someone joins, a killing spree (3/5/8/12), a spree ended |
| Capture The Flag, Blackout Relay, Fortress Team 2 | new round, a minute left, round over |
| Capture The Flag, Blackout Relay | flag stolen, carrier down, flag returned, capture |
| Blackout Relay | lockdown, overtime, sudden death |
| Fortress Team 2 | gates open, checkpoint reached, the final stretch |
| Burger Tycoon | restaurant claimed, a purchase (dearer ones are bigger news), restaurant finished |

Up to two bots react to one event, the same kind of event then waits out a
cooldown in that round, several notifications about one moment (the flag is
taken *and* the team is locked down) get one reaction, and the round stays
"buzzing" for a while afterwards -- bots are likelier to answer each other and
the players, so an event turns into a conversation. When the language model
is down, events fall back to short stock lines ("they have our flag", "nice
cap").

### The language model

Everything a bot writes comes from an OpenAI-compatible endpoint, by default
`http://10.0.0.139:5000/v1` (LM Studio, llama.cpp, TabbyAPI,
text-generation-webui, KoboldCpp, Ollama and vLLM all work). On start and on
**Probe** it asks the server everything it will say — the loaded model and its
context length, the sampling settings in force, the chat template, and a
tokenizer it uses to calibrate token counting — and applies them: the sampling
settings are sent with every request unless you override one on the Language
Model tab, and in completion mode the server's own chat template is rendered
locally (a sandboxed Jinja subset) so the prompt is exactly what the model was
trained on.

Every request is built the same way: the **system message** for that kind of
interaction (comment, wall reply, DM, in-game chat, post, usernames, profile;
all editable on the Prompts tab), then the bot's **persona block**, then the
content — the comment section, the conversation or the chat so far. The
context is capped at `Context limit` (16,000 tokens by default, or less if the
server's context is smaller) and culled oldest-first, for chats and comment
sections alike. Requests go through a priority queue with a rate limit and a
circuit breaker: in-game chat first, usernames and profiles last, and when the
endpoint is down the bots simply stay quiet and the creation pipeline falls
back to its built-in generators.

Each bot has its own folder, `data/bots/accounts/<shard>/<id>-<name>/`, with
`account.json` and a `logs/` directory holding one log per conversation —
`kikamu Comment Section`, `Chat Conversation With kikamu`,
`In-Game Chat In World Burger Tycoon`, `Status Posts` — and each request is
given the log for that bot and that conversation only. The dashboard's bot
drawer reads them.

### Creating bots

**Bot Creation** generates bots on demand (type a number, press Generate) or,
with its switch on, grows the population towards a target in the background.
Each bot is made in order: a name (the model is shown your example usernames
and asked for more; names that are taken are handed back to it as taken and
it is asked again, and after `Duplicate-name retries` the built-in generator
fills the gap rather than hang), then its persona and traits, a profile, an
inventory and outfit, a join date from the configured range, a play history in
proportion to its age, and friendships it would already have made. Each batch
is one database transaction.

### Bots Zone

The admin tab has a live header (every count, a chart of online and in-world
bots against the target curve, and a master switch), then one subtab per
area. **Bot Stats** lists every bot with its tags, state, world and round,
friends against its target, latest comment, K/D and when it will next change
what it is doing; clicking one opens a drawer with its persona, traits,
schedule, friends, comments, stats and its conversation logs, and buttons to
bring it online, send it to a world or offline, or delete it. The other tabs
each open with the feature's own switch, followed by that feature's settings;
**Dynamic Modifiers** and **Speech Events** also show what is live right now
(conversations with momentum, rounds with chat heat, the latest events and
who reacted). Every change applies live, with no restart.

The terminal read-out splits people from bots too: meters show people as `█`
and bots as `▓`, counts read `people+bots`, and a `bots` line shows online,
in-world and sleeping-round totals and the model's queue.

## Development tools

```bash
tools/devserver.sh start --port 8972 --no-https   # start/stop/restart/log
tools/sitetests.py                      # HTTP-level tests for the website
tools/sitetests.py --https              # ...the same suite over TLS
tools/checkmaps.py                      # static map validation
tools/checkeffects.py                   # Unusual effects vs the shapes that exist
tools/simclient.py --world capture_the_flag --bots 4 --seconds 20
tools/gametests.py                      # full gameplay test suite
BLOCKHAVEN_TLS=1 tools/gametests.py     # ...over HTTPS and wss://
tools/gametests.py ctf combat tycoon    # or a subset
tools/mapcheck.py                       # geometry QA for every map
tools/mapcheck.py ironvale              # ...or just one
tools/tlstests.py                       # certificate discovery and chain tests
tools/install_cert.py                   # with no arguments: check what is installed
tools/bottests.py                       # bot unit tests, headless rounds, scale
tools/bottests.py scale --bots 100000   # ...just the scale test, bigger
tools/mockllm.py --port 5055            # a stand-in language model endpoint
```

`bottests.py` needs no server and works in a throwaway data directory. The
unit group covers names, personas, the chat-template renderer and the
sleeping-round models; the chat group checks the Dynamic Modifiers (momentum
and its decay, chat heat, the bot-to-bot limit), each speech event from both
sides, the events and game state the host reports, and the chat relay end to
end with the language model stubbed out; the live group plays every world
headless on a simulated clock with bots and a stand-in real player and checks
that they move, fight, take objectives and wake mid-round, that no bot is ever
inside the map's geometry or needs rescuing from the void, and that ledge
jumps land on the ledge; the scale group creates
thousands of bots, loads them and times the director. `mockllm.py` answers
like a llama.cpp server (model list, `/props` with a chat template and
sampling, `/tokenize`, chat and completions); point the Language Model tab at
`http://127.0.0.1:5055/v1` to work without a real model, and use `--dupes` to
make it repeat taken usernames or `--fail` to make it unreliable.

`gametests.py` asserts exact outcomes in empty rounds — a flag captured, a
cart pushed — so run it against a server started with `--no-bots` (or
`BLOCKHAVEN_BOTS=0`); with bots on, they share the round and are entitled to
take the flag first.

`tools/tlstests.py` needs no server: it mints throwaway certificates with
openssl into a temporary directory and points the discovery code at them, so
the bundle layouts, the chain assembly and the refusals above are proved
rather than assumed. The rest of the test tools follow `BLOCKHAVEN_PORT`, so
they and the server agree by default. Both suites can be pointed at the encrypted listener, which is how
the TLS path gets exercised rather than assumed: `--https` for the site tests,
`BLOCKHAVEN_TLS=1` for the gameplay ones, which then drive real `wss://`
sockets through the same listener the pages come from.

`BLOCKHAVEN_TYCOON_COINS=200000 python3 main.py` starts every Burger Tycoon
crew with a large float, which is handy when you want to look at a finished
restaurant without building one first.

`gametests.py` drives real websocket clients against the running servers and
asserts on what the servers broadcast: flag captures, damage and the kill feed,
fire-rate clamping, movement correction, cart pushing, tycoon buying and
income, instance overflow, visit accounting and the end-of-round shuffle vote.

`mapcheck.py` needs no server; it builds each map and audits the geometry:

| Check | Catches |
| --- | --- |
| z-fighting | two surfaces on one plane, facing the same way, overlapping |
| decor over a void | paint, paths or plates that run off an edge or across a stairwell |
| lights in the air | neon that is not fixed to a ceiling, a wall or a step |
| walk-through clutter | anything without collision standing where a player can walk |
| loose decor | a decorative part touching nothing at all |
| mirror symmetry | a solid with no twin across the middle (maps that set `MIRROR_AXIS`) |
| spawns and markers | spawns inside walls, without clearance, or over holes |
| playfield | holes in the ground |
| routes | every objective reachable *and* leavable (skipped with `--fast`) |

Ironvale is held to all of them; the older maps are reported, not fixed.

## Data

Everything lives in `data/blockhaven.sqlite3` (WAL mode). Delete it, or run
with `--reset`, to start over. Bots add `data/bots/` (one folder of logs per
bot and the director's snapshot) and `data/navcache/` (nav grids, rebuilt
whenever a map changes). `data/secret.key` holds the HMAC secret used for
sessions and join tickets.
