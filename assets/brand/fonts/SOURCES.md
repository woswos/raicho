# Geologica font sources

[Geologica on Google Fonts](https://fonts.google.com/specimen/Geologica) is
the Raicho wordmark and supporting typeface. The wordmark uses weight 580,
stylistic set 1 (`ss01`, the single-storey “a”), default kerning, and no added
tracking. The `CRSV`, `SHRP`, and `slnt` axes are all set to 0.

The TTF and license are unmodified downloads from the official
[Google Fonts collection](https://github.com/google/fonts), pinned to commit
`9710da1eacb3be272583c3224dcb70f9da6eadbb`. Only the TTF's local filename
has changed; its internal font names are unchanged.

| Local file | Source |
| --- | --- |
| `Geologica-Variable.ttf` | [Google Fonts TTF](https://raw.githubusercontent.com/google/fonts/9710da1eacb3be272583c3224dcb70f9da6eadbb/ofl/geologica/Geologica%5BCRSV%2CSHRP%2Cslnt%2Cwght%5D.ttf) |
| `Geologica-Variable.woff2` | Locally converted from the TTF above; see below |
| `OFL.txt` | [Google Fonts license](https://raw.githubusercontent.com/google/fonts/9710da1eacb3be272583c3224dcb70f9da6eadbb/ofl/geologica/OFL.txt) |

[Google Fonts metadata](https://raw.githubusercontent.com/google/fonts/9710da1eacb3be272583c3224dcb70f9da6eadbb/ofl/geologica/METADATA.pb)
credits Monokrom, Sindre Bremnes, and Frode Helland.

## Web font conversion

The full WOFF2 was locally repackaged from the pinned TTF using fontTools
4.63.0 and Brotli 1.2.0, at quality 11 in FONT mode. No glyphs were subsetted
and no variable axes were removed. Encoding used `recalcTimestamp=False`
and `WOFF2FlavorData(transformedTables=set())`. The font contains 973 glyphs.

Decoding verified that all 19 non-`head` tables are byte-identical to the
TTF, including glyph outlines, variations, positioning, and substitutions.
The `head` table changes are limited to checksum adjustment and the
lossless-compression flag (bit 11). This WOFF2 is a local conversion, not an
unchanged download from Google's web font CDN.

## SHA-256

```text
9124d9e88ac6c11d761f35241713a51d68e2c4ebedce0edaca834717a00959ec  Geologica-Variable.ttf
4ef62ab86a2e85c10f154a754d7763da9eba767f3e4b89710d5c37bf0c5edbb2  Geologica-Variable.woff2
778186245840aea0e60bec6a46e7fb1442e0cd78e41afeadffcd3e8824b379e0  OFL.txt
```

## Use and licensing

| Axis | Range | Raicho wordmark |
| --- | --- | --- |
| Weight (`wght`) | 100–900 | 580 |
| Cursive (`CRSV`) | 0–1 | 0 |
| Sharpness (`SHRP`) | 0–100 | 0 |
| Slant (`slnt`) | −12–0 | 0 |

Enable `ss01` to obtain the selected single-storey “a”. `fonts.css` loads
the WOFF2 for upright browser use and enables that feature by default.
The TTF is supplied for design tools. Production wordmark SVGs contain
outlines extracted from this font, with OpenType shaping applied.

The supplied license states: Copyright 2020 The Geologisk Project Authors
(https://github.com/monokromskriftforlag/geologisk). Its historical project
name is preserved exactly in `OFL.txt`.

The fonts are distributed under the SIL Open Font License 1.1. Include
`OFL.txt` when redistributing them. The supplied license declares no Reserved
Font Names. The font license does not require logos or documents created
with the font to use the OFL.
