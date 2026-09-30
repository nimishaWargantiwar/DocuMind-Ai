# DocuMind AI - Design System Reference

**Comprehensive guide to the design system and styling applied to the DocuMind AI application.**

---

## Design Tokens

### Color Palette

#### Primary Colors
- **Primary (Accent)**: `#4F46E5` - Used for active states, links, primary buttons
- **Primary Hover**: `#4338CA` - Darker shade for hover states
- **Primary Light**: `#EEF2FF` - Light background for accents

#### Neutral Colors
- **Background Primary**: `#F7F8FA` - Main page background
- **Background Surface**: `#FFFFFF` - Cards, inputs, sidebar
- **Text Primary**: `#111827` - Main text color
- **Text Secondary**: `#667085` - Secondary text, labels
- **Text Tertiary**: `#9CA3AF` - Disabled, hints
- **Border**: `#E5E7EB` - Dividers, input borders
- **Border Light**: `#F3F4F6` - Subtle dividers

#### Status Colors
- **Success**: `#22C55E` with light: `#ECFDF5`
- **Warning**: `#F59E0B` with light: `#FFFBEB`
- **Error**: `#EF4444` with light: `#FEF2F2`
- **Info**: Accent color with light: `#EEF2FF`

### Spacing Scale

```
--spacing-xs:  0.25rem  (4px)
--spacing-sm:  0.5rem   (8px)
--spacing-md:  1rem     (16px)
--spacing-lg:  1.5rem   (24px)
--spacing-xl:  2rem     (32px)
--spacing-2xl: 3rem     (48px)
```

### Typography

#### Font Sizes
```
--text-xs:   0.75rem    (12px)
--text-sm:   0.875rem   (14px)
--text-base: 1rem       (16px)
--text-lg:   1.125rem   (18px)
--text-xl:   1.25rem    (20px)
--text-2xl:  1.5rem     (24px)
--text-3xl:  1.875rem   (30px)
```

#### Font Family
- System font stack: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif`
- Font weight: 400 (regular), 500 (medium), 600 (semibold), 700 (bold), 800 (extra bold)

### Border Radius

```
--radius-sm: 0.375rem (6px)   - Small elements (inputs, badges)
--radius-md: 0.5rem   (8px)   - Medium elements (buttons, cards)
--radius-lg: 0.75rem  (12px)  - Large elements (file uploader)
```

---

## Component Styling

### Buttons

#### Default Button
```css
background-color: #FFFFFF
color: #111827
border: 1px solid #E5E7EB
padding: 0.625rem 1.25rem
height: 2.25rem
border-radius: 0.5rem
font-weight: 600
font-size: 0.875rem
```

#### Button States
- **Hover**: Background changes to #F7F8FA, border becomes primary color
- **Active**: Background remains #FFFFFF, slight transform down
- **Disabled**: Background becomes #F3F4F6, text becomes #9CA3AF, cursor not-allowed

#### Primary Button (Active Navigation)
```css
background-color: #4F46E5
color: #FFFFFF
border: none
```

#### Sidebar Button (Inactive)
```css
background-color: transparent
color: #667085
border: 1px solid transparent
```

### Input Fields

```css
background-color: #FFFFFF
color: #111827
border: 1px solid #E5E7EB
border-radius: 0.375rem
padding: 0.5rem 0.75rem
font-size: 0.875rem
```

#### Focus State
- Border color changes to #4F46E5 (primary)
- Box-shadow: 0 0 0 3px #EEF2FF (accent light)

### File Uploader

```css
border: 2px dashed #E5E7EB
border-radius: 0.75rem
background-color: #FFFFFF
padding: 2rem
text-align: center
```

#### Hover State
- Border color: #4F46E5
- Background color: #EEF2FF

### Status Messages

#### Success
```css
background-color: #ECFDF5
border-left: 3px solid #22C55E
```

#### Warning
```css
background-color: #FFFBEB
border-left: 3px solid #F59E0B
```

#### Error
```css
background-color: #FEF2F2
border-left: 3px solid #EF4444
```

#### Info
```css
background-color: #EEF2FF
border-left: 3px solid #4F46E5
```

### Navigation Tabs

#### Default Tab
```css
color: #667085
border-bottom: 2px solid transparent
padding: 0.75rem 1rem
font-weight: 600
font-size: 0.875rem
```

#### Active Tab
```css
color: #4F46E5
border-bottom: 2px solid #4F46E5
```

---

## Layout & Spacing

### Main Container
```css
max-width: 1000px
padding: 1.5rem 2rem 2rem
margin: auto
```

### Sidebar
```css
background-color: #FFFFFF
border-right: 1px solid #E5E7EB
padding: 1rem
```

### Section Headers
```css
font-size: 0.75rem
font-weight: 700
text-transform: uppercase
letter-spacing: 0.05em
color: #667085
margin-bottom: 0.75rem
```

### Margins & Padding
- Between major sections: `1.5rem` (24px)
- Between subsections: `1rem` (16px)
- Between elements: `0.75rem` (12px)
- Tight spacing: `0.5rem` (8px)

---

## Responsive Design

### Desktop (> 768px)
- Full-width layout with max-width constraint
- 2rem horizontal padding
- Normal font sizes
- Full button heights (2.25rem)

### Mobile (≤ 768px)
- Reduced padding (1rem)
- Adjusted font sizes (text-xs to text-sm)
- Button heights: 2.125rem
- Stack layout where needed

---

## Accessibility

### Color Contrast
- **Text on background**: 4.5:1 minimum ratio
- **Primary #4F46E5 on white**: 5.5:1 (WCAG AAA)
- **Text secondary #667085 on white**: 4.6:1 (WCAG AA)

### Interactive Elements
- All buttons have focus state with outline
- Disabled states visually distinct
- Hover states provide feedback
- Touch targets: minimum 44x44px for mobile

### Typography
- Line height: 1.6 for body text, 1.2 for headings
- Letter spacing: -0.01em for headings, 0.05em for labels
- Font sizes never below 12px on mobile

---

## Sidebar Layout

```
┌─────────────────────────────────┐
│  ✦ DocuMind AI                  │
│  AI-Powered Document Intelligence│
├─────────────────────────────────┤
│                                 │
│ WORKSPACE                       │
│ [💬 Chat]                       │
│ [📚 Documents]                  │
│ [🧠 Analyze]                    │
│ [🔀 Compare]                    │
│ [📊 Evaluation]                 │
│                                 │
├─────────────────────────────────┤
│ DOCUMENTS                       │
│ [2 uploaded]                    │
│ ☑ document1.pdf                 │
│ ☑ document2.pdf                 │
│                                 │
├─────────────────────────────────┤
│ SETTINGS                        │
│ [⚙️ Advanced ▼]                 │
│                                 │
├─────────────────────────────────┤
│ STATUS                          │
│ ✓ LLM ready                     │
└─────────────────────────────────┘
```

---

## Main Page Layout

```
┌─────────────────────────────────────┐
│ UPLOAD DOCUMENTS                    │
│ ┌─────────────────────────────────┐ │
│ │  📤 Upload PDF documents        │ │
│ │  (Drag files here or click)      │ │
│ └─────────────────────────────────┘ │
│ Maximum file size: 200 MB per file  │
│                                     │
│ [Current Workspace Content]         │
└─────────────────────────────────────┘
```

---

## Chat Interface

### User Message
```
[Timestamp] You
Message content here...
```

### Assistant Message
```
✦ DocuMind
Response content here...

