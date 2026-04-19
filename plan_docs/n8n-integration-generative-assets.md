# n8n + Generative AI Integration for Inkline Assets

**Status:** Implemented  
**Version:** 1.0  
**Date:** April 2026

---

## Overview

Inkline can orchestrate automated image generation via **n8n** + **Gemini API** (or any other generative model). This enables:

- **AI-generated slide backgrounds** — custom backgrounds that match brand color, theme, and narrative context
- **Icon generation** — brand-consistent icons and infographic elements
- **Chart backgrounds** — textured or illustrated backgrounds for chart slides
- **Logo variations** — automated logo generation in different styles/colors
- **Custom illustrations** — full-width hero images, connector diagrams, process flows

This fills a critical gap vs. Gamma: while Gamma provides LLM-driven design advice, it requires users to source or manually create visual assets. Inkline can **auto-generate** them on-demand.

---

## Architecture

### 1. n8n Workflow Automation

n8n orchestrates the generation pipeline:

```
Webhook Trigger
    ↓
HTTP Request (Gemini API call with prompt)
    ↓
Response Processing (extract base64 image data)
    ↓
Write Binary File (save PNG/SVG to disk)
    ↓
Callback to Inkline (webhook response)
```

**Key advantages:**
- **No code** — workflows are visual; non-technical users can edit generation prompts
- **Chainable** — extend with image post-processing, resizing, or tagging
- **Scheduled** — generate asset libraries on-demand or on a schedule
- **Self-hosted or cloud** — runs locally or in n8n Cloud

### 2. Gemini API Integration

The Gemini 1.5 Flash model generates images with:

- **Free tier** — 15 requests/min for free tier users; paid tier includes higher limits
- **Response mime type:** `image/png` — returns binary PNG (not JSON-wrapped)
- **Prompt control** — full natural language prompt specifies style, color, composition
- **Base64 encoding** — n8n extracts and decodes the base64 response to write PNG

---

## Workflows

### Workflow 1: Inkblot Icon Generator

**File:** `/mnt/d/inkline/inkblot-icon-generator-workflow.json`

Generates organic ink blotch icons in any brand color with optional text overlay.

```json
POST https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=API_KEY

Body:
{
  "contents": [{
    "parts": [{
      "text": "Generate a square icon: organic ink blotch splat shape in deep indigo color #3D2BE8, with white italic serif lowercase 'i' character perfectly centered inside the blotch. White background. Flat design, no gradients or shadows. High contrast, clean edges."
    }]
  }],
  "generationConfig": {
    "responseMimeType": "image/png"
  }
}
```

**Output:** `brand/logo/inkblot-icon-512.png` (and `inkblot-icon-64.png` at smaller scale)

**Usage in Inkline:**

```python
from inkline.typst import export_typst_slides

slides = [
    {
        "slide_type": "title",
        "data": {
            "company": "Inkline",
            "tagline": "AI-Powered Document Toolkit",
            "logo_path": "brand/logo/inkblot-icon-512.png",
            "background_image": "backgrounds/generated_geometric.png",
        }
    },
]
```

### Workflow 2: Branded Background Generator

**Workflow name:** Gemini Slide Background Generator

Generates full-slide or hero-section backgrounds that match:
- Brand color palette (e.g., primary, secondary, accent)
- Design aesthetic (minimalist, bold, editorial, corporate)
- Narrative context (tech, finance, healthcare)

**Prompt template:**

```
Generate a full-width 16:9 background image for a ${theme} ${audience} slide about "${title}". 
Style: ${aesthetic} (minimalist geometric | bold abstract | editorial collage | corporate clean).
Color palette: primary=${brand_primary}, secondary=${brand_secondary}, accent=${brand_accent}.
Do not include text. Leave room for content overlay on ${region} (left | center | top | bottom).
Flat design, no photographic textures.
```

**Example invocation:**

