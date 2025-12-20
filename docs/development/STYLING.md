# Keiko Styling Guide

## Colors

| Name | Hex | Usage |
|------|-----|-------|
| Primary | `#DCFF4A` | Buttons, Links, Accents, Focus States |
| Black | `#000000` | Text, Backgrounds (Dark Mode) |
| White | `#FFFFFF` | Backgrounds, Text (Dark Mode) |

### Tailwind Classes

```tsx
// Primary accent
<button className="bg-keiko-primary text-keiko-black">Action</button>

// Dark background
<div className="bg-keiko-black text-keiko-white">Dark Section</div>

// Light background
<div className="bg-keiko-white text-keiko-black">Light Section</div>
```

## Fonts

| Type | Font Family | Usage |
|------|-------------|-------|
| Headlines | IBM Plex Mono | H1-H6, Data, Code |
| Body | Inter | Paragraphs, UI Text |

### Font Stack

```css
/* Headlines, Code, Data */
code, .headline-mono, .data {
  font-family: 'IBM Plex Mono', 'Roboto Mono', Consolas, 'Courier New', monospace;
}

/* Body Text */
body {
  font-family: 'Inter', ui-sans-serif, system-ui, sans-serif;
}
```

### Tailwind Classes

```tsx
// Headlines (automatic)
<h1>Headline</h1>  // Uses font-headline (IBM Plex Mono)

// Body text (automatic)
<p>Body text</p>   // Uses font-body (Inter)

// Manual overrides
<span className="font-mono">Monospace</span>
<span className="font-headline">Headline Style</span>
<span className="font-data">42.5%</span>
```

## Component Examples

### Buttons

```tsx
// Primary Button
<button className="bg-keiko-primary text-keiko-black font-mono px-4 py-2 hover:opacity-90">
  Submit
</button>

// Secondary Button
<button className="border border-keiko-black text-keiko-black font-mono px-4 py-2 hover:bg-keiko-black hover:text-keiko-white">
  Cancel
</button>
```

### Cards

```tsx
<div className="bg-keiko-white border border-keiko-black p-6">
  <h3 className="font-headline text-lg">Card Title</h3>
  <p className="font-body text-muted-foreground">Card content...</p>
</div>
```

### Data Display

```tsx
<div className="font-data text-2xl text-keiko-black">
  1,234.56
</div>
```

## Dark Mode

Dark mode is enabled via the `dark` class on the root element.

```tsx
// Automatic dark mode support
<div className="bg-background text-foreground">
  Auto-switches based on theme
</div>

// Manual dark mode styles
<div className="bg-keiko-white dark:bg-keiko-black text-keiko-black dark:text-keiko-white">
  Explicit dark mode
</div>
```

## CSS Variables

```css
:root {
  --keiko-primary: 68 100% 64%;   /* #DCFF4A in HSL */
  --keiko-black: 0 0% 0%;
  --keiko-white: 0 0% 100%;
}
```