SOURCES
- paper.pdf — Page 12 — Chunk 1 (95% relevant)
- report.pdf — Page 5 — Chunk 3 (87% relevant)

EVIDENCE
[Evidence visualization]
```

---

## Form Elements

### Text Input
- Border: 1px solid #E5E7EB
- Padding: 0.5rem 0.75rem
- Font size: 0.875rem
- Height: auto (typically 36px)
- Placeholder color: #9CA3AF

### Select/Dropdown
- Same styling as text input
- Background-image: down arrow
- No additional icon needed

### Checkbox
- Size: 20x20px
- Color: #4F46E5 when checked
- Label: 0.875rem, margin-left 0.5rem

### Slider
- Track: #E5E7EB
- Thumb: #4F46E5
- Padding: 1rem 0

### Expander/Accordion
- Border: 1px solid #E5E7EB
- Header background: #FFFFFF
- Header padding: 0.75rem 1rem
- Header hover: background becomes #F7F8FA
- Arrow: #667085

---

## Implementation Example

```python
# Using design tokens in CSS
st.markdown("""
<style>
    :root {
        --accent: #4F46E5;
        --bg-surface: #FFFFFF;
        --text-primary: #111827;
        --spacing-md: 1rem;
        --radius-md: 0.5rem;
    }
    
    .custom-card {
        background-color: var(--bg-surface);
        padding: var(--spacing-md);
        border-radius: var(--radius-md);
        color: var(--text-primary);
    }
    
    .custom-card:hover {
        border-color: var(--accent);
    }
</style>
""", unsafe_allow_html=True)
```

---

## Best Practices

1. **Use CSS Variables**: Always use `var(--token-name)` for consistency
2. **Maintain Spacing**: Use the spacing scale, don't create arbitrary values
3. **Consistent Heights**: Use 2.25rem for buttons, 1.5rem for small controls
4. **Color Usage**: Use semantic colors (primary, success, warning, error) not absolute colors
5. **Responsive**: Test on mobile, tablet, and desktop sizes
6. **Accessibility**: Always check color contrast and interactive element sizing

---

## Verification

To verify the design system is correctly applied:

1. **Run the application**:
   ```bash
   streamlit run app.py
   ```

2. **Check visual elements**:
   - Sidebar renders with proper colors
   - Buttons have consistent height and spacing
   - File uploader has rounded corners and proper hover state
   - Text has proper contrast
   - Spacing between elements is consistent

3. **Test responsiveness**:
   - Resize browser window
   - Check mobile viewport (375px width)
   - Verify all content is readable

4. **Test accessibility**:
   - Tab through interactive elements
   - Verify focus states are visible
   - Test with browser DevTools accessibility checker

---

**Design System Version**: 1.0  
**Last Updated**: September 30, 2026  
**Status**: Production Ready ✅
