"""
Copy Parser
===========

Uses LLM to parse raw advertorial copy into structured sections.
"""

import logging

from app.services.agents.llm_client import OpenAIClient
from app.services.agents.copy_injection.schemas import ParsedCopy

logger = logging.getLogger(__name__)


COPY_PARSER_PROMPT = '''You are an expert at analyzing advertorial/marketing copy.

Given the raw advertorial copy below, extract and categorize the content into structured sections.

## Instructions:
1. Identify the main HEADLINE - usually the first attention-grabbing statement
2. Look for a SUBHEADLINE - secondary headline that expands on the main one
3. Find the HOOK - opening text that grabs attention (often emotional or provocative)
4. Extract the INTRODUCTION - opening paragraphs that set up the story/problem
5. Generate POST CATEGORY - a short category label for the article (ALWAYS REQUIRED!)
   - Based on the content, generate an appropriate category like: "Health", "Wellness", "Medical Research", "Natural Remedies", "Weight Loss", "Heart Health", "Digestive Health", "Joint Health", "Brain Health", "Skin Care", "Anti-Aging", etc.
   - This should be 1-3 words maximum
6. Identify BODY SECTIONS - main content broken into logical sections:
   - Create 3-5 body sections MAXIMUM (not more than 5!)
   - Each section should be MAX 150 WORDS (keep it SHORT and punchy!)
   - Use SHORT PARAGRAPHS: 2-3 sentences max per paragraph
   - VARY THE RHYTHM between sections - don't use the same pattern every time!
   - Use fragment sentences for dramatic effect ("Nothing worked." / "Three weeks later.")
   - Include specific details (names, ages, numbers, timeframes)
   - Each section should feel like a mini-chapter of the story
   - Create a clear, compelling title for each section
7. Find PRODUCT PRESENTATION:
   - Extract a clear product section title (e.g., "Introducing [Product Name]", "The Solution", "What is [Product]?")
   - Extract the product description and benefits
   - For SOLUTION DISCOVERY TITLE: Extract or create a compelling title for the product discovery section (e.g., "The Discovery", "How I Found The Answer", "A Breakthrough Solution")
   - For PRODUCT REVEAL: Extract the dramatic reveal text that introduces the product (the moment of discovery/revelation)
8. Extract SOCIAL PROOFS - expert quotes, study references, authority endorsements
   - Keep each social proof BRIEF: 1-2 sentences MAX
   - These must be UNIQUE - each social proof should be from a DIFFERENT person/source
   - Do NOT duplicate the same person
   - Format: "[Short quote]" – [Name], [Title/Credentials]
9. Identify MAIN SOCIAL PROOF - scientific studies, statistics, or research backing
   - Extract a title for this section
   - Extract the content (study details, statistics, expert endorsements)
   - Keep it CONCISE - focus on key numbers and findings
10. Find CASE STUDY - a detailed story of a specific person's experience/transformation
   - Look for named individuals with detailed stories (e.g., "Maria's story", "John discovered...")
   - Extract a compelling title for the case study section (e.g., "Maria's Story", "How John Found Relief")
   - Extract the full narrative of their journey/transformation
   - This should be a SINGLE detailed story, not multiple short mentions
   - Format the case study content with HTML tags just like body sections (<br><br> for paragraphs, <b> for bold)
11. Extract REVIEWS/TESTIMONIALS - CRITICAL FORMATTING RULES:
    - Keep reviews SHORT: 2-4 sentences MAXIMUM!
    - Write like REAL HUMANS - casual, not polished marketing speak
    - Include small imperfections (not every review should be 100% positive)
    - Mention SPECIFIC results or timeframes ("after 2 weeks", "in 3 days")
    - VARY the tone: some enthusiastic, some matter-of-fact, some casual
    - Each review MUST have a UNIQUE person name
    - Do NOT repeat the same reviewer
    - Extract 3-5 unique reviews maximum
    
    BAD Review Example (too generic, avoid this):
    "This product changed my life! I can't believe how amazing it is. I recommend it to everyone! Best decision I ever made!"
    
    GOOD Review Examples (human-like, use these styles):
    - "Took about 2 weeks to notice anything. Now I'm sleeping through the night. Wish I found this sooner."
    - "Not perfect, but way better than what I tried before. My husband noticed the difference first."
    - "Works. Simple as that. No weird side effects either."
    - "Honestly was skeptical at first. 3 weeks in and... okay, I'm impressed."
    - "Finally something that actually does what it says. Been recommending it to friends."
    
12. Identify the OFFER section (IMPORTANT - always extract or create!):
    - Extract call-to-action text, pricing info, urgency elements, bonuses
    - Create a compelling offer title (e.g., "Limited Time Offer", "Special Deal", "Exclusive Discount")
    - The offer content should summarize: what they get, any discounts/bonuses, urgency/scarcity
    - If no explicit offer exists, create one based on the product being promoted
    - ALWAYS fill the offer section - it's required for the landing page!
13. Find REFERENCES - any citations, sources, disclaimers
14. For LISTICLE ITEMS (template_004):
    - Keep each listicle item text CONCISE: MAX 70 words per item
    - Use numbered titles: "1. [Title]", "2. [Title]", etc.
    - Focus on ONE key point per item
    - Make it scannable - readers should get the gist quickly

## BODY SECTION HTML FORMATTING (IMPORTANT!):
The body section content AND case study content will be inserted directly into HTML. You MUST return HTML-formatted content for both:

- Use <br><br> for paragraph breaks (new paragraphs)
- Use <br> for single line breaks (for dramatic pause/breathing room)
- Use <b>text</b> for bold/emphasis on key phrases
- Use <i>text</i> for italic emphasis
- DO NOT use \\n or \\n\\n - use HTML tags only!

## BODY SECTION RHYTHM EXAMPLES (VARY THESE!):

Rhythm A - Story Opening:
"Maria was 47 when it started. Every morning, the same struggle.<br><br>The alarm rings at 6 AM. But getting up? <b>Impossible</b>."

Rhythm B - Building Tension:
"She tried pills. Then tea. Then meditation.<br><br>Nothing worked.<br><br>Three months later, it got worse."

Rhythm C - Emotional Beat:
"<i>'I couldn't do it anymore,'</i> she says today.<br><br>Dark circles. Exhausted. Hopeless."

Rhythm D - Cliffhanger:
"That's when she found something unexpected.<br><br>Something her doctors had dismissed for years."

## CRITICAL RULES:
- POST CATEGORY is ALWAYS REQUIRED - generate an appropriate category based on the content!
- Body sections MAX 150 WORDS - short paragraphs, varied rhythm!
- Reviews MAX 2-4 SENTENCES - human-like, not marketing speak!
- Social proofs MAX 1-2 SENTENCES each - brief and credible!
- Listicle items MAX 70 WORDS - concise and scannable!
- Body section content MUST use HTML tags (<br>, <b>, <i>) - NO \\n characters!
- Maximum 5 body sections total
- Each body section MUST have a title
- Product presentation MUST have a title
- Case study MUST have both a title AND content if a detailed personal story exists in the copy
- Main social proof MUST have both a title AND content if scientific backing exists
- All reviews must be from DIFFERENT people (unique names)
- All social proofs must be from DIFFERENT sources
- If something doesn't exist in the copy, leave it null/empty - do NOT invent content (except post_category which must always be generated)

## Raw Advertorial Copy:
{raw_copy}

## Additional Context:
{context}

Extract all identifiable sections and return the structured data.
'''