```python
import json, requests

n8n_webhook = "http://localhost:5678/webhook/slide-background"
payload = {
    "title": "Revenue compounding 34% YoY",
    "theme": "consulting",
    "audience": "investors",
    "aesthetic": "bold abstract",
    "brand_primary": "#1F2937",
    "brand_secondary": "#3B82F6",
    "brand_accent": "#10B981",
    "region": "right",
}

r = requests.post(n8n_webhook, json=payload)
image_path = r.json()["image_path"]  # e.g. "backgrounds/generated_bg_xyz.png"

# Use in Inkline
slides.append({
    "slide_type": "chart_caption",
    "data": {
        "title": "Revenue trend",
        "background_image": image_path,
        "image_path": "charts/revenue.png",
    }
})
```

---

## Implementation Guide

### Step 1: Set up n8n

**Option A: Self-hosted (recommended for privacy)**
```bash
docker run -d -p 5678:5678 n8nio/n8n
# Access http://localhost:5678
```

**Option B: n8n Cloud**
- Sign up at https://n8n.cloud
- Create a new workflow

### Step 2: Create Gemini API Key

1. Visit https://aistudio.google.com
2. Click "Create API key"
3. Copy the key (store in `.env` or n8n credentials)
4. Gemini 1.5 Flash is free tier

### Step 3: Import Workflow

In n8n:
1. **Menu** → **Import from file**
2. Select `/mnt/d/inkline/inkblot-icon-generator-workflow.json`
3. Update the Gemini API key in the HTTP Request node
4. Test: `curl -X POST http://localhost:5678/webhook/inkblot-icon`

### Step 4: Configure Inkline to Call n8n

In your Inkline generation script:

```python
import requests
from pathlib import Path

def generate_ai_background(
    title: str,
    theme: str,
    aesthetic: str,
    brand_colors: dict,
    output_dir: Path = Path("~/.local/share/inkline/output/backgrounds").expanduser()
) -> str:
    """Call n8n to generate a branded background image."""
    
    n8n_webhook = "http://localhost:5678/webhook/slide-background"
    payload = {
        "title": title,
        "theme": theme,
        "aesthetic": aesthetic,
        **brand_colors,
    }
    
    r = requests.post(n8n_webhook, json=payload, timeout=120)
    r.raise_for_status()
    
    image_path = r.json()["image_path"]
    return image_path
```

### Step 5: Use Generated Assets in Decks

```python
from inkline.typst import export_typst_slides

# Generate a background
bg_path = generate_ai_background(
    title="Q4 Financials",
    theme="consulting",
    aesthetic="bold abstract",
    brand_colors={
        "brand_primary": "#1F2937",
        "brand_secondary": "#3B82F6",
        "brand_accent": "#10B981",
    }
)

# Use it in a slide
slides = [
    {
        "slide_type": "chart_caption",
        "data": {
            "section": "Financials",
            "title": "Revenue growing 34% YoY",
            "background_image": bg_path,
            "image_path": "charts/revenue.png",
            "caption": "ARR compounding each quarter",
        }
    }
]

export_typst_slides(slides=slides, output_path="deck.pdf", brand="minimal")
```

---

## Workflow Templates (Ready to Import)

### Available Workflows

| Workflow | Input | Output | Purpose |
|---|---|---|---|
| `inkblot-icon-generator-workflow.json` | Webhook POST | PNG icon (512×512) | Brand icon with text overlay |
| `slide-background-generator` | Webhook POST | PNG background (1920×1080) | Full-slide branded background |
| `hero-illustration-generator` | Webhook POST | SVG or PNG | Full-width hero image |
| `infographic-element-generator` | Webhook POST + SVG prompt | SVG diagram | Process flows, org charts, etc. |

**Location:** `/mnt/d/inkline/n8n-workflows/`

To import any workflow:
1. In n8n, click **+** → **Import from file**
2. Select the `.json` file
3. Update API keys / credentials
4. Activate the workflow

---

## Prompt Engineering

### Best Practices for Image Generation

**DO:**
- ✓ Specify color by hex code (e.g., `#3D2BE8`)
- ✓ Use design vocabulary: "geometric", "abstract", "minimalist", "bold", "editorial"
- ✓ Name the aspect ratio: "16:9 landscape" or "square"
- ✓ Say "no text" if you want only visuals
- ✓ Reference style inspirations: "inspired by Stripe design language"

