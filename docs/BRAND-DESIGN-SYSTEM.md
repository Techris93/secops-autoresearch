# Brand & Design System Guide

## Brand Identity

### Brand Name

**secopsai** — Clean, technical, descriptive

### Tagline

"Intelligent Attack Detection for OpenClaw"

### Mission Statement

Provide production-grade security detection for OpenClaw with F1 1.0 accuracy, ease-of-use like ByteRover, and transparency in metrics.

---

## Visual Identity

### Color Palette

**Primary Colors:**

- **Deep Red** `#D81B60` — Danger, security, action
  - Used for: CTAs, alerts, key highlights
  - Psychology: Urgency, trust, power

- **Dark Slate** `#1A1A1A` — Professional, technical
  - Used for: Text, backgrounds, navigation
  - Psychology: Stability, authority, tech-forward

- **White** `#FFFFFF` — Clean, clarity
  - Used for: Backgrounds, negative space
  - Psychology: Trust, simplicity, clarity

**Secondary Colors:**

- **Light Gray** `#F5F5F5` — Subtle backgrounds, cards
- **Medium Gray** `#666666` — Secondary text, borders
- **Success Green** `#4CAF50` — Checkmarks, success states
- **Warning Orange** `#FF9800` — Caution, findings severity

### Typography

**Font Stack:**

```css
/* Headlines */
font-family: "Inter", "Helvetica Neue", sans-serif;
font-weight: 700;
letter-spacing: -0.02em;

/* Body Text */
font-family: "Inter", "Helvetica Neue", sans-serif;
font-weight: 400;
line-height: 1.6;

/* Code */
font-family: "Fira Code", "Courier New", monospace;
font-weight: 500;
```

**Sizes:**

- **H1** — 48px, bold, 1.2x line-height
- **H2** — 32px, bold, 1.3x line-height
- **H3** — 24px, bold, 1.4x line-height
- **Body** — 16px, regular, 1.6x line-height
- **Small** — 14px, regular, 1.5x line-height
- **Code** — 13px, monospace, 1.5x line-height

### Logo Design

**Primary Logo:**

```
🛡️ secopsai
```

**Simple Shield Icon + Text:**

```
┌─────────┐
│    🛡️   │  secopsai
│ DETECT  │
└─────────┘
```

**Favicon:** Shield icon 32x32px with D81B60 background

---

## Component Library

### Buttons

**Primary Button (CTA)**

```css
background-color: #d81b60;
color: #ffffff;
padding: 12px 24px;
border-radius: 6px;
font-weight: 600;
hover: brightness(1.1);
```

Usage: "Get Started", "Download", main actions

**Secondary Button**

```css
background-color: transparent;
color: #D81B60;
border: 2px solid #D81B60;
padding: 12px 24px;
border-radius: 6px;
font-weight: 600;
hover: background-color: #F5F5F5;
```

Usage: "View Docs", "Learn More", secondary actions

**Tertiary Button**

```css
background-color: transparent;
color: #666666;
border: 1px solid #E0E0E0;
padding: 12px 24px;
border-radius: 6px;
font-weight: 500;
hover: background-color: #F5F5F5;
```

Usage: Navigation, less important actions

### Cards

**Feature Card**

```css
background-color: #FFFFFF;
border: 1px solid #E0E0E0;
border-radius: 8px;
padding: 24px;
box-shadow: 0 1px 3px rgba(0,0,0,0.1);
hover: box-shadow: 0 4px 12px rgba(0,0,0,0.15);
transition: 0.3s ease;
```

**Stat Card (for metrics)**

```css
background: linear-gradient(135deg, #d81b60 0%, #9c27b0 100%);
color: #ffffff;
padding: 32px;
border-radius: 12px;
text-align: center;

.stat-value {
  font-size: 48px;
  font-weight: 700;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 16px;
  opacity: 0.9;
}
```

### Alert/Finding Box

```css
border-left: 4px solid #d81b60;
background-color: #fafafa;
padding: 16px;
border-radius: 4px;
margin: 16px 0;

.alert-icon {
  display: inline-block;
  margin-right: 8px;
  font-size: 20px;
}

.alert-title {
  font-weight: 600;
  margin-bottom: 4px;
}

.alert-text {
  color: #666666;
  font-size: 14px;
}
```

### Navigation Bar

```css
background-color: #FFFFFF;
border-bottom: 1px solid #E0E0E0;
padding: 16px 40px;
display: flex;
justify-content: space-between;
align-items: center;
position: sticky;
top: 0;
z-index: 100;

.logo {
  font-size: 20px;
  font-weight: 700;
  color: #1A1A1A;
}

.nav-links {
  display: flex;
  gap: 32px;
  margin: 0;
  list-style: none;
}

.nav-links a {
  color: #666666;
  text-decoration: none;
  font-weight: 500;
  hover: color: #D81B60;
  transition: color 0.2s;
}

.nav-links a.active {
  color: #D81B60;
  border-bottom: 2px solid #D81B60;
  padding-bottom: 8px;
}
```

### Code Block

