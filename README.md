# Community Orchive

A parody of [Community Archive](https://www.community-archive.org/): Warhammer orcs and goblins
as if they posted on Twitter. Not part of Community Archive or Games Workshop.

Live at https://community-orchive.vercel.app. Every post is in one file anyone can build on:
https://community-orchive.vercel.app/orchive.json

## Add yer own git

1. Write one file, `data/<handle>.json`. The format is on the site under "Da API"; the site's
   "Show me 'ow" button gives a starting file.
2. Open a pull request. A check runs on every pull request and says what is wrong.
3. Once it is merged, the site rebuilds with your account in it.

One account per file. Posts are 280 characters at most. Replies point at `handle/id`. Keep it
about orcs and goblins. What you contribute is public domain (CC0).

Nothing reaches the site until a maintainer has read it and merged it. The orcs are rude about
stunties, pointy-ears and each other. Slurs,
real-world politics, real people and anything hateful are closed without merging.

## How it is built

`python3 build.py` checks every file in `data/`, then writes `orchive.json` (the whole set) and
`index.html` (one self-contained page). `python3 -m unittest` checks the data, the page and
that bad files are refused. No dependencies.
