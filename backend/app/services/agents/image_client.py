"""
OpenAI Image Client (GPT Image)
===============================

Wraps OpenAI's Image API for photorealistic image generation.
Returns base64 data URIs for direct embedding in HTML.

Model: OPENAI_IMAGE_MODEL (default gpt-image-2.5-flare — the fast GPT Image model)
"""

import asyncio
import logging
import random
from enum import Enum
from functools import cached_property
from typing import Optional

from openai import AsyncOpenAI, RateLimitError

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# JPEG keeps the inline base64 images small; OpenAI also generates it faster than PNG
JPEG_COMPRESSION = 85

# Base wait after hitting the per-minute image limit (Tier 1 allows 5 images/minute)
RATE_LIMIT_WAIT_SECONDS = 20


class ImageType(str, Enum):
    """Type of advertorial image to generate."""

    HEADLINE = "headline"
    BODY = "body"
    PRODUCT = "product"


# =============================================================================
# SYSTEM PROMPTS FOR ADVERTORIAL IMAGE GENERATION
# =============================================================================

HEADLINE_IMAGE_SYSTEM_PROMPT = """
## Headline Images – AI Generation Instructions

### Core Goal (Very Important)
The headline image exists for one reason only: Create extreme curiosity and force 
the reader to continue reading the advertorial. It must visually support what the 
headline is saying without explaining it fully.

- If the image answers the question → it FAILED.
- If the image makes the reader think "wait… why?" → it WORKED.

### Core Rules (Non-Negotiable)

1. **The image must visually express the headline**
   - The reader should instantly feel that the image and headline belong together.
   - The image should show the situation or moment the headline is hinting at — 
     NOT the solution, NOT the product.

2. **Curiosity is more important than clarity**
   The image should:
   - Feel unfinished
   - Suggest something happening or about to happen
   - Make the viewer want context
   - The goal is continuation, not explanation.

3. **It must feel real, not like an ad**
   Images should look:
   - Editorial
   - Candid
   - Observational
   - NOT staged, polished, or commercial.

### Image Type Choice (Critical)

#### GIF / Animation (Preferred)
Use a GIF or subtle animation whenever motion increases curiosity.
Best used when the headline implies:
- A process
- A change over time
- Something hidden inside the body or situation
- A cause that isn't obvious

Animation rules:
- 2–4 second loop
- Very subtle movement only
- Natural motion (breathing, hand movement, slow zoom, light change)
- No effects, no text, no dramatic transitions
- The animation should feel like a living moment, not a graphic.

#### Static Image
Use a static image only when a frozen moment creates more tension or mystery.
Best used when:
- One specific moment says enough
- The stillness itself feels uncomfortable or intriguing
- Motion would reduce impact

The static image should feel like it was captured mid-moment, not posed.

### Absolute Do-Nots
- NO product
- NO logos
- NO text or captions
- NO obvious advertising style
- NO perfect stock models
""".strip()


