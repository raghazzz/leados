import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import EmailActivity
from app.services.lead_service import get_lead
from app.core.config import settings

logger = logging.getLogger(__name__)

EMAIL_PROMPTS = {
    "outreach": """You are an expert B2B sales copywriter.
Write a personalised cold outreach email for this lead:

- Name: {name}
- Title: {title}
- Company: {company}
- Industry: {industry}
- Company size: {company_size}

Product being sold: LeadOS — an AI platform that helps sales teams
automatically score leads and send personalised outreach at scale.

Rules:
- Subject line must mention their company or role specifically
- Show you understand their industry in the opening line
- Mention one pain point relevant to their role
- One clear benefit of LeadOS
- Soft CTA — suggest a 15 minute call, not "buy now"
- Under 150 words total
- Friendly and conversational, not robotic

Reply in exactly this format:
SUBJECT: <subject line here>
BODY:
<email body here>""",

    "follow_up_1": """Write a short friendly follow-up email.
The lead did not reply to the first outreach.

Lead: {name} at {company}, their title is {title}

Rules:
- Under 80 words
- Reference that you reached out before
- Try a different angle or benefit
- End with a simple yes or no question

Reply in exactly this format:
SUBJECT: <subject line here>
BODY:
<email body here>""",

    "follow_up_2": """Write a final breakup email for a lead
who has not replied to 2 previous emails.

Lead: {name} at {company}

Rules:
- Under 60 words
- Be respectful and warm
- Say you won't reach out again unless they want
- Leave the door open

Reply in exactly this format:
SUBJECT: <subject line here>
BODY:
<email body here>""",
}


def _parse_email(text: str) -> tuple[str, str]:
    """Split the AI response into subject and body."""
    lines = text.strip().split("\n")
    subject = ""
    body_lines = []
    in_body = False

    for line in lines:
        if line.startswith("SUBJECT:"):
            subject = line.replace("SUBJECT:", "").strip()
        elif line.strip() == "BODY:":
            in_body = True
        elif in_body:
            body_lines.append(line)

    return subject, "\n".join(body_lines).strip()


async def _call_mistral(prompt: str) -> tuple[str, str]:
    """Send the prompt to Mistral and get back subject + body."""

    if not settings.MISTRAL_API_KEY:
        logger.warning("MISTRAL_API_KEY not set — returning placeholder email.")
        return (
            "Quick question about your sales process",
            "Hi there,\n\nI wanted to reach out about LeadOS and how it could help your team qualify leads faster.\n\nWould a quick 15 minute call make sense this week?\n\nBest,\nThe LeadOS Team",
        )

    try:
        import httpx

        headers = {
            "Authorization": f"Bearer {settings.MISTRAL_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": settings.MISTRAL_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 400,
            "temperature": 0.7,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            text = data["choices"][0]["message"]["content"]
            return _parse_email(text)

    except Exception as e:
        logger.error(f"Mistral call failed: {e}")
        return "Error generating email", f"Generation failed: {e}"


async def generate_lead_email(
    db: AsyncSession,
    lead_id: str,
    email_type: str = "outreach",
    custom_context: Optional[str] = None,
) -> Optional[EmailActivity]:
    """Generate and save a personalised email for a lead."""

    lead = await get_lead(db, lead_id)
    if not lead:
        return None

    prompt_template = EMAIL_PROMPTS.get(email_type, EMAIL_PROMPTS["outreach"])
    prompt = prompt_template.format(
        name=lead.name,
        title=lead.title or "Sales Leader",
        company=lead.company or "your company",
        industry=lead.industry or "your industry",
        company_size=lead.company_size or "your team",
    )

    if custom_context:
        prompt += f"\n\nExtra context to use: {custom_context}"

    subject, body = await _call_mistral(prompt)

    email_record = EmailActivity(
        lead_id=lead_id,
        subject=subject,
        body=body,
        email_type=email_type,
        sequence_number={
            "outreach": 1,
            "follow_up_1": 2,
            "follow_up_2": 3
        }.get(email_type, 1),
        generated_by=settings.MISTRAL_MODEL,
    )
    db.add(email_record)
    await db.flush()

    return email_record