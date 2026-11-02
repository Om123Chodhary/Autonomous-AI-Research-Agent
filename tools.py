import time
import requests
import json
import asyncio
from openai import OpenAI 
import os
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
from webless import search_sync

load_dotenv()

api_key = os.getenv("GROQ_API_KEY_1") or os.getenv("GROQ_API_KEY_3")

# Groq Client setup
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=api_key
)
MODEL = os.getenv("MODEL", "llama3-70b-8192")

def verify_finding(session_id: str,source: str, finding: str, evidence: str) -> dict:
    print(f"\n[Verifier] Checking: '{finding}'")
    system_prompt = (
        "You are an evidence verification assistant. "
        "Determine whether the supplied evidence supports the supplied finding. "
        "Return JSON with exactly two fields: 'supported' (boolean) and 'explanation' (string)."
    )
    
    user_prompt = f"Source: {source}\nFinding: {finding}\nEvidence: {evidence}"

    # Groq API Call
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"} # Groq JSON mode
    )
    
    try:
        result = json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        result = {"supported": False, "explanation": "Failed to parse JSON"}
        
    if result.get("supported") is True:
        print(f"✅ Supported. Marking as verified.")
        mark_note_verified(session_id,source, finding)
    else:
        print(f"❌Not supported: {result.get('explanation')}")
        
    return result
def clear_research_notes(session_id: str):
    """Clears the notes for a specific user session."""
    research_notes_db[session_id] = []

research_notes_db = {}
def add_research_note(session_id: str,source: str, finding: str, evidence: str) -> dict:
    """
    Adds a structured research finding to the notes.
    Use this tool to save important information you find on the web.
    
    Args:
        source: The URL or name of the website.
        finding: The key important point (summary).
        evidence: The exact quote or supporting text from the page.
        
    Returns:
        A confirmation dictionary.
    """

    if session_id not in research_notes_db:
        research_notes_db[session_id] = []

    note = {
        "source": source,
        "finding": finding,
        "evidence": evidence,
        "verified": False
    }
    
    research_notes_db[session_id].append(note)
    print(f"\n[Note Saved] {finding}")
    
    return {
        "status": "stored",
        "verified": False,
        "finding": finding
    }

def mark_note_verified(session_id: str, source: str, finding: str) -> dict:
    if session_id in research_notes_db:
        for note in research_notes_db[session_id]:
            if note["source"] == source and note["finding"] == finding:
                note["verified"] = True
                print(f"\n[Note Verified] {finding}")
                return {"status": "verified", "finding": finding}
    return {"status": "not found", "finding": finding}

def get_verified_research_notes(session_id: str) -> list:
    """
    Returns ONLY the verified research notes for final report generation.
    """
    if session_id not in research_notes_db:
        return []
    return [note.copy() for note in research_notes_db[session_id] if note["verified"] == True]


def get_research_notes(session_id: str) -> list:
    """
    Returns all research notes collected so far in this session.
    Use this tool to review all findings before writing the final report.
    """
    if session_id not in research_notes_db:
        return []
    return [note.copy() for note in research_notes_db[session_id]]

async def search_web(query, max_results=7):
        
    try:
        max_results = int(max_results)
    except:
        max_results = 3
    
    try:
        # webless search function
        result = await asyncio.to_thread(search_sync, query, limit=max_results)
        
        results = []
        for hit in result:
            results.append({
                "title": hit.title,
                "url": hit.url,
                "snippet": hit.snippet
            })
         # 🚨 LOGGING ADD KAREIN
        print(f"[SEARCH SUCCESS] Found {len(results)} results for: {query}")
        return results
        
    except Exception as e:
        # 🚨 ERROR LOGGING
        print(f"[SEARCH ERROR] Failed to search for '{query}'. Error: {e}")
        return []

def read_webpage(url):
    """
    Download a webpage and extract its text.

    Args:
        url: Webpage URL.

    Returns:
        Extracted webpage text.
    """
    if url.lower().endswith('.pdf') or '.pdf' in url:
        return "Error: Cannot read PDF files. Please choose an HTML webpage (not a PDF) from the search results."

    if url.startswith("//"):
        url = "https:" + url

    # Extract the real URL from 
    #  DuckDuckGo redirect URL
    parsed_url = urlparse(url)

    if "duckduckgo.com" in parsed_url.netloc:
        params = parse_qs(parsed_url.query)

        if "uddg" in params:
            url = params["uddg"][0]
    response = requests.get(
        url,
        headers = {
                # Real browser like user-agent
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            },
        timeout=20
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    for element in soup(
        ["script", "style", "noscript"]
    ):
        element.decompose()

    text = soup.get_text(
        "\n",
        strip=True
    )

    return text[:4000]
