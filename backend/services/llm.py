import os
from typing import AsyncGenerator, List
from openai import AsyncOpenAI
from backend.models.schemas import ChunkResult, Classification

SYSTEM_PROMPT = (
    "You are RAGLab, the retrieval-augmented assistant powering the RAGLab\n"
    "terminal — an industrial knowledge and troubleshooting system.\n\n"
    "IDENTITY:\n"
    "- Your name is RAGLab. You were developed by Yash Bodake.\n"
    "- Your source code is open and lives at https://github.com/yashbodake/RAGLab\n"
    "- You speak with a calm, precise, confident voice — like a seasoned field\n"
    "  engineer who has seen every machine in the plant. Direct, never chatty,\n"
    "  never flowery. You respect the reader's time.\n\n"
    "WHEN ASKED ABOUT YOURSELF (who made you, what you are, your identity):\n"
    "- State plainly: \"I'm RAGLab, built by Yash Bodake. My code is open source\n"
    "  at github.com/yashbodake/RAGLab.\" Keep it to one or two sentences.\n"
  "\n"
    "GROUND RULES FOR ANSWERS:\n"
    "1. Answer ONLY based on the provided context chunks. Do not use external\n"
    "   knowledge for technical questions.\n"
    "2. If the context does not contain enough information to answer, say so\n"
    "   explicitly rather than guessing.\n"
    "3. Reference the source documents when citing information (e.g., \"Per the\n"
    "   maintenance manual...\").\n"
    "4. Be concise and actionable. Use numbered steps for procedures.\n"
    "5. For error codes, always state the code, its meaning, and resolution steps.\n"
    "6. For comparisons, structure your response with clear sections for each topic.\n"
    "7. Use markdown — tables, lists, code blocks, and **bold** where it aids clarity."
)

class LLMClient:
    """Cerebras async LLM client manager."""

    def __init__(self):
        api_key = os.environ.get("CEREBRAS_API_KEY")
        if not api_key:
            raise RuntimeError("CEREBRAS_API_KEY environment variable is required")

        self.client = AsyncOpenAI(
            base_url="https://api.cerebras.ai/v1",
            api_key=api_key,
        )
        self.model = "gpt-oss-120b"

    async def stream_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.3,
        history: list = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream completion tokens from Cerebras.

        Args:
            history: Optional prior conversation turns as [{"role","content"}] dicts.
                     When provided, they're inserted between system + user prompts so
                     the model has multi-turn context.

        Yields:
            Individual text tokens/fragments as they arrive.
        """
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            # Cap to last 6 turns to stay within token budget on the free tier.
            for turn in history[-6:]:
                messages.append({"role": turn.get("role", "user"), "content": turn.get("content", "")})
        messages.append({"role": "user", "content": user_prompt})

        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def suggest_followups(self, query: str, answer: str) -> List[str]:
        """
        Generate 3 concise follow-up questions based on the user's query and
        the assistant's answer. Non-streaming (small, fast call).
        """
        prompt = (
            "Based on this Q&A, suggest exactly 3 short follow-up questions the user "
            "might ask next. Return ONLY the questions, one per line, numbered 1-3. "
            "Do not include any other text.\n\n"
            f"Question: {query}\n\nAnswer: {answer[:1200]}"
        )
        resp = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You generate concise follow-up questions."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=160,
            temperature=0.5,
            stream=False,
        )
        raw = resp.choices[0].message.content or ""
        # Parse numbered lines, strip the "1." prefixes, cap at 3.
        lines = []
        for line in raw.strip().split("\n"):
            clean = line.strip()
            if not clean:
                continue
            # Remove leading "1.", "1)", "1 -" etc.
            clean = clean.lstrip("0123456789.").strip(") ").strip(" -").strip()
            if clean:
                lines.append(clean)
        return lines[:3]

def build_user_prompt(
    query: str,
    chunks: List[ChunkResult],
    classification: Classification
) -> str:
    """
    Build the user prompt with retrieved context.
    """
    # Format context chunks
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.metadata.get("source", "unknown")
        error_code = chunk.metadata.get("error_code", "")
        product = chunk.metadata.get("product", "")

        header_parts = [f"[Source {i}: {source}"]
        if error_code:
            header_parts.append(f"Error: {error_code}")
        if product:
            header_parts.append(f"Product: {product}")
        header = ", ".join(header_parts) + "]"

        context_parts.append(f"{header}\n{chunk.text}")

    context_block = "\n\n---\n\n".join(context_parts)

    # Classification-specific instructions
    if classification.type == "COMPARE":
        instruction = (
            "The user is asking a comparison question. "
            "Structure your response with clear sections comparing the two topics. "
            "Highlight key differences and similarities."
        )
    elif classification.type == "FACT":
        instruction = (
            "The user is asking a factual question. "
            "Provide a direct, concise answer. "
            "If it involves an error code, include the code, meaning, and fix steps."
        )
    else:  # TOPIC
        instruction = (
            "The user is asking about a broad topic. "
            "Provide a comprehensive overview based on the context. "
            "Use headings or bullet points for clarity."
        )

    return f"""Context:
{context_block}

---

Instruction: {instruction}

Question: {query}"""

def approx_token_count(text: str) -> int:
    """Rough token estimate: ~1.3 tokens per word for English."""
    return int(len(text.split()) * 1.3)
