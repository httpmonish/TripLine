# Tripline Brand Guidelines & Asset Documentation

## Concept
A "T" made of two core forensic concepts:
- **The horizontal bar**: The boundary (the line an AI agent's action must not cross).
- **The red stroke above it**: The proposed action, stopped short before crossing the line.
- **The stem below**: A receipt with a torn edge representing the cryptographic proof that is left behind.
- **The red dot on the first 'i' in the wordmark**: Echoes the stopped action.

## Palette
- **Ink**: `#0F1115`
- **Paper**: `#FFFFFF`
- **Accent (Decisions & Stopped Action only)**: `#E5484D`

## Typography & Licensing
- **Wordmark Font**: Inter Display SemiBold by Rasmus Andersson.
- **License**: SIL Open Font License 1.1 (see [`OFL.txt`](./OFL.txt)).
- The wordmark in all SVG files is converted to outlines; no runtime font installation or remote font download is needed.

## File Manifest
| Filename | Type | Dimensions | Intended Usage |
|---|---|---|---|
| `tripline-mark-dark.svg` | SVG | Vector | App icon mark on dark backgrounds |
| `tripline-mark-light.svg` | SVG | Vector | App icon mark on light backgrounds |
| `tripline-mark-bare.svg` | SVG | Vector | Unframed mark for custom containers |
| `tripline-lockup-on-dark.svg` | SVG | Vector | Full lockup (mark + wordmark) on dark surfaces |
| `tripline-lockup-on-light.svg` | SVG | Vector | Full lockup (mark + wordmark) on light surfaces |
| `tripline-favicon.svg` | SVG | Vector | Modern browser vector favicon |
| `tripline-mark-512.png` | PNG | 512×512 | High-res raster icon / PWA manifest |
| `tripline-favicon-32.png` | PNG | 32×32 | Standard browser raster favicon |
| `tripline-apple-touch-180.png` | PNG | 180×180 | Apple touch icon for mobile home screens |
| `tripline-lockup-on-dark.png` | PNG | Raster | Fallback lockup on dark background |
| `tripline-lockup-on-light.png` | PNG | Raster | Fallback lockup on light background |
| `social-preview-1280x640.png` | PNG | 1280×640 | OpenGraph / social preview card |

## Usage Rules & Restrictions
1. **Clear Space**: Always maintain clear space around the mark equal to or greater than the height of the red stroke.
2. **Minimum Sizes**:
   - **Mark only**: Minimum 16px height / width.
   - **Full Lockup**: Minimum 120px width.
3. **No Alterations**:
   - Do NOT recolour, stretch, rotate, crop, or redraw the mark or lockup.
   - Do NOT recolour the red accent stroke (`#E5484D`).
   - Do NOT apply drop shadows, 3D skews, or blur filters to the logo assets.
4. **Offline Integrity**: All assets are served locally from disk (`/public` or `/static/brand/`). Zero CDN or external network requests.
