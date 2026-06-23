import re
from backend.models.schemas import Classification

class QueryRouter:
    """Classifies queries to optimize retrieval parameters and sub-queries."""

    @staticmethod
    def classify(query: str, query_understanding: bool) -> Classification:
        if not query_understanding:
            return Classification(type="FACT", top_k=5, sub_queries=None)

        query_lower = query.lower().strip()

        # Check COMPARE first (most specific)
        compare_pattern = r"difference between|vs\.?|compare|comparison"
        if re.search(compare_pattern, query_lower):
            # Extract entities around the compare keyword
            entities = QueryRouter.extract_compare_entities(query.strip())
            # Clean and filter empty sub-queries
            sub_queries = [entity.strip() for entity in entities if entity.strip()]
            if not sub_queries:
                sub_queries = [query.strip()]
            return Classification(type="COMPARE", top_k=5, sub_queries=sub_queries)

        # Check FACT: short question
        word_count = len(query_lower.split())
        if word_count <= 8 and query_lower.endswith("?"):
            return Classification(type="FACT", top_k=3, sub_queries=None)

        # Default: TOPIC
        return Classification(type="TOPIC", top_k=7, sub_queries=None)

    @staticmethod
    def extract_compare_entities(query: str) -> list[str]:
        """Split query around comparison keywords to find the two entities."""
        query_clean = query.strip()
        
        # Check "difference between X and Y"
        diff_match = re.search(r"difference between\s+(.+?)\s+and\s+(.+)", query_clean, re.IGNORECASE)
        if diff_match:
            return [diff_match.group(1).strip(), diff_match.group(2).strip()]
            
        # Check "compare X and Y" / "comparison of X and Y"
        comp_match = re.search(r"(?:compare|comparison of)\s+(.+?)\s+and\s+(.+)", query_clean, re.IGNORECASE)
        if comp_match:
            return [comp_match.group(1).strip(), comp_match.group(2).strip()]

        # Other split patterns
        split_patterns = [r"\s+vs\.?\s+", r"\s+versus\s+", r"\s+compared\s+to\s+"]
        for pattern in split_patterns:
            parts = re.split(pattern, query_clean, flags=re.IGNORECASE, maxsplit=1)
            if len(parts) == 2:
                return [parts[0].strip(), parts[1].strip()]
                
        # Fallback: treat as single query
        return [query_clean]
