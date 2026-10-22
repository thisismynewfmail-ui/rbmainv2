# The fifteen arena worlds -- design

Fifteen new servers sit beside Last Light and Blackout Relay. Each one is a
world of its own: its own entry in `app/models/worlds.py`, its own game-host
process (the supervisor starts one per world, and the host opens a new
instance whenever the last one fills), its own card on the home page and in
the world browser, its own page with its places, roles and badges, and its
own subtab in the Bots Zone.

Every world is built from **four places** (areas). A round is played in one
of them; after the world's set number of rounds there, the server shuffles to
another at random, and arriving somewhere new plays that place's own arrival
sequence over the game. The end of a round that moves on shows the world's
own transition -- a storm warning, a curtain, a train -- and a reel of the
places that lands on the next one. Only the place being played is ever sent
to a client.

They share one engine, `app/game/arena/`:

| Piece | File | What it gives every world |
| --- | --- | --- |
| Rounds, areas, the shuffle | `arena/base.py` | setup -> active -> results -> next round; N rounds per place, then a random new place; per-area payloads; round twists |
| Spawning | `arena/base.py` | per-area, per-team (or per-role) spawn rooms; elimination worlds spectate until the next round |
| Hold-E channels | `arena/base.py` | hacking, digging, cracking, freeing: hold E in range, with a bar |
| Loadouts | `arena/base.py` | a world can hand out its own weapons (dodgeballs, paint blasters, knives) and give your own back afterwards |
| Entities | `arena/entities.py` | carts on tracks, pickups, NPCs, zones -- drawn by the client from the snapshot |
| Map kit | `arena/kit.py` | the Last Light area kit plus team spawn rooms, tracks, ladders, platforms and props |
| Bots | `arena/bots.py` | a plan per world on top of the shared brain: objective play by persona |
| Sleeping rounds | `bots/dormant.py` (`arena` mode) | rounds, area shuffles and team scores advanced in closed form |
| Client | `static/js/game/arena.js` | HUD, results card, reel, roles, entity drawing, spectating; a plugin per world |
| Arrivals | `static/js/game/arena_intro.js` | a scene per place, a transition per world |
| Thumbnails | `static/js/ui/world_thumbs.js` | a diorama per world and per place; players in the classic yellow, red and blue |

---

## 1. Cataclysm -- survive the disaster

*Free for all, no fighting. 24 players.*

**Loop.** Twenty seconds of calm to find somewhere safe (the forecast on the
HUD hints at what is coming), then a disaster for 60-80 seconds, getting
worse as it goes. Everyone still standing scores, and survival streaks pay
more each time. The dead watch until the next round. Three disasters per
place, then the town is evacuated to another. From the third round a place
can throw two disasters at once (**Double Trouble**).

**Disasters.** Flash Flood (water rises; get high), Tsunami (a wall of water
sweeps across from the sea), Meteor Shower (telegraphed impacts; roofs
protect), Tornado (a roaming vortex that pulls and throws; get indoors),
Acid Rain (anywhere with sky over it burns), Lightning Storm (strikes where
you stand, more often up high), Earthquake (tremors that throw you about and
drop debris near buildings), Blizzard (body heat drains outdoors; huddle by
fires or get inside), Sandstorm (gusts and grit outdoors), Eruption (lava
climbs from the crater; lava bombs). Each place has its own five.

**Shoves.** Weapons do no damage here, but any hit shoves -- pushing a
friend off the lighthouse is half the fun of the genre.

**Places.**
* **Breezy Point Harbour** -- a fishing village on stilts, the lighthouse,
  the hill chapel and its water tower. Tsunami, flood, lightning, tornado,
  meteors.
* **Mount Ashfall** -- a terraced village on a live volcano: the observatory,
  rope bridges over the lava river, the old mine. Eruption, meteors,
  earthquake, acid rain, lightning.
* **Dustbowl Ranch** -- barn, silo, windmill, farmhouse, cornfield and the
  storm cellar. Tornado, sandstorm, lightning, flood, acid rain.
* **Glasstown Downtown** -- an office tower you can climb, the mall, a parking
  garage and the subway. Earthquake, meteors, acid rain, blizzard, lightning.

