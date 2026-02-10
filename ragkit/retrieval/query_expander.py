"""Query expansion strategies for improved retrieval."""

from __future__ import annotations


class QueryExpander:
    """Query expander with multiple expansion strategies.

    Strategies:
    - Synonyms: Add synonyms using WordNet
    - LLM Rewrite: Generate query variants using LLM
    - HyDE: Generate hypothetical document and search for similar docs
    """

    def __init__(self, llm_client=None):
        """Initialize query expander.

        Args:
            llm_client: Optional LLM client for rewrite/HyDE strategies
        """
        self.llm_client = llm_client

    async def expand(
        self,
        query: str,
        strategy: str = "synonyms",
        max_expansions: int = 3,
    ) -> list[str]:
        """Expand query using specified strategy.

        Args:
            query: Original query
            strategy: Expansion strategy ("synonyms", "llm_rewrite", "hyde")
            max_expansions: Maximum number of expanded queries to generate

        Returns:
            List of queries (original + expansions)
        """
        if strategy == "synonyms":
            return self.expand_with_synonyms(query, max_expansions)
        elif strategy == "llm_rewrite":
            return await self.expand_with_llm(query, max_expansions)
        elif strategy == "hyde":
            return await self.hyde(query)
        else:
            raise ValueError(f"Unknown expansion strategy: {strategy}")

    def expand_with_synonyms(
        self, query: str, max_expansions: int = 3
    ) -> list[str]:
        """Expand query by adding synonyms using WordNet.

        Args:
            query: Original query
            max_expansions: Max number of synonyms per word

        Returns:
            List of expanded queries
        """
        try:
            from nltk.corpus import wordnet
        except ImportError:
            # NLTK not available, return original query only
            return [query]

        # Split query into words
        words = query.lower().split()

        expanded_queries = [query]  # Start with original

        # For each word, get synonyms
        for word in words:
            synsets = wordnet.synsets(word)
            synonyms = set()

            for synset in synsets[:max_expansions]:
                for lemma in synset.lemmas():
                    synonym = lemma.name().replace("_", " ")
                    if synonym.lower() != word and synonym not in synonyms:
                        synonyms.add(synonym)

            # Create expanded queries with synonyms
            for synonym in list(synonyms)[:max_expansions]:
                expanded = query.replace(word, synonym, 1)
                if expanded not in expanded_queries:
                    expanded_queries.append(expanded)

        return expanded_queries[:max_expansions + 1]

    async def expand_with_llm(
        self, query: str, num_variants: int = 3
    ) -> list[str]:
        """Expand query by generating variants using LLM.

        Args:
            query: Original query
            num_variants: Number of variants to generate

        Returns:
            List of query variants (original + generated)
        """
        if self.llm_client is None:
            # No LLM available, return original only
            return [query]

        # Prompt template for query rewriting
        prompt = f"""Generate {num_variants} different ways to ask the following question.
Each variant should be semantically similar but use different words or phrasing.

Original question: "{query}"

Provide {num_variants} variants, one per line:"""

        try:
            # Call LLM (implementation depends on client)
            response = await self.llm_client.complete(prompt)

            # Parse response (simple line-based parsing)
            variants = [line.strip() for line in response.split("\n") if line.strip()]

            # Return original + variants
            return [query] + variants[:num_variants]

        except Exception as e:
            print(f"LLM expansion failed: {e}")
            return [query]

    async def hyde(self, query: str) -> list[str]:
        """Generate hypothetical document for query (HyDE strategy).

        HyDE: Generate a hypothetical answer to the query, then search for
        documents similar to that answer.

        Args:
            query: Original query

        Returns:
            List containing hypothetical document
        """
        if self.llm_client is None:
            # No LLM available, return original query
            return [query]

        # Prompt for generating hypothetical answer
        prompt = f"""Given this question, write a detailed answer that directly addresses it.
Be specific and informative.

Question: "{query}"

Answer:"""

        try:
            # Generate hypothetical document
            hypothetical_doc = await self.llm_client.complete(prompt)

            # Return hypothetical document (will be embedded and searched)
            return [hypothetical_doc]

        except Exception as e:
            print(f"HyDE generation failed: {e}")
            return [query]
