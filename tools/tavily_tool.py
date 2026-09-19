from tavily import TavilyClient
import os
from dotenv import load_dotenv

load_dotenv()

client = TavilyClient( api_key= os.getenv("TAVILY_API_KEY"))

def tavily_search(query: str):
    response = client.search(
        query = query,
        max_results= 5
    )
    results = []

# Create an empty list. We will store each cleaned/formatted search result inside this list.
    for i, result in enumerate(response["results"], 1):

    # response["results"] contains the list of results returned by Tavily.
    
    # enumerate(..., 1) gives us:
    # i      → result number (1, 2, 3, ...)
    # result → the actual result dictionary
        title = result.get("title", "Unknown")

    # Get the title from the result. .get() safely retrieves the value. If "title" doesn't exist, use "Unknown" instead.
        url = result.get("url", "")

    # Get the URL of the search result. If no URL exists, use an empty string.
        content = result.get("content", "")

    # Get the actual text/content returned by Tavily. If content doesn't exist, use an empty string.
        results.append(
            f"{i}. {title}\n"
            f"URL: {url}\n"
            f"{content}"
        )

    # Create a readable string containing:
    # 1. Result number + title
    # URL, Content
    
    # Then add that formatted string to our results list.


    return "\n\n".join(results)

# results is currently a LIST of strings.

# "\n\n".join(results) combines all those strings into
# ONE string, putting two newline characters between them.

# This gives the agent a clean text response instead of  the large raw Tavily dictionary.

#print(tavily_search("best places to visit in Mumbai"))