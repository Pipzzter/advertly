# Agent 1: Copy & Image Injection

> **Template-Aware Copy & Image Injection AI Agent**

## 🎯 Overview

The Copy Injection Agent automatically generates complete landing pages by filling predefined HTML templates with provided marketing copy and AI-generated images. It eliminates the need for manual copy placement and image sourcing.

**Testing Ground:** [CheckoutChamp Funnel Builder](https://app.checkoutchamp.com/editfunnel/b263cdf6-2082-4fec-9565-77578efc1772)

---

## 📋 Table of Contents

- [How It Works](#-how-it-works)
- [Processing Pipeline](#-processing-pipeline)
- [Components](#-components)
- [Template System](#-template-system)
- [Copy Parsing](#-copy-parsing)
- [Placeholder System](#-placeholder-system)
- [Image Generation](#-image-generation)
- [API Reference](#-api-reference)
- [Data Schemas](#-data-schemas)

---

## 🔄 How It Works

### High-Level Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER INPUT                                        │
│  1. Select HTML template                                                    │
│  2. Provide raw advertorial copy                                            │
│  3. (Optional) Product name & category hints                                │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        COPY INJECTION AGENT                                 │
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   1. Load   │───▶│  2. Parse   │───▶│  3. Fill    │───▶│ 4. Generate │  │
│  │  Template   │    │    Copy     │    │ Placeholders│    │   Images    │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│         │                  │                  │                  │          │
│         ▼                  ▼                  ▼                  ▼          │
│    HTML + CSS         Structured        Filled HTML         Final HTML     │
│    Metadata           ParsedCopy        with text           with images    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              OUTPUT                                         │
│  ✅ Complete HTML ready to publish                                          │
│  ✅ All placeholders filled with copy                                       │
│  ✅ AI-generated images embedded as base64 data URIs                        │
│  ✅ Summary of placements made                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Processing Pipeline

### Step-by-Step Process

#### 1. Load Template
```python
html = TemplateService.get_html(template_id)
metadata = TemplateService.get_metadata(template_id)
```
- Loads HTML template from `/backend/app/static/templates/`
- Reads template metadata (repeatable sections, placeholder definitions)
- Extracts all placeholders for reporting

#### 2. Parse Raw Copy (LLM)
```python
parsed_copy = await self.copy_parser.parse(
    raw_copy=input_data.raw_copy,
    product_name=input_data.product_name,
    product_category=input_data.product_category,
)
```
- Sends raw copy to **Gemini 2.5 Flash** with structured output
- LLM identifies and categorizes all content sections
- Returns a `ParsedCopy` Pydantic model with structured data

#### 3. Fill Repeatable Sections
```python
filler.fill_repeat_section(
    section_name="body",
    items=parsed_copy.body_sections,
    fill_item_func=fill_body_item,
)
```
- Clones template blocks for each item (body sections, reviews, social proofs)
- Regenerates HTML IDs to avoid duplicates
- Preserves original CSS styling

#### 4. Fill Simple Placeholders
```python
filler.fill_simple("[Headline goes here]", parsed_copy.headline)
```
- Direct text replacement for non-repeatable content
- Handles fallback defaults for required fields

#### 5. Remove Empty Optional Sections
```python
html = self._remove_empty_optional_sections(html, parsed_copy)
```
- Removes entire sections marked as `OPTIONAL` if no content exists
- Uses HTML comments: `<!--OPTIONAL:section_name:START-->...<!--OPTIONAL:section_name:END-->`

#### 6. Generate Images
```python
html = await self.image_generator.generate_all_images(html, parsed_copy)
```
- Generates images for all placeholder markers
- Uses **Gemini 2.5 Flash Image** model
- Embeds images as base64 data URIs (no external files)

#### 7. Clean Unfilled Placeholders
```python
html = self._clean_unfilled_placeholders(html)
```
- Removes any remaining `[... goes here]` placeholders
- Removes unfilled image markers

---

## 🧩 Components

### File Structure

```
backend/app/services/agents/
├── base.py                      # Abstract base agent class
├── llm_client.py                # Gemini LLM client (text generation)
├── image_client.py              # Gemini Image client (image generation)
└── copy_injection/
    ├── __init__.py
    ├── agent.py                 # Main CopyInjectionAgent orchestrator
    ├── copy_parser.py           # LLM-based copy parsing
    ├── placeholder_filler.py    # Template filling logic
    ├── image_generator.py       # Image generation orchestration
    ├── template_service.py      # Template loading & metadata
    └── schemas.py               # Pydantic data models
```

### Component Responsibilities

| Component | Purpose |
|-----------|---------|
| `CopyInjectionAgent` | Main orchestrator - coordinates all steps |
| `CopyParser` | Uses LLM to parse raw copy into structured `ParsedCopy` |
| `PlaceholderFiller` | Handles text replacement and section cloning |
| `ImageGenerator` | Generates images and replaces image placeholders |
| `TemplateService` | Loads templates and metadata from filesystem |
| `GeminiClient` | LLM API client with structured output support |
| `GeminiImageClient` | Image generation API client |

---

## 📄 Template System

### Template Location
```
backend/app/static/templates/
├── template_metadata.json       # Central metadata for all templates
└── template_simple.html         # "Clean Article" — the single default template
```

### Placeholder Types

#### 1. Simple Placeholders (Non-Repeatable)
```html
<h1>[Headline goes here]</h1>
<p>[Hook goes here]</p>
<span>[Author info goes here]</span>
```

#### 2. Repeatable Section Markers
```html
<!-- REPEAT:body:START -->
<div class="body-section">
    <h2>[Body section title goes here]</h2>
    <p>[Body section goes here]</p>
    <img src="[Body section image goes here]" />
</div>
<!-- REPEAT:body:END -->
```

#### 3. Optional Section Markers
```html
<!--OPTIONAL:case_study:START-->
<section class="case-study">
    <h2>[Case study title goes here]</h2>
    <p>[Case study goes here]</p>
</section>
<!--OPTIONAL:case_study:END-->
```

### All Supported Placeholders

| Placeholder | Section Type | Description |
|-------------|--------------|-------------|
| `[Headline goes here]` | Simple | Main headline |
| `[Subheadline goes here]` | Simple | Secondary headline |
| `[Hook goes here]` | Simple | Opening hook text |
| `[POST CATEGORY GOES HERE]` | Simple | Article category label |
| `[Author info goes here]` | Simple | Author name/credentials |
| `[Date of last edit goes here]` | Simple | Auto-filled with current date |
| `[Introduction goes here]` | Simple | Introduction paragraphs |
| `[Product presentation title goes here]` | Simple | Product section title |
| `[Product presentation goes here]` | Simple | Product description |
| `[Product reveal goes here]` | Simple | Product reveal text |
| `[Solution product discovery title goes here]` | Simple | Discovery section title |
| `[Main Social proof title goes here]` | Simple | Main social proof title |
| `[Main Social proof goes here]` | Simple | Studies/statistics |
| `[Case study title goes here]` | Optional | Case study title |
| `[Case study goes here]` | Optional | Case study narrative |
| `[Offer section title goes here]` | Simple | Offer title |
| `[Offer section goes here]` | Simple | Offer CTA content |
| `[References goes here]` | Simple | Citations/disclaimers |
| `[Body section title goes here]` | Repeatable | Body section title |
| `[Body section goes here]` | Repeatable | Body section content |
| `[Review person name goes here]` | Repeatable | Reviewer name |
| `[Review person location goes here]` | Repeatable | Reviewer location |
| `[Review text goes here]` | Repeatable | Testimonial text |
| `[Social proof person goes here]` | Repeatable | Expert name/title |
| `[Social proof quote goes here]` | Repeatable | Expert quote |

### Image Placeholders

| Placeholder | Aspect Ratio | Description |
|-------------|--------------|-------------|
| `[Headline image goes here]` | 16:9 | Hero/banner image |
| `[Author image goes here]` | 1:1 | Author headshot |
| `[Body section image goes here]` | 4:3 | Body section illustration |
| `[Product presentation image goes here]` | 4:3 | Product photograph |
| `[Review person image goes here]` | 1:1 | Reviewer portrait |
| `[Social proof image goes here]` | 1:1 | Expert/authority photo |
| `[Main social proof image goes here]` | 4:3 | Scientific/credibility image |
| `[Case study image goes here]` | 4:3 | Case study illustration |
| `[Offer section image goes here]` | 4:3 | Promotional image |
| `[Introduction image goes here]` | 4:3 | Introduction illustration |

---

## 🤖 Copy Parsing

### LLM Model
- **Model:** Gemini 2.5 Flash (`gemini-2.5-flash`)
- **Output:** Structured JSON via Pydantic schema
- **Max Tokens:** 65,536

### What the LLM Extracts

The copy parser prompt instructs the LLM to identify:

1. **Headlines & Hooks**
   - Main headline (attention-grabbing statement)
   - Subheadline (secondary headline)
   - Hook (opening text that grabs attention)

2. **Body Content**
   - 3-5 body sections maximum
   - MAX 150 words per section
   - HTML formatted (`<br>`, `<b>`, `<i>`)
   - Varied rhythm between sections

3. **Product Information**
   - Product presentation title
   - Product description and benefits
   - Product reveal text
   - Solution discovery title

4. **Social Proof**
   - Expert quotes (1-2 sentences each)
   - Main social proof (studies, statistics)
   - Case study (detailed transformation story)

5. **Reviews/Testimonials**
   - 2-4 sentences per review
   - Human-like writing (not marketing speak)
   - Specific results and timeframes
   - Unique person names

6. **Offer Section**
   - Call-to-action text
   - Pricing, urgency, bonuses

7. **Metadata**
   - Post category (auto-generated)
   - Author name and credentials
   - References and disclaimers

### Content Guidelines Enforced

| Element | Constraint |
|---------|------------|
| Body sections | MAX 5 sections, MAX 150 words each |
| Reviews | MAX 2-4 sentences, human-like tone |
| Social proofs | MAX 1-2 sentences each |
| Listicle items | MAX 70 words per item |
| All content | HTML tags only (no `\n` characters) |

---

## 🖼️ Image Generation

### Technology
- **Model:** Gemini 2.5 Flash Image (`gemini-2.5-flash-image`)
- **Output:** Base64 data URIs (embedded directly in HTML)
- **Retry Logic:** Exponential backoff for rate limits

### Image Type Guidelines

The image generator follows strict guidelines for three image types:

#### Headline Images
**Goal:** Create extreme curiosity and force the reader to continue reading.

- Must visually express the headline
- Curiosity > clarity
- Feel real, not like an ad
- Editorial, candid, observational style
- **NO:** product, logos, text, obvious advertising

#### Body Section Images
**Goal:** Visually explain the exact idea of the section simply.

- One section = one core idea = one image
- Must explain, not decorate
- Understandable for older readers
- Simple compositions, clear focus
- Static for situations; GIF for mechanisms

#### Product Introduction Images
**Goal:** Visually prove how the product works.

- Must match exact product being sold
- Must explain product mechanism
- Split screen format (product + mechanism)
- Educational, trustworthy, calm tone

### Image Prompts

```python
IMAGE_PROMPTS = {
    "headline": "Photorealistic hero image for an advertorial about: {context}...",
    "author": "Photorealistic professional headshot photograph of {context}...",
    "body_section": "Photorealistic image illustrating: {context}...",
    "product": "Photorealistic product photograph of: {context}...",
    "review_person": "Photorealistic portrait photograph of a happy customer...",
    "social_proof": "Photorealistic image of: {context}...",
    "offer": "Photorealistic promotional image for: {context}...",
    "case_study": "Photorealistic image illustrating: {context}...",
}
```

### How Images Are Placed

1. **Simple image placeholders** - Direct replacement:
   ```
   [Headline image goes here] → data:image/png;base64,...
   ```

2. **Repeatable section images** - Use index markers:
   ```
   __IMG_PLACEHOLDER_0_[Body section image goes here]__ → data:image/png;base64,...
   __IMG_PLACEHOLDER_review_0__ → data:image/png;base64,...
   ```

---

## 📡 API Reference

### Endpoints

#### Process Copy Injection
```http
POST /api/v1/copyinjection
```

**Request Body:**
```json
{
  "template_id": "template_simple",
  "raw_copy": "Your full advertorial copy here...",
  "product_name": "ProductX",
  "product_category": "Health Supplements"
}
```

**Response:**
```json
{
  "html": "<html>...complete page...</html>",
  "placeholders_found": ["[Headline goes here]", "[Hook goes here]", ...],
  "placements": [
    {"placeholder": "[Headline goes here]", "content_preview": "Revolutionary Discovery..."},
    ...
  ],
  "images_generated": 12,
  "success": true,
  "error_message": null
}
```

#### List Templates
```http
GET /api/v1/copyinjection/templates
```

**Response:**
```json
[
  {"id": "template_simple", "name": "Clean Article"}
]
```

---

## 📊 Data Schemas

### Input Schema

```python
class CopyInjectionInput(BaseModel):
    template_id: str           # ID of template to use
    raw_copy: str              # Raw advertorial copy
    product_name: str | None   # Optional product name hint
    product_category: str | None  # Optional category hint
```

### Output Schema

```python
class CopyInjectionOutput(BaseModel):
    html: str                          # Final HTML output
    placeholders_found: list[str]      # All placeholders in template
    placements: list[PlacementSummary] # Summary of what was placed
    images_generated: int              # Number of images generated
    success: bool                      # Whether processing succeeded
    error_message: str | None          # Error details if failed
```

### Parsed Copy Schema

```python
class ParsedCopy(BaseModel):
    # Header
    headline: str
    subheadline: str | None
    hook: str | None
    post_category: str | None
    
    # Author
    author_name: str | None
    author_description: str | None
    
    # Introduction
    introduction: str | None
    
    # Body (repeatable)
    body_sections: list[BodySection]
    
    # Product
    product: ProductInfo | None
    product_reveal: str | None
    solution_discovery_title: str | None
    
    # Social proof
    social_proofs: list[SocialProof]
    main_social_proof_title: str | None
    main_social_proof: str | None
    
    # Case study
    case_study_title: str | None
    case_study: str | None
    
    # Reviews (repeatable)
    reviews: list[Review]
    
    # Offer
    offer: OfferInfo | None
    
    # References
    references: str | None
    
    # Image contexts
    headline_image_context: str | None
```

---

## 🔧 Technical Details

### LLM Client Configuration

```python
class GeminiClient:
    model = "gemini-2.5-flash"
    max_tokens = 65536
    response_mime_type = "application/json"  # For structured output
```

### Image Client Configuration

```python
class GeminiImageClient:
    model = "gemini-2.5-flash-image"
    supported_aspect_ratios = [
        "1:1", "2:3", "3:2", "3:4", "4:3", 
        "4:5", "5:4", "9:16", "16:9", "21:9"
    ]
```

### Retry Logic
Both clients implement exponential backoff:
- Initial wait: 2 seconds
- Multiplier: 2x per attempt
- Max retries: 3
- Jitter: Random 0-1 second addition

### Error Handling
- Failed image generation returns SVG placeholder
- Missing placeholders logged but don't fail process
- Empty optional sections automatically removed

---

## 📝 Example Usage

### Python (Backend)

```python
from app.services.agents.copy_injection import CopyInjectionAgent
from app.services.agents.copy_injection.schemas import CopyInjectionInput

agent = CopyInjectionAgent()

result = await agent.process(
    CopyInjectionInput(
        template_id="template_simple",
        raw_copy="""
        HEADLINE: Doctors Shocked by New Discovery
        
        A revolutionary breakthrough is changing how we think about health...
        
        [Full advertorial copy here]
        """,
        product_name="HealthMax Pro",
        product_category="Health Supplements",
    )
)

if result.success:
    print(f"Generated HTML with {result.images_generated} images")
    # result.html contains the complete page
else:
    print(f"Failed: {result.error_message}")
```

### TypeScript (Frontend)

```typescript
import { copyInjectionApi } from '@/api/agents/copyInjection';

const result = await copyInjectionApi.process({
  template_id: 'template_simple',
  raw_copy: advertorialCopy,
  product_name: 'HealthMax Pro',
  product_category: 'Health Supplements',
});

if (result.success) {
  // result.html contains complete page ready to publish
  document.getElementById('preview').innerHTML = result.html;
}
```

---

## ✅ Success Criteria

The agent is successful when:

- ✅ Pages can be generated end-to-end automatically
- ✅ Output HTML renders correctly without layout issues
- ✅ Images feel relevant and intentional
- ✅ Manual copy rearranging is rarely needed
- ✅ The system can be used daily for production

---

## 🚀 One-Sentence Summary

> The Copy Injection Agent takes predefined HTML templates, uses Gemini 2.5 Flash to parse and structure raw advertorial copy, fills all placeholders with appropriate content, generates context-aware images using Gemini 2.5 Flash Image, and outputs a fully ready landing page—all automatically.