BODY_IMAGE_SYSTEM_PROMPT = """
## Body Section Images – AI Generation Instructions

### Core Goal
Body section images exist to visually explain the exact idea of that section in the 
simplest possible way. Each image must act like a visual translation of the section's 
core message, especially for an older reader.

If someone only skimmed the text + image, they should still "get it".

### Core Rules (Non-Negotiable)

1. **One section = one core idea = one image**
   Before generating any image, define: "What is the single idea this section is 
   trying to explain?" The image must only communicate that idea.
   - No mixing concepts
   - No jumping ahead
   
   Example logic (not prompts):
   - Section talks about treatments being destroyed before reaching lungs → 
     image shows that loss visually
   - Section talks about digestion stopping medication → 
     image shows stomach/liver blocking flow
   - Section talks about direct delivery → 
     image shows clear path to lungs

2. **Images must explain, not decorate**
   Body images are functional, not aesthetic. They must:
   - Simplify a complex idea
   - Reduce mental effort
   - Make the explanation feel obvious
   - If the image can be removed without losing understanding → it FAILED.

3. **Must be understandable for an older reader**
   Assume:
   - Slower reading pace
   - Less tolerance for abstraction
   - Needs clear cause → effect visuals
   
   That means:
   - Simple compositions
   - Clear focus
   - No clutter
   - No clever metaphors that require interpretation

### Static vs GIF / Animation (Important)

#### Static Images (Default)
Use static images when:
- Showing a situation
- Showing a person's condition
- Showing a comparison in a simple way
- Showing "this is happening" moments

Static images should feel:
- Calm
- Clear
- Observational
- Editorial (not ad-like)

#### GIF / Animation (Required for mechanisms)
Use GIFs / subtle animations when explaining a mechanism or process, especially:
- Digestion
- Absorption
- Blockage
- Delivery paths
- Cause-and-effect over time

**In this advertorial, mechanism sections MUST use GIFs.**

Animation rules:
- 2–5 second loop
- Slow, explanatory motion
- No effects, no text overlays
- Motion should clarify, not distract

Think: "Educational animation you'd see in a serious article — simplified."

### How Images Should Relate to the Copy (Critical)
- The image must reflect what the reader just read, not what comes next
- Images should sit exactly where understanding might drop
- They should visually confirm: "Yes, this makes sense now"

Examples applied to copy:
- Stuck mucus section → visual shows mucus physically blocking airways
- 5% problem section → visual shows most of substance disappearing before lungs
- Doctor discovery section → visual shows research, charts, late-night investigation
- Direct delivery vs swallowing → visual shows two paths, one failing, one reaching lungs
""".strip()


PRODUCT_IMAGE_SYSTEM_PROMPT = """
## Product Introduction Images – AI Generation Instructions

### Core Goal
Product introduction images exist to visually prove how the product works the moment 
it is introduced. This is where the reader shifts from:
"I understand the problem" → "I understand why this solution makes sense."

### Core Rules (Non-Negotiable)

1. **Images must match the exact product being sold**
   - The product shown must be identical to the real product
   - Same form factor, delivery method, and usage
   - No generic or "similar-looking" products
   - If the image doesn't match the product → it CANNOT be used.

2. **The image must explain the product's mechanism**
   This is the most important rule. The image must visually demonstrate what makes 
   the product work, not just show it.
   
   If the product works via:
   - Direct delivery
   - Bypassing digestion
   - Targeted absorption
   
   The image must show that process clearly. This is NOT optional.

### Image Types

#### Type 1 — Mechanism GIF / Animation (Primary, Mandatory)
This is the default and preferred format.

Use when:
- Introducing the product
- Explaining why it works better than alternatives
- Showing cause → effect

Typical structure:
- Split screen (recommended)
- One side: the real product
- Other side: animated mechanism (e.g. direct airway delivery)

Animation rules:
- 3–6 second loop
- Clean, slow, explanatory motion
- No text overlays
- No dramatic effects
- Feels educational, not promotional

The animation should answer: "How does this product actually reach the problem area?"

#### Type 2 — Standalone Product Images (Secondary)
Used only to:
- Ground the product visually
- Reinforce legitimacy and realism

Rules:
- Neutral background or realistic environment
- Soft lighting
- No badges, no claims, no CTA
- Clean, calm, credible

These images do not explain — they support.

### Overall Visual Tone
- Educational
- Trustworthy
- Calm
- Clinical-but-human
- Nothing should feel like an ad.
""".strip()


def get_system_prompt_for_image_type(image_type: ImageType) -> str:
    """Return the appropriate system prompt based on image type."""
    prompts = {
        ImageType.HEADLINE: HEADLINE_IMAGE_SYSTEM_PROMPT,
        ImageType.BODY: BODY_IMAGE_SYSTEM_PROMPT,
        ImageType.PRODUCT: PRODUCT_IMAGE_SYSTEM_PROMPT,
    }
    return prompts.get(image_type, BODY_IMAGE_SYSTEM_PROMPT)


def size_for_aspect_ratio(aspect_ratio: str) -> str:
    """Map a "W:H" aspect ratio to the closest size every GPT Image model supports."""
    width, height = (float(part) for part in aspect_ratio.split(":"))
    if width > height:
        return "1536x1024"
    if height > width:
        return "1024x1536"
    return "1024x1024"