**Bots.** Read the forecast and the disaster like a person: climb for floods
and tsunamis (the highest ground within reach), get under a roof for acid
rain, lightning and meteors, run from the tornado and into buildings, huddle
at fires in a blizzard, keep moving in a quake. Panicky personas run about,
chaotic ones shove people, explorers climb the tallest thing for the view.

**Badges.** Disaster Survivor (disasters survived), Unbroken (best survival
streak), Weathered Every Storm (each kind survived -- derived), Last One
Standing (sole survivor), Storm Chaser (survived a tornado up close), Pushy
(shoves landed).

---

## 2. Prop Panic -- prop hunt

*Props against Hunters. 20 players.*

**Loop.** Thirty seconds of hiding while the Hunters wait blindfolded in the
cage; then three minutes of hunting. Props press **E** on any prop to become
one (a teapot, a teddy, a cannonball pile...), and can **taunt** for points or
drop a **decoy**. Hunters shoot what they think is a person: hitting a real
prop scenery piece costs the Hunter health, finding a person heals them. In
the last minute the props squeak every twenty seconds. Teams swap every round;
two rounds per place (everyone hunts once).

**Places.** Grandma Willow's Cottage (kitchen, parlour, bedrooms, attic,
greenhouse, garden gnomes), Toybox Emporium (aisles, plush wall, train set,
stockroom), Brine & Barnacle Maritime Museum (ship hall, cannon gallery,
aquarium, gift shop), FreshCo Supermarket (aisles, produce, freezers,
loading dock, car park). Each has a dozen-plus kinds of prop placed many
times over, so a careful prop has somewhere to blend in.

**Bots.** Props pick something common in the room, settle beside its
siblings at their angle, and hold still; they move when a hunter is far
away and bolt when shot. Hunters sweep rooms, and shoot props that moved in
view, props in odd places, or (now and then) a hunch.

**Badges.** Master of Disguise (rounds survived as a prop), Eagle Eye (props
found), Squeaky Toy (taunts), Decoy Artist (decoys shot by hunters),
Untouched (survived a round without a scratch), Clean Sweep (hunted down the
whole team).

---

## 3. Rail Rumble -- payload race

*Red against Blue, a cart each. 24 players.*

**Loop.** Both teams push their own cart along their own track towards the
finish; standing by your cart moves it (faster with up to three), an enemy
beside it stops it. Along each track are **junction levers**: pull one (hold
E) to send that track's cart round its long detour loop for a while -- the
other team's, obviously. **Coal hoppers** let a pusher stoke the cart for a
burst of speed. First cart home wins; when the clock runs out, the further
one does. Two races per place.

**Places.** Gold Gulch Canyon (mesas, a trestle bridge both tracks cross, the
saloon town), Frostbite Pass (rock tunnels, the frozen lake, avalanche sheds),
Sunken Temple (temple steps, rope bridges, the waterfall), Ironworks Foundry
(molten channels, cranes, catwalks). Tracks are point-mirrored, so neither
side has the shorter run.

**Bots.** Pushers ride the cart and stoke it; flankers hunt the enemy's
pushers; switchers go for the levers when the enemy cart nears a junction and
put their own straight again.

**Badges.** Conductor (distance pushed), Switchman (junctions thrown),
Stoker (boosts), Derailer (enemy pushers knocked out), Photo Finish (wins
with the other cart within a tenth of the track), Railroad Champion (wins).

---

## 4. Convoy -- payload travel

*Escort against Ambush, a journey across three places. 24 players.*

**Loop.** The Escort team drives the armoured convoy across a route of three
legs -- three of the four places, in a random order every match. Each leg the
convoy rolls in through the west gate and has to reach the east gate; on the
way there is a **roadblock** the Escort must breach (hold E on its
generator) and two checkpoints that add time. Reach the gate and the
convoy rolls on: everybody moves to the next place with the convoy (the leg
transition). The Ambush wins by holding any leg until its clock runs out.
Then the teams swap and a new route is drawn.

**Places.** Canal Market Quarter (canals, bridges and market stalls),
Redrock Highway (gas station, motel, the overpass), Pinecrest Pass
(switchbacks, the dam, the lumber mill), Neon Boulevard (holo billboards,
monorail pillars, plazas).

