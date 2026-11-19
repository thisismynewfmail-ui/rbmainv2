"""Family accounts: parents, the children they create, and the dashboard.

A **parent** is a separate kind of account.  It lives in its own table
(``family_parents``), signs in on its own page with its own cookie
(``config.FAMILY_COOKIE``), and is never a player: it has no avatar, no
inventory, no profile, and it never appears in search, the news strip, the
friend graph or anywhere else on the player side of the site.  The only way
one is made is the onboarding page, ``/parent-signup``.

A **child** is an ordinary player account (a ``users`` row, so it plays,
dresses up and makes friends exactly like anybody else) with a row in
``family_children`` tying it to the parent who created it.  That link is the
one thing this package guards hardest: it is never rendered, returned or
hinted at anywhere but the owning parent's own pages.  To every other player
-- and to every public page and API -- a child account is just a player.

    store.py      the tables, created alongside the rest of the schema
    shield.py     Safe Chat: personal-information and outside-contact filter
                  (pure functions; the game hosts import it too)
    controls.py   the parental controls: defaults by age, validation, labels
    accounts.py   parent accounts and parent sessions
    children.py   creating, listing and managing child accounts, plus the
                  in-memory directory every enforcement check reads
    guard.py      the enforcement hooks the rest of the site calls -- a
                  set lookup and out for every account that is not a child
    activity.py   play-time metering from the game hosts' heartbeats: daily
                  totals, sessions, the limit and quiet-hours kicks
    insights.py   everything the dashboard shows, assembled per child
    views.py      the pages and the JSON API
"""
