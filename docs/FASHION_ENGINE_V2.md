# ASSTYLIST Fashion Engine v2.0.0

## Product thesis

v2 is not a generic "trend recommender". It treats fashion as a design problem:

`intent → cultural reference → silhouette → material → hero item → tension → complete look`

Popularity is a signal, not a verdict. A viral item with no design tension can lose to a quieter archival or reworked piece.

## September 2026 radar

The committed radar is dated `2026-09-16` and is intentionally refreshable.

### Core current signals

- Modern Craftsman
- Leather Weather
- Broken-down Prep
- Romantic Menswear
- Military Romance
- Archive Reconstruction
- Technical Romantic
- 90s Americana Recut
- Accessory-first Styling
- Dusty Pink Accent
- Sport Couture
- Neo-Gothic Editorial
- Post-punk Archive
- Minimal Precision

### De-emphasised as generic

`old money`, `quiet luxury`, generic `gorpcore`, logo-heavy hypewear and other broad internet formulas remain searchable for compatibility, but v2 does not let them dominate a high-niche recommendation without strong silhouette/material/cultural evidence.

## Social signal model

The radar accepts signals from four independent surfaces:

- TikTok — velocity and emerging vocabulary.
- Pinterest — intentional search behavior and long-tail aesthetic discovery.
- Instagram — editorial/stylist/designer adoption and visual language.
- Reddit — community friction, fatigue with formulas and long-form style discussion.

A production refresh should use compliant APIs, exports or licensed datasets. Do not make unrestricted scraping a hard dependency.

## Avito search v2

Avito remains the marketplace source. The engine now treats a listing URL as the primary identity, not `brand::name`, so two sellers can surface the same model at different prices/conditions.

The existing Avito provider already supports:

- RU query translation and fashion vocabulary expansion;
- title > description relevance weighting;
- material, color, size, condition and photo signals;
- live listing validation;
- short negative cache and temporary block backoff;
- HTML cards → JSON-LD → Next.js fallback parsing;
- snapshot fallback for environments where Avito blocks the runtime.

The v2 layer adds niche/current-fashion ranking above those listing signals.

## Scoring philosophy

The v2 score increases the contribution of:

- uniqueness;
- construction and silhouette;
- cultural/editorial relevance;
- niche factor;
- current fashion relevance;
- interesting trend signal.

Generic-factor penalties become stronger as the user's niche level rises.

## Refresh protocol

Refresh `trend_radar_v2.py` on a regular cadence. Keep the radar dated. A style should not become "permanent" simply because it was once viral.

Recommended pipeline:

1. collect platform signals;
2. normalise vocabulary;
3. deduplicate aesthetic synonyms;
4. score velocity + cross-platform corroboration + niche value;
5. decay stale signals;
6. update hero-item vocabulary;
7. run outfit regression tests;
8. publish a dated radar snapshot.
