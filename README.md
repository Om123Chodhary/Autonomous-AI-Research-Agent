# 🎓 Autonomous AI Research Agent

**Autonomous AI Research Agent** is a full-stack, production-ready AI Research Agent. It takes a user's query, plans a research strategy, autonomously browses the web, verifies facts using an LLM-as-a-Judge, and synthesizes a highly structured Markdown research report—all while streaming its live internal progress to the frontend.

![Workflow Architecture](./assets\Autonomous AI Research Workflow.png)

## 🚀 Key Features

*   **Custom Agent Architecture:** Built from scratch without heavy frameworks (like LangGraph/CrewAI) to maintain absolute control over state routing and tool execution.
*   **State-Machine Enforcement:** Prevents LLM laziness by enforcing a strict `Search -> Read -> Save -> Verify` workflow using Python-level boolean flags.
*   **LLM-as-a-Judge (Verification):** A secondary LLM call verifies if the extracted evidence genuinely supports the research finding, eliminating hallucinations.
*   **Real-Time Streaming (SSE):** Utilizes Server-Sent Events (`asyncio.Queue` + `StreamingResponse`) to push real-time agent activity to the browser.
*   **Multi-Key API Fallback:** Gracefully handles Groq API rate limits by automatically rotating through multiple API keys without failing the user's request.
*   **Non-Blocking Async Architecture:** Uses `asyncio.to_thread` for heavy tasks (Scraping, LLM calls) so the FastAPI server never freezes for other users.
*   **Agentic UX:** The frontend dynamically renders the agent's thoughts using human-readable messages (e.g., "📖 Reading the webpage...").

## 🛠️ Tech Stack

*   **Backend:** Python, FastAPI, Uvicorn, Asyncio
*   **AI / LLM:** Groq API (GPT-OSS-120B), OpenAI SDK, Custom Prompt Engineering
*   **Frontend:** HTML5, CSS3, Vanilla JavaScript (Fetch API + Streams), Marked.js
*   **Data Processing:** BeautifulSoup4, `webless` (Web Search API)
*   **Deployment:** Docker, Render

## ⚙️ How the Workflow Works

1.  **Input:** User enters a research topic in the web interface.
2.  **Planning:** The FastAPI backend triggers the `Planner Agent`, which generates a 3-5 step research roadmap.
3.  **Execution Loop:** The custom Python agent loop begins. The LLM decides which tool to use based on the plan.
4.  **Tooling:** The agent uses `search_web` to find URLs, and `read_webpage` to extract text (PDFs are ignored to save tokens).
5.  **Enforcement & Verification:** If the agent tries to skip steps, Python forces it back. Extracted findings are saved and verified by a secondary LLM call.
6.  **Streaming:** Every action triggers an event that is streamed via SSE to the frontend dashboard.
7.  **Synthesis:** Once enough verified notes are gathered, the `Report Generator` synthesizes them into a professional Markdown report.

## 🧠 Skills Demonstrated

By building this project, the following advanced AI Engineering skills were implemented:
*   **Agentic Design Patterns:** Tool calling, ReAct loop, State-machine enforcement, and LLM-as-a-judge verification.
*   **Async Python:** Handling concurrent tasks, non-blocking API calls, and background threads.
*   **Production Reliability:** API fallback systems, error handling, and input validation.
*   **Full-Stack Development:** Building a responsive frontend that consumes real-time streaming data from a Python backend.

## 🚀 Getting Started (Local Setup)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Om123Chodhary/Autonomous-AI-Research-Agent.git
   cd Autonomous AI Research Agent