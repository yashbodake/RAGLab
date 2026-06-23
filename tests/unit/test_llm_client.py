import pytest
from unittest.mock import AsyncMock, patch
from backend.services.llm import LLMClient, build_user_prompt, approx_token_count
from backend.models.schemas import ChunkResult, ChunkScores, Classification

@pytest.mark.unit
def test_approx_token_count():
    """Verify word-based token estimate is 1.3x."""
    text = "The quick brown fox jumps"
    # 5 words * 1.3 = 6.5 -> int(6.5) = 6
    assert approx_token_count(text) == 6

@pytest.mark.unit
def test_build_user_prompt():
    """Verify prompt formatting and instructions based on classification."""
    chunks = [
        ChunkResult(
            id="doc1",
            text="First document text.",
            metadata={"source": "maintenance_manual", "error_code": "E430", "product": "switch"},
            scores=ChunkScores(dense=0.9),
            rank=1
        )
    ]
    clf = Classification(type="COMPARE", top_k=5, sub_queries=["X", "Y"])
    
    prompt = build_user_prompt("E430 vs E440", chunks, clf)
    assert "[Source 1: maintenance_manual, Error: E430, Product: switch]" in prompt
    assert "First document text." in prompt
    assert "comparison question" in prompt
    assert "E430 vs E440" in prompt

@pytest.mark.unit
@pytest.mark.asyncio
async def test_llm_stream_completion():
    """Verify LLM client streams tokens back correctly using mocked openai response."""
    # Mock AsyncOpenAI client
    with patch("backend.services.llm.AsyncOpenAI") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        
        # Mock completions.create stream response
        mock_stream = AsyncMock()
        mock_choices = [
            AsyncMock(delta=AsyncMock(content="To")),
            AsyncMock(delta=AsyncMock(content=" resolve")),
            AsyncMock(delta=AsyncMock(content=" error."))
        ]
        
        # Async generator for openai stream chunks
        async def mock_async_iter():
            for choice in mock_choices:
                chunk = AsyncMock(choices=[choice])
                yield chunk
                
        mock_stream.__aiter__.side_effect = mock_async_iter
        mock_client.chat.completions.create = AsyncMock(return_value=mock_stream)
        
        # Initialize client and call completion
        os_environ_patch = {"CEREBRAS_API_KEY": "test-key"}
        with patch.dict("os.environ", os_environ_patch):
            client = LLMClient()
            tokens = []
            async for token in client.stream_completion("system prompt", "user prompt"):
                tokens.append(token)
                
            assert "".join(tokens) == "To resolve error."
