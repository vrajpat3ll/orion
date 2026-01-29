import re
from urllib.parse import urlparse
import httpx
from pydantic import BaseModel, Field

from tavily import TavilyClient

from tools.base import Tool, ToolInvocation, ToolKind, ToolResult
from tools.registry import register_tool


class WebFetchParams(BaseModel):
    url: str = Field(..., description="URL to fetch (must be http:// or https://)")
    timeout: int = Field(
        120,
        ge=5,
        le=600,
        description="Request timeout in seconds (default: 120)",
    )


@register_tool
class WebSearchTool(Tool):
    name = "web_fetch"
    description = "Fetch content from a URL. Returns the response body as text."
    kind = ToolKind.NETWORK
    schema = WebFetchParams

    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = WebFetchParams(**invocation.params)

        url = params.url
        timeout = params.timeout

        url_pat = "^https?:\\/\\/(?:www\\.)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b(?:[-a-zA-Z0-9()@:%_\\+.~#?&\\/=]*)$"

        parsed = urlparse(url)
        if not parsed.scheme or parsed.scheme not in ("http", "https"):
            return ToolResult.error_result(
                f"Invalid URL (must have http:// or https://): {url}"
            )
        if not re.match(url_pat, url):
            return ToolResult.error_result(f"Invalid URL: {url}")

        use_tavily = self.config.web_api_key is not None
        try:
            # ? check with Tavily first, then use httpx as fallback fetch
            if use_tavily:
                with TavilyClient(
                    api_key=self.config.web_api_key,
                ) as client:
                    response = client.extract(
                        urls=url,
                        timeout=timeout,
                    )
                results = response.get("results", [])
                text = ""
                if results:
                    text = "\n".join(
                        [
                            result.get("raw_content")
                            for result in results
                            if result.get("error") is None
                        ]
                    )
            else:
                async with httpx.AsyncClient(
                    timeout=timeout,
                    follow_redirects=True,
                ) as client:
                    response = await client.get(url=url)
                    response.raise_for_status()
                text = response.text
        except httpx.HTTPStatusError as e:
            return ToolResult.error_result(
                f"HTTP {e.response.status_code}: {e.response.reason_phrase}",
            )
        except Exception as e:
            return ToolResult.error_result(f"Request failed: {e}")
        if len(text) > 100 * (1 << 10):
            text = text[: 100 * (1 << 10)] + "\n...[content truncated]"

        return ToolResult.success_result(
            output=text,
            metadata={
                "status_code": response.status_code if not use_tavily else None,
                "content_length": len(response.content)
                if not use_tavily
                else len(response.get("results")[0].get("raw_content")),
            },
        )