class OpenAIImageClient:
    """
    Generates images using OpenAI GPT Image models (default: gpt-image-2.5-flare).

    Returns base64 data URIs for direct embedding in HTML, eliminating
    the need for file storage and separate HTTP requests.

    Supports three image types for advertorial generation:
    - HEADLINE: Curiosity-driven images that force readers to continue
    - BODY: Explanatory images that simplify complex ideas
    - PRODUCT: Product introduction images that demonstrate mechanism

    Usage:
        client = OpenAIImageClient()

        # Headline image (creates curiosity)
        data_uri = await client.generate(
            "A photorealistic ...",
            image_type=ImageType.HEADLINE,
            aspect_ratio="16:9"
        )

        # Body image (explains concept)
        data_uri = await client.generate(
            "A clear visual showing ...",
            image_type=ImageType.BODY,
            aspect_ratio="4:3"
        )

        html = f'<img src="{data_uri}" />'
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        quality: Optional[str] = None,
    ) -> None:
        settings = get_settings()
        self.model = model or settings.openai_image_model
        self.quality = quality or settings.openai_image_quality
        self._api_key = api_key or settings.openai_api_key

    @cached_property
    def client(self) -> AsyncOpenAI:
        # Created on first use so a missing API key surfaces as a request error
        return AsyncOpenAI(api_key=self._api_key, max_retries=3)

    async def generate(
        self,
        prompt: str,
        image_type: ImageType = ImageType.BODY,
        aspect_ratio: str = "4:3",
        max_retries: int = 3,
    ) -> str:
        """
        Generate one image from a text prompt, return as base64 data URI.

        The system prompt is automatically selected based on the image_type to ensure
        the generated image follows the advertorial guidelines:

        - HEADLINE: Creates curiosity, feels editorial/candid, no product/logos
        - BODY: Explains one core idea clearly, simple composition, educational
        - PRODUCT: Shows product mechanism, trustworthy, clinical-but-human

        Args:
            prompt:       Photorealistic description of the image.
            image_type:   Type of advertorial image (HEADLINE, BODY, PRODUCT).
            aspect_ratio: "W:H" ratio, mapped to the closest supported size
                          (landscape 1536x1024, portrait 1024x1536, square 1024x1024).
            max_retries:  Retries after hitting the per-minute image rate limit.

        Returns:
            Base64 data URI string, e.g. "data:image/jpeg;base64,/9j/4AAQ..."
        """
        # Get the appropriate system prompt for this image type
        system_prompt = get_system_prompt_for_image_type(image_type)

        # Combine system prompt with user prompt for better guidance
        full_prompt = f"{system_prompt}\n\n---\n\n## Image Request:\n{prompt}"
        size = size_for_aspect_ratio(aspect_ratio)

        for attempt in range(max_retries + 1):
            try:
                response = await self.client.images.generate(
                    model=self.model,
                    prompt=full_prompt,
                    size=size,
                    quality=self.quality,
                    output_format="jpeg",
                    output_compression=JPEG_COMPRESSION,
                )
                break
            except RateLimitError as e:
                # An empty balance won't recover by waiting; the per-minute limit will
                if e.code == "insufficient_quota" or attempt == max_retries:
                    raise
                wait = RATE_LIMIT_WAIT_SECONDS * (attempt + 1) + random.uniform(0, 2)
                logger.warning(
                    "Image rate limit hit, attempt %d/%d — retrying in %.0fs",
                    attempt + 1,
                    max_retries,
                    wait,
                )
                await asyncio.sleep(wait)

        image = response.data[0] if response.data else None
        if image is None or not image.b64_json:
            raise ValueError("OpenAI image response contained no image data")

        logger.info(
            "Image generated: type=%s size=%s bytes=%d tokens_in=%s tokens_out=%s prompt_preview=%s",
            image_type.value,
            size,
            len(image.b64_json) * 3 // 4,
            getattr(response.usage, "input_tokens", None),
            getattr(response.usage, "output_tokens", None),
            prompt[:80],
        )
        return f"data:image/jpeg;base64,{image.b64_json}"
