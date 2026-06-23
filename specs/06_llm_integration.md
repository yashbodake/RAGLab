# LLM Integration (Cerebras)

## Setup
- Library: `openai` with `AsyncOpenAI`.
- Base URL: `https://api.cerebras.ai/v1`
- API key: `CEREBRAS_API_KEY` env var.
- Model: `llama3.1-8b`

## Client Initialization

```python
from openai import AsyncOpenAI

class LLMClient:
    def __init__(self):
        api_key = os.environ.get("CEREBRAS_API_KEY")
        if not api_key:
            raise RuntimeError("CEREBRAS_API_KEY environment variable is required")

        self.client = AsyncOpenAI(
            base_url="https://api.cerebras.ai/v1",
            api_key=api_key,
        )
        self.model = "llama3.1-8b"

    async def stream_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.3,
    ) -> AsyncGenerator[str, None]:
        """
        Stream completion tokens from Cerebras.

        Yields:
            Individual text tokens/fragments as they arrive.
        """
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
```

## Generation Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| `temperature` | 0.3 | Low creativity; factual industrial answers |
| `max_tokens` | 1024 | Sufficient for detailed troubleshooting steps |
| `stream` | `true` | Always stream for responsive UX |
| `top_p` | 1.0 (default) | Not explicitly set; temperature handles variance |

## Prompt Template

### System Prompt

```
You are an expert industrial support assistant. Your role is to help engineers
and technicians troubleshoot equipment, understand maintenance procedures,
and resolve operational issues.

Rules:
1. Answer ONLY based on the provided context chunks. Do not use external knowledge.
2. If the context does not contain enough information to answer, say so explicitly.
3. Reference the source documents when citing information (e.g., "According to
   the maintenance manual...").
4. Be concise and actionable. Use numbered steps for procedures.
5. For error codes, always state the error code, its meaning, and resolution steps.
6. If comparing two topics, structure your response with clear sections for each.
```

### User Prompt Construction

```python
def build_user_prompt(
    query: str,
    chunks: list[ChunkResult],
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
```

### Example Constructed Prompt

**For a FACT query: "How to fix error E452 on server?"**

```
Context:
[Source 1: maintenance_manual, Error: E452, Product: server]
To resolve error E452, first check the power supply unit connections.
Ensure all cables are properly seated. If the error persists, the PSU
may need replacement. Contact your supplier for a compatible unit
rated at minimum 750W.

---

[Source 2: troubleshooting_guide, Error: E452, Product: server]
Error E452 indicates a power delivery fault. Common causes include:
loose power cables, degraded PSU, or overloaded circuits. This error
is critical and should be resolved within 4 hours to prevent data loss.

---

[Source 3: release_notes, Error: E452, Product: server]
Firmware v2.4.1 improved E452 detection accuracy, reducing false
positives by 40%. Update firmware before replacing hardware.

---

Instruction: The user is asking a factual question. Provide a direct, concise answer. If it involves an error code, include the code, meaning, and fix steps.

Question: How to fix error E452 on server?
```

## Error Handling

| Error | Handling |
|-------|----------|
| API key missing | Raise `RuntimeError` at startup — fail fast |
| Rate limit (429) | Log warning, send SSE `error` event with retry delay |
| Timeout | 30s timeout per request; send SSE `error` event |
| Invalid response | Log full error server-side, send generic SSE `error` event |
| Stream interruption | Finalize partial message, send SSE `done` event |

## Token Counting (Approximate)

For metrics reporting, approximate token count using whitespace splitting:
```python
def approx_token_count(text: str) -> int:
    """Rough token estimate: ~1.3 tokens per word for English."""
    return int(len(text.split()) * 1.3)
```

This is used for logging purposes only, not for prompt truncation. Context window management relies on limiting `top_k` chunks.