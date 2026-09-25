"""Synthetic players ("bots").

A bot is an ordinary account -- a ``users`` row with ``is_bot = 1``, a
profile, an avatar, an inventory, friends and a wall -- driven by a persona.
The package is split by job:

``config``      the schema-driven settings the Bots Zone edits
``personas``    persona tags, the traits they imply, and the prompt text
``names``       procedural usernames and the rules every name must satisfy
``storage``     each bot's folder: account.json and one log per conversation
``llm``         the language-model client, probe, queue and budget
``template``    a sandboxed renderer for the model's own chat template
``prompts``     system messages, persona blocks and context culling
``factory``     the creation pipeline and the background jobs that run it
``dormant``     the abstract ("asleep") model of a world instance
``social``      friendships, wall comments, posts and direct messages
``director``    the runtime that decides who is online, where and doing what

Nothing a bot does goes around the platform's own rules: a bot's comment is a
row in ``profile_comments``, its friendship a row in ``friendships``, its game
a seat in a real instance whenever a person is there to see it.
"""