**Bots.** Escorts ride the convoy and push forward to clear the next corner;
breachers make for the roadblock; ambushers set up ahead of the convoy and
pull back as it passes, and rush it when it is contested.

**Badges.** Wheelman (distance escorted), Breacher (roadblocks breached),
Highwayman (legs held by the Ambush), Long Haul (full journeys delivered),
Roadkill (escorts knocked out near the convoy), Convoy Champion (wins).

---

## 5. Midnight Mystery -- murder mystery

*One Murderer, one Sheriff, everyone else innocent. 18 players.*

**Loop.** Roles are dealt in secret. The **Murderer** has a knife (one hit,
and a thrown knife on a cooldown); the **Sheriff** has a revolver (one
shot -- shoot an innocent and you both go down, and the gun drops for anyone
to pick up); **Innocents** collect the coins scattered about and try not to
be alone. The Murderer wins by getting everybody; everyone else wins if the
Murderer falls or the clock runs out. Three rounds per place.

**Places.** Ravenhurst Manor (grand hall, library, ballroom, wine cellar and
the secret passage), Hotel Marigold (lobby, pool deck, corridors, the roof
bar), Snowpine Station (the stopped luxury train, carriage by carriage, and
its platforms), Carnevale Nocturne (tents, the carousel, the hall of mirrors,
the haunted ride).

**Bots.** Innocents gather coins and keep to company, remember who they saw
kill and say so; the Sheriff shoots on what it has actually seen; the
Murderer stalks the ones who wander off, keeps the knife away while watched,
and throws at the Sheriff when it has to.

**Badges.** Detective (Murderers stopped), Perfect Crime (wins as the
Murderer), Coin Collector (coins), Survivor (rounds survived as innocent),
Unlikely Hero (picked up the gun and stopped the Murderer), Silent Blade
(kills nobody saw).

---

## 6. Grand Heist -- cops and robbers

*Robbers against Cops. 24 players.*

