from pydantic import BaseModel, Field

from ddgs import DDGS
from tavily import TavilyClient

from tools.base import Tool, ToolInvocation, ToolKind, ToolResult
from tools.registry import register_tool


class WebSearchParams(BaseModel):
    query: str = Field(..., description="Search query")
    max_results: int = Field(
        10,
        ge=1,
        le=20,
        description="Maximum number of results to return (default: 10)",
    )


@register_tool
class WebSearchTool(Tool):
    name = "web_search"
    description = "Search the web for information. Returns search results with titles, URLs and snippets."
    kind = ToolKind.NETWORK
    schema = WebSearchParams

    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = WebSearchParams(**invocation.params)
        query = params.query
        max_results = params.max_results

        use_tavily = self.config.web_api_key is not None
        try:
            # ? check with Tavily first, then use duckduckgo as fallback search
            if use_tavily:
                results = TavilyClient(
                    api_key=self.config.web_api_key,
                ).search(
                    query=query,
                    max_results=max_results,
                )
            else:
                results = DDGS().search(
                    query=query,
                    region="us-en",
                    safesearch="off",
                    timelimit="y",
                    page=1,
                    backend="auto",
                    max_results=max_results,
                )
        except Exception as e:
            return ToolResult.error_result(f"Search failed: {e}")

        if not results:
            return ToolResult.success_result(
                f"No results found for query '{query}'",
                metadata={
                    "query": query,
                    "results": 0,
                },
            )
        output_lines = [f"Search results for query: {query}"]
        for i, result in enumerate(results, 1):
            output_lines.append(f"{i}. Title: {result.get('title', '')}")
            output_lines.append(f"    URL: {result.get('href', 'Unknown URL')}")
            if result.get("body"):
                output_lines.append(f"    Snippet: {result['body']}")

            output_lines.append("")

        return ToolResult.success_result(
            "\n".join(output_lines),
            metadata={
                "query": query,
                "results": len(results),
            },
        )