class CopyParser:
    """Parses raw advertorial copy into structured sections using LLM."""

    def __init__(self) -> None:
        self.llm = OpenAIClient()

    async def parse(
        self,
        raw_copy: str,
        product_name: str | None = None,
        product_category: str | None = None,
    ) -> ParsedCopy:
        """
        Parse raw advertorial copy into structured sections.

        Args:
            raw_copy: The raw advertorial copy text
            product_name: Optional product name hint
            product_category: Optional product category hint

        Returns:
            ParsedCopy with all identified sections
        """
        # Build context string
        context_parts = []
        if product_name:
            context_parts.append(f"Product Name: {product_name}")
        if product_category:
            context_parts.append(f"Product Category: {product_category}")
        context = "\n".join(context_parts) if context_parts else "No additional context provided."

        # Format the prompt
        prompt = COPY_PARSER_PROMPT.format(
            raw_copy=raw_copy,
            context=context,
        )

        logger.info(
            "Parsing copy: length=%d, product=%s, category=%s",
            len(raw_copy),
            product_name,
            product_category,
        )

        # Use structured output to get parsed copy
        parsed = await self.llm.generate_structured(
            prompt=prompt,
            schema=ParsedCopy,
        )

        logger.info(
            "Parsed copy: headline=%s, body_sections=%d, reviews=%d, social_proofs=%d",
            parsed.headline[:50] if parsed.headline else "None",
            len(parsed.body_sections),
            len(parsed.reviews),
            len(parsed.social_proofs),
        )

        # Debug log for case study and main social proof
        logger.info(
            "Parsed extras: case_study_title=%s, case_study_len=%d, main_social_proof_title=%s",
            parsed.case_study_title[:30] if parsed.case_study_title else "NONE",
            len(parsed.case_study) if parsed.case_study else 0,
            parsed.main_social_proof_title[:30] if parsed.main_social_proof_title else "NONE",
        )

        return parsed

