---
name: ToyCad Hackathon
colors:
  surface: '#131313'
  surface-dim: '#131313'
  surface-bright: '#3a3939'
  surface-container-lowest: '#0e0e0e'
  surface-container-low: '#1c1b1b'
  surface-container: '#201f1f'
  surface-container-high: '#2a2a2a'
  surface-container-highest: '#353534'
  on-surface: '#e5e2e1'
  on-surface-variant: '#cdc7ac'
  inverse-surface: '#e5e2e1'
  inverse-on-surface: '#313030'
  outline: '#969179'
  outline-variant: '#4a4733'
  surface-tint: '#dbc90a'
  primary: '#ffffff'
  on-primary: '#363100'
  primary-container: '#f9e534'
  on-primary-container: '#706500'
  inverse-primary: '#695f00'
  secondary: '#ffffff'
  on-secondary: '#283500'
  secondary-container: '#c3f400'
  on-secondary-container: '#556d00'
  tertiary: '#ffffff'
  on-tertiary: '#2f3131'
  tertiary-container: '#e2e2e2'
  on-tertiary-container: '#636565'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#f9e534'
  primary-fixed-dim: '#dbc90a'
  on-primary-fixed: '#201c00'
  on-primary-fixed-variant: '#4f4800'
  secondary-fixed: '#c3f400'
  secondary-fixed-dim: '#abd600'
  on-secondary-fixed: '#161e00'
  on-secondary-fixed-variant: '#3c4d00'
  tertiary-fixed: '#e2e2e2'
  tertiary-fixed-dim: '#c6c6c7'
  on-tertiary-fixed: '#1a1c1c'
  on-tertiary-fixed-variant: '#454747'
  background: '#131313'
  on-background: '#e5e2e1'
  surface-variant: '#353534'
typography:
  headline-xl:
    fontFamily: Plus Jakarta Sans
    fontSize: 48px
    fontWeight: '800'
    lineHeight: '1.1'
    letterSpacing: -0.04em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '700'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 28px
    fontWeight: '700'
    lineHeight: '1.2'
  body-md:
    fontFamily: Hanken Grotesk
    fontSize: 16px
    fontWeight: '500'
    lineHeight: '1.6'
  label-sm:
    fontFamily: Space Grotesk
    fontSize: 12px
    fontWeight: '600'
    lineHeight: '1'
    letterSpacing: 0.05em
rounded:
  sm: 0.5rem
  DEFAULT: 1rem
  md: 1.5rem
  lg: 2rem
  xl: 3rem
  full: 9999px
spacing:
  base: 8px
  xs: 4px
  sm: 12px
  md: 24px
  lg: 48px
  xl: 64px
  gutter: 20px
  margin-mobile: 16px
  margin-desktop: 40px
---

## Brand & Style

The design system is built for a high-energy, creative hackathon environment focused on 3D modeling and toy design. The brand personality is **exuberant, tactile, and professional-yet-playful**. It targets a demographic of creators, developers, and designers who appreciate high-fidelity aesthetics and a sense of "digital physicalness."

The visual style merges **Glassmorphism** with **Neo-Brutalism**. It utilizes the depth and transparency of glass surfaces against the structure of heavy borders and vibrant, high-contrast colors. The interface should feel like a premium physical toolset that has been digitized—squishy, bold, and incredibly satisfying to interact with.

- **Emotional Response:** Creative confidence, excitement, and tactile satisfaction.
- **Visual Motif:** 3D rendered assets, thick strokes, and soft-frosted glass layers.

## Colors

The palette is anchored by a **deep obsidian black** (`#0F0F0F`) background, which allows the vibrant neon accents to pop with maximum intensity. 

- **Primary (Electric Yellow):** Used for primary calls to action and key brand highlights.
- **Secondary (Acid Green):** Used for success states, secondary actions, and high-energy decorative elements.
- **Neutral (Obsidian & Soft White):** Obsidian provides the canvas, while Soft White is used for primary body text and high-contrast surfaces.
- **Glass Accents:** Surfaces utilize a semi-transparent white tint with high backdrop-blur values to create depth without clutter.

## Typography

Typography is clean but carries high character through variable weights and geometric shapes. **Plus Jakarta Sans** provides a friendly yet bold headline voice. **Hanken Grotesk** maintains high legibility for body content with a modern, technical feel. **Space Grotesk** is used for labels and technical data to reinforce the "CAD" and "Hackathon" identity.

Tight letter-spacing on headlines ensures a compact, punchy look that complements the thick borders and rounded shapes of the UI.

## Layout & Spacing

The design system utilizes a **fluid grid** with generous internal padding to create a "breathable" but dense aesthetic. 

- **Desktop:** 12-column grid with a 1200px max-width container.
- **Mobile:** Single column with 16px side margins and a focus on vertical stackability.
- **Rhythm:** An 8px linear scale guides all spacing decisions. Large sections should be separated by `lg` (48px) units to maintain the bold, oversized feel of the brand.

Containers should often use "Full Width" or "Inset" logic depending on whether they are glass surfaces (Inset) or primary background sections (Full Width).

## Elevation & Depth

This system avoids traditional soft dropshadows. Instead, it uses **stacked tonal layers** and **backdrop blurs** to define hierarchy.

1.  **Level 0 (Base):** Obsidian black background.
2.  **Level 1 (Surface):** Dark grey surfaces (`#1A1A1A`) with 2px solid borders (`#262626`).
3.  **Level 2 (Glass):** Semi-transparent white (`rgba(255,255,255,0.08)`) with a 20px - 40px Backdrop Blur.
4.  **Level 3 (Pop):** High-saturation primary colors (Yellow/Green) for elements that need immediate attention.

Interactive elements should feel "pushed" or "raised" using 2px - 4px solid offsets (hard shadows) rather than diffused ones, creating a tactile, toy-like appearance.

## Shapes

The shape language is **hyper-rounded**. Following the "Toy" aspect of the brand, sharp corners are strictly forbidden. 

- **Primary Containers:** Minimum 32px border radius.
- **Buttons:** Always pill-shaped (fully rounded).
- **Icons:** Encapsulated in rounded-square or circular containers.
- **Stroke:** A consistent 2px or 3px border width should be applied to all discrete UI elements to provide a structural, "blueprint" feel.

## Components

### Buttons
Buttons are high-contrast, pill-shaped elements. 
- **Primary:** Bold Yellow background with Black text. 3px solid black border.
- **Secondary:** Acid Green background with Black text.
- **Ghost:** Glass surface with a 2px white border and white text.

### Cards
Cards use the "Level 1" or "Level 2" elevation logic. They must feature a 32px border radius and a 2px stroke. Content inside cards should have at least 24px of padding.

### Inputs
Input fields are dark obsidian with a subtle 1px border that thickens and turns Primary Yellow on focus. They should follow the same high-roundedness as other components (16px+).

### Chips & Tags
Small pill-shaped indicators used for categories. Use the secondary color with low opacity backgrounds and high-contrast text to ensure they don't compete with primary buttons.

### 3D Viewport
A unique component for this system—the 3D canvas should be framed with a subtle inner-glow and a grid-pattern background to emphasize the "CAD" workspace nature.