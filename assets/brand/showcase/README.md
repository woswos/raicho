# Raicho brand showcase

Editable brand compositions, interface concepts, and ready-to-use PNG exports.
The pages load the existing production SVG logos and local Geologica WOFF2.
They require no build step, remote font service, or network API.

## Preview

From the repository root, serve the brand directory locally:

```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory assets/brand
```

Open [the identity board](http://127.0.0.1:8765/showcase/identity_board.html).
The page navigation also opens the inbox concept and launch compositions.

| Source | Purpose |
| --- | --- |
| [identity_board.html](identity_board.html) | Current visual identity with production artwork and Geologica |
| [inbox.html](inbox.html) | Interactive light/dark inbox concept with mobile layout |
| [launch.html](launch.html) | Editable layouts for the four launch exports |
| [Writing guide](../voice.md) | Tagline, product description, and draft interface copy |

The inbox contains fictional messages. Theme, density, search, folder selection,
reading, starring, and archiving operate on sample data in memory. Reply and
compose open a preview dialog; no mail is sent. Reloading resets the demo.
The mobile folder picker keeps all five folders available.

## Exports

| Image | Dimensions |
| --- | --- |
| [Identity board](../previews/identity-board.png) | 1440 px wide |
| [Light inbox](../previews/inbox-light.png) | 1440 × 836 px |
| [Dark inbox](../previews/inbox-dark.png) | 1440 × 836 px |
| [Mobile inbox](../previews/inbox-mobile.png) | 366 × 800 px |
| [Symbol size proof](../previews/symbol-legibility.png) | 1280 × 710 px |
| [Repository social preview](../social/repository-card.png) | 1280 × 640 px |
| [README banner](../social/readme-banner.png) | 1600 × 440 px |
| [Project introduction](../social/announcement.png) | 1200 × 900 px |
| [Square avatar](../social/avatar.png) | 1024 × 1024 px |

The launch source uses fixed-size artboards scaled to fit the preview page.
For a new export, capture the named artboard at scale 1 after the local font and
images finish loading. The element IDs are `repository-card`, `readme-banner`,
`announcement`, and `brand-avatar`. The board and inbox use `identity-board`
and `mail-app`. Export the inbox first, then the identity board: the board embeds
both inbox PNGs.

## Design decisions

- Original bird paths and Geologica 580 with `ss01` remain the identity masters.
- Neutral interface surfaces leave the message content in focus.
- Vermilion appears on the compose action and selected-message marker.
- Dark text on vermilion preserves readable button labels; normal body text uses
  neutral surfaces. Theme colors are prototype values, not new core brand colors.
- Black and white one-color marks use transparent cutouts. At 16–24 px, expect
  silhouette recognition; use 32–48 px for more visible detail.

These are design concepts, not a shipped email client. The earlier generated
identity board remains preserved in `references/` as a historical source.