**DON'T:**
- ✗ Use photographic descriptions — Gemini generates illustrations, not photos
- ✗ Request trademarked logos or copyrighted characters
- ✗ Overly complex compositions (keep 2–3 visual elements)
- ✗ Vague color refs like "blue" — always use hex

### Example Prompts

**Icon:**
```
Generate a square icon: organic ink blotch splat shape in contrast color #3D2BE8, 
with white italic serif lowercase 'i' perfectly centered. White background, 
flat design, no gradients.
```

**Background:**
```
Generate a 16:9 background for a consulting slide about "Operational Efficiency". 
Minimalist geometric style. Color palette: dark navy #1F2937 (90% of image), 
accent teal #06B6D4 (10%, accent lines/shapes). Leave top-right area clear for text overlay. 
No photographic textures, pure vector illustration.
```

**Infographic:**
```
Generate an SVG diagram showing a 4-step process: Intake → Analysis → Decision → Output. 
Use flow arrows between boxes. Color code: primary steps #3B82F6, connectors #9CA3AF. 
Minimalist line style, no fill. Include labels inside each box.
```

---

## Comparison: Inkline vs Competitors

| Feature | Inkline | Gamma | Beautiful.ai | Canva |
|---|:---:|:---:|:---:|:---:|
| AI design advice | ✓ | ✓ | ✗ | ✗ |
| **AI image generation** | ✓ | ✗ | ✗ | ✓ (limited) |
| **n8n / workflow automation** | ✓ | ✗ | ✗ | ✗ |
| Generative backgrounds | ✓ | ✗ | ✗ | ✓ |
| Icon generation | ✓ | ✗ | ✗ | ✗ |
| Self-hosted | ✓ | ✗ | ✗ | ✗ |
| Code-first | ✓ | ✗ | ✗ | ✗ |
| Visual audit | ✓ | ✗ | ✗ | ✗ |

---

## Troubleshooting

### API Key Issues

**Error:** `"API key not valid"`
- Check the key in the n8n HTTP Request node
- Verify the key is for Gemini API (not Vertex AI)
- Try a test call: `curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:listCached?key=YOUR_KEY"`

### Image Quality

**Generated images look pixelated or low-quality:**
- Increase the prompt specificity: add "high quality", "sharp edges", "crisp lines"
- Add "SVG-style" or "vector illustration" to enforce clean geometry
- Try `gemini-1.5-pro` instead of Flash for higher quality (slower, paid)

### Timeout Issues

**Error:** `Request timeout after 120s`
- Gemini API can take 30–60s per request
- Increase the timeout in Inkline's request call: `requests.post(..., timeout=180)`
- For batch generation, queue requests asynchronously

---

## Integration with Archon Pipeline

The n8n image generation can be integrated into the full Archon audit pipeline:

```python
# ── Phase 0: Generate Assets ────────────────────────────────────
print("[ARCHON] Phase: generate_assets")
backgrounds = {}
for section_title in section_titles:
    bg = generate_ai_background(
        title=section_title,
        theme=template,
        aesthetic="bold abstract",
        brand_colors=brand_palette,
    )
    backgrounds[section_title] = bg
print("[ARCHON] generate_assets → OK in 45.2s")

# ── Phase 1–4: Standard Archon pipeline ────────────────────────
# (parse → design → export → audit)
```

---

## Roadmap

- [ ] Workflow library (10+ ready-to-use templates)
- [ ] Icon library generation (batch create 50+ icons at once)
- [ ] Animated SVG support (Lottie integration)
- [ ] Chart background overlays (textured backgrounds behind charts)
- [ ] Brand asset auto-sync (auto-update generated assets when brand changes)
- [ ] Multi-model support (Flux, Recraft, Ideogram alongside Gemini)

---

## References

- [Gemini API Docs](https://ai.google.dev/docs)
- [n8n Docs](https://docs.n8n.io)
- [Inkline n8n Workflow Examples](../brand/logo/inkblot-icon-generator-workflow.json)