```css
background-color: #1a1a1a;
color: #e0e0e0;
padding: 16px;
border-radius: 6px;
overflow-x: auto;
font-family: "Fira Code", monospace;
font-size: 13px;
line-height: 1.5;
margin: 16px 0;

/* Syntax Highlighting */
.keyword {
  color: #ff79c6;
}
.string {
  color: #f1fa8c;
}
.number {
  color: #bd93f9;
}
.comment {
  color: #6272a4;
}
.operator {
  color: #ff79c6;
}
```

---

## Design Patterns

### Hero Section

- Full width background
- Centered text overlay
- Large headline (48px)
- Subheadline (20px, lighter weight)
- CTA button (primary)
- Optional background image or shape

### Feature Grid

- 2-3 columns on desktop, 1 on mobile
- Card-based layout
- Icon + headline + description
- Consistent height cards
- Hover effects on cards

### Metric/Benchmark Display

- Large numbers with corresponding labels
- Color-coded severity (green for good, orange for warning)
- Grid layout for comparison
- Optional sparkline or chart

### Rule Reference

- Vertical card layout
- Rule ID prominent (e.g., "RULE-101")
- Attack type with MITRE code
- Pattern description
- Severity badge
- F1 score indicator

---

## Spacing & Layout

**Spacing Scale:**

```
4px  — Extra small
8px  — Small
16px — Base
24px — Medium
32px — Large
48px — Extra large
64px — Huge
```

**Container Width:**

```
Mobile:    100% (with 16px padding)
Tablet:    100% (with 32px padding)
Desktop:   1200px max-width
Wide:      1400px max-width
```

**Grid System:**

```
12-column grid
Gutter: 24px
Mobile: 4px gutter
Tablet: 16px gutter
```

---

## Imagery & Icons

### Icon Style

- Solid, clean, minimal
- 24x24px base size
- Line weight: 2px
- Rounded corners (2px)
- Shield, check, alert, arrow styles

### Photography

- Tech-focused, clean
- Dark mode friendly
- Real attack scenarios preferred
- No stock photos of "hackers"
- Use terminal screenshots, diagrams

### Diagrams & Illustrations

- Mermaid diagrams for architecture
- Flow charts for processes
- Attack chain visualizations
- Network diagrams for deployment

---

## Interactions & Animations

### Hover States

```css
/* Cards */
transform: translateY(-4px);
box-shadow: 0 4px 12px rgba(216, 27, 96, 0.15);
transition: all 0.3s ease;

/* Buttons */
opacity: 0.9;
transform: scale(1.02);
transition: all 0.2s ease;

/* Links */
color: #d81b60;
text-decoration: underline;
transition: color 0.2s ease;
```

### Loading States

- Spinner animation (rotating shield icon)
- Fade-in for content appearance
- Skeleton screens for data loading

### Success/Error States

- Green checkmark for success
- Red X for error
- Orange warning for caution
- Toast notifications for feedback

---

## Dark Mode

Mirror of light mode with inverted colors:

```css
/* Dark Mode Palette */
background: #0D0D0D
text: #E0E0E0
accent: #FF79C6 (brighter red)
card: #1A1A1A
border: #333333
```

All previous color rules apply with inverted backgrounds.

---

## Accessibility

### Color Contrast

- Min 4.5:1 for body text
- Min 3:1 for large text
- All interactive elements distinct from background

### Typography

- Min 16px for body text
- Line height min 1.4
- Letter spacing: 0.5px for headings

### Interactive Elements

- Min 44x44px touch targets
- Keyboard navigation support
- Focus indicators visible
- ARIA labels for complex components

---

## Brand Voice

**Tone:**

- Professional but approachable
- Technical but not jargon-heavy
- Confident without arrogance
- Direct and clear

**Word Choice:**

- "Detect" not "monitor"
- "Findings" not "alerts"
- "Production-ready" not "enterprise"
- "Reproducible" not "validated"

**Example Copy:**

```
❌ Monitor your environment for potential issues
✅ Detect security attacks with F1 1.0 accuracy

❌ Enterprise attack detection platform
✅ Production-grade security detection for OpenClaw

❌ Our sophisticated ML algorithms analyze threats
✅ 12 battle-tested detection rules with zero false positives
```

---

## Implementation Checklist

- [ ] Download Inter font (Google Fonts)
- [ ] Download Fira Code font (Google Fonts)
- [ ] Create logo files (SVG, PNG, favicon)
- [ ] Build color palette CSS variables
- [ ] Create reusable component library
- [ ] Design homepage mockup (HTML/CSS)
- [ ] Set up Tailwind or CSS framework
- [ ] Create template for documentation pages
- [ ] Test dark mode on all components
- [ ] Verify accessibility (WCAG 2.1 AA)

---

## Resources

- **Font Downloads:** https://fonts.google.com (Inter, Fira Code)
- **Icon Library:** https://heroicons.com/ (Tailwind-native)
- **Color Tools:** https://coolors.co/
- **Accessibility:** https://webaim.org/articles/contrast/
- **Design System Template:** https://www.figma.com/design-systems/