**Loop.** Robbers crack vaults (hold E; a cop's taser interrupts), grab loot
bags (one at a time, and they slow you) and run them to the getaway. Cops
taser robbers (a stunned robber hit again is cuffed and sent to the cell);
a free robber can spring the cell (hold E at the switch), or a cuffed one
waits out the bail timer. Robbers win at the take target, Cops by running
out the clock or cuffing the whole crew at once. Nobody dies -- it is
stuns, cuffs and jailbreaks. Teams swap; two rounds per place.

**Places.** First Blockhaven Bank (vault level, offices, roof helipad),
Royal Flush Casino (gaming floor, cashier cage, penthouse, garage),
Crown Jewel Tower (jewel house, armouries, battlements, the river boat),
Gold Express Railyard (the gold train, signal towers, warehouses).

**Bots.** Crackers go for vaults in pairs (one watches), runners carry bags,
the brave spring the cell; cops patrol vaults, chase bag carriers first, and
camp the getaway when the take is close.

**Badges.** Safecracker (vaults cracked), Getaway Driver (bags delivered),
Long Arm of the Law (arrests), Jailbreaker (cells sprung), Big Score (wins
as Robbers), Thin Blue Line (wins as Cops).

---

## 7. Splat Turf -- paint the ground

*Pink against Teal. 16 players.*

**Loop.** Three minutes to paint as much of the floor your colour as you can
with the **Splat Blaster**, the **Roller** and the **Lobber**. Ink is your
ammo and refills fast standing in your own colour; enemy ink slows you.
Splatting an enemy sends them back to spawn. The last thirty seconds are a
**Splat Rush** (double spread). Coverage at the horn decides it. Two rounds
per place.

**Places.** Rad Ramps Skatepark (bowls, stepped ramps, rails), Coral Commons
Aquarium (the tunnel, tank halls, the plaza pools), Rooftop Gardens (rooftops
joined by bridges, greenhouses), Gumdrop Works (conveyor lines, vats,
catwalks).

**Bots.** Painters sweep unpainted and enemy ground, fighters push into enemy
paint and splat, and everybody heads home to refill when dry.

**Badges.** Turf Painter (cells painted), Splatter (splats), Team Colours
(wins), Last-Second Painter (painting in a Splat Rush), Inked Out (cells
painted in one round, best -- max), Roller Coaster (roller splats).

---

## 8. Bonk Brawl -- knock them off

*Free for all on floating arenas. 16 players.*

**Loop.** Every hit raises the victim's **bonk %**, and the higher it is the
further the next hit throws them. Knock people off the edge; three stocks
each, last one with stocks wins, or most KOs when the clock runs out.
Power-ups spawn (Mega Bonk, Feather, Bubble Shield) and jump pads throw you
across the gaps. Three rounds per place.

**Places.** Cloudtop Temple (marble islands in the sky), Magma Forge
(platforms over lava, flame vents that throw), Big Top Circus (rings,
trampolines, the cannon), Junkyard Asteroid (space junk in low gravity).

**Bots.** Brawlers pick the highest-% target near an edge and hit them
outward; careful ones keep to the middle of a platform and recover onto the
nearest one; everybody grabs power-ups.

**Badges.** Bonker (knock-outs), Home Run (a KO from 200%+), Last Stock
Standing (wins), Comeback Kid (won on your last stock), Power Player
(power-ups), Airtime (jump pads).

---

## 9. Bastion -- tower defence

*Everyone together against the machines. 16 players.*

**Loop.** Waves of robots march along the paths to the core. Kill them for
scrap, spend scrap on turret pads (Gatling, Cannon, Frost, Tesla; upgrade
twice), and keep the core alive. Every fifth wave brings a Siege Mech.
Leaked robots damage the core; when it falls the sector is lost and the next
try starts over; hold to wave 15 and the sector is secured. Two tries (or a
win) per place.

**Places.** Meadow Crossing (one long road, two bridges), Redstone Canyon
(two paths that merge), Frostfall Outpost (a frozen lake path), Neon Grid (a
glowing circuit, three lanes).

**Bots.** Builders keep the pads filled and upgraded where the path bends,
gunners hold the chokepoints, and somebody always runs to the core when it is
hit.

**Badges.** Scrapper (robots destroyed), Architect (turrets built),
Unbreachable (best wave held -- max), Mech Breaker (siege mechs), Sector
Secured (sectors held to the end), Repair Crew (core repairs).

---

## 10. Dodgeball Showdown

*Two teams on a court. 16 players.*

**Loop.** Balls sit on the centre line at the whistle: rush for them. Hit an
opponent and they are out to the bench; **catch** a ball thrown at you
(right mouse or E as it arrives) and the thrower is out and a teammate comes
back on. Step over the centre line and you are out. Last team with anybody on
court wins. Twists: Big Balls, Fast Balls, Low Gravity. Two rounds per place.

**Places.** Northfield High Gym, Sunny Shores Beach, Orbital Station Zero (low
gravity), Castle Courtyard.

**Bots.** Rush the line, throw at the nearest open target, back up to dodge,
and catch when a ball comes straight at them (skill decides how often).

**Badges.** Sharp Arm (hits), Butterfingers No More (catches), Comeback
(teammates brought back), Last One Standing, Dodgeball Champion (wins),
Line Judge (opponents out for crossing the line... caused by a throw).

---

## 11. Bomb Bash -- hot potato

*Free for all elimination. 20 players.*

**Loop.** A countdown, then a quarter of the players are handed a ticking
bomb. Tag somebody (a hit at arm's length) to pass it on; the bomb carrier is
faster. When the fuse runs out, whoever holds it is out. New bombs go to the
survivors until one is left. Power-ups: Sneakers, Bubble, Short Fuse
(for whoever you tag). Three rounds per place.

**Places.** Jungle Gym Playground, Rooftop Runway, Arcade Mania, Pirate Cove
Deck.

**Bots.** Carriers chase the nearest runner (and never the one who just
passed it); runners keep away from carriers, using the climbing frames and
the rigging.

**Badges.** Hot Potato (passes), Fuse Dodger (rounds survived), Last Spark
(wins), Close Call (passed with under two seconds), Boomer (eliminated while
holding -- for laughs), Sprinter (sneakers).

---

## 12. Plunder Cove -- treasure race

*Two pirate crews. 20 players.*

**Loop.** X marks appear about the island: dig one up (hold E), carry the
chest back to your ship's hold (slowly; it drops if you go down). Wooden
chests are worth one, silver two, gold three. Raid the other ship's hold to
steal. Each ship has two cannons on deck that crew can fire at the beach.
First to fifteen, or the richer crew when the clock runs out. Two rounds per
place.

**Places.** Skull Rock Cove, Palm Lagoon, Shipwreck Reef, Smoking Isle.

**Bots.** Diggers head for the nearest mark, carriers go straight home with
an escort, raiders slip aboard the enemy ship, gunners man the cannons when
chests are being carried across the beach.

**Badges.** Treasure Hunter (chests dug), Deckhand (chests delivered), Sea
Wolf (chests stolen), Cannoneer (cannon hits), Pirate King (wins), Gold Fever
(golden chests).

---

## 13. Storm Circle -- battle royale

*Free for all. 24 players.*

**Loop.** Everybody drops in from the sky, floats down and loots supply
crates (armour, medkits, a power weapon for the rest of the round). The storm
closes in five phases on a random point; outside it you burn, harder each
phase. Last one standing wins. Two rounds per place.

**Places.** Pinewood Isle, Copper Mesa, Shattered City, Glacier Bay.

**Bots.** Land somewhere quiet or somewhere hot by persona, loot, move inside
the circle early (careful ones) or late (greedy ones), and fight what they
meet.

**Badges.** Storm Survivor (rounds won), Eliminator (eliminations), Looter
(crates), Into the Eye (top five finishes), Edge Runner (survived outside the
storm for a while), Drop Zone (eliminations within the first minute).

---

## 14. Flee the Beast -- one against many

*One Beast, everybody else running. 16 players.*

**Loop.** Survivors hack computers (hold E; a missed beat alarms the Beast)
until the exits power up; then hold an exit open and get out. The Beast
hits a survivor down and drags them to a freezer pod; a pod holds you for
sixty seconds unless a friend frees you. Lockers hide you (the Beast can
check them). Survivors win if anybody escapes; the Beast wins if everyone is
frozen. Three rounds per place, a new Beast every round.

**Places.** Hollowbrook Facility, Ashgrove Academy, Abyssal Station,
Undercroft Sewers.

**Bots.** Survivors hack in pairs, run from the Beast's footsteps, hide when
cornered and free pods when it is away; the Beast patrols computers, chases
whoever alarmed one, and checks lockers.

**Badges.** Hacker (computers), Escape Artist (escapes), Rescuer (pods
freed), Apex Beast (wins as the Beast), Freezer Burn (survivors frozen),
Hide and Seek (survived a locker check).

---

## 15. Tycoon Wars -- build, earn, raid

*Four companies. 24 players.*

**Loop.** Each team owns a plot. Droppers make product, conveyors carry it to
the bank, and buttons buy the next machine (more droppers, upgraders, laser
gates that hurt intruders, auto turrets, the Mega Drill). The ore field in the
middle can be mined by hand and carried home for a bonus. Raid an enemy
vault (hold E) to take a tenth of their bank. Eight-minute seasons; highest
net worth wins. Then the economy moves to another biome.

**Places.** Goldvein Mines, Sugarloaf Candy Co., Timberline Lumber, Oasis Oil
Fields.

**Bots.** Builders buy in order and keep the bank collected, miners run ore,
guards stay home when raiders are about, raiders hit the richest vault.

**Badges.** Tycoon (net worth earned), Industrialist (machines bought), Vault
Raider (raids), Prospector (ore mined), Market Leader (season wins), Security
Chief (raiders stopped at home).

---

## Rules every world follows

* **Distinct servers.** One host process per world, instances opened on
  demand, sleeping bot rounds per world, and a card of its own everywhere
  worlds are listed.
* **Spawning.** Every place has its own spawn room per team or role, checked
  for room and floor by `tools/mapcheck.py`; pickups, NPCs and objectives are
  placed per place and reset when the place changes.
* **Geometry.** Every place passes `tools/mapcheck.py`: no z-fighting, no
  decor over voids, no floating lights, no walk-through clutter, spawns clear,
  and every objective reachable from the spawn rooms.
* **Bots.** Every world has a plan on top of the shared brain, driven by the
  same persona tags, with its own settings in the Bots Zone and its own live
  view there, its own speech events, and a sleeping-round model.
