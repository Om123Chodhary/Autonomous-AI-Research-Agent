# 🎓 Autonomous AI Research Agent

**Autonomous AI Research Agent** is a full-stack, production-ready AI Research Agent. It takes a user's query, plans a research strategy, autonomously browses the web, verifies facts using an LLM-as-a-Judge, and synthesizes a highly structured Markdown research report—all while streaming its live internal progress to the frontend.

**An end-to-end AI agent that autonomously plans, researches, verifies, and generates structured reports.**

[![Live Demo](https://img.shields.io/badge/Live_Demo-Click_Here-brightgreen?style=for-the-badge&logo=render)](https://autonomous-ai-research-agent-r3s9.onrender.com/)
[![GitHub Repo](https://img.shields.io/badge/GitHub-Repository-blue?style=for-the-badge&logo=github)](https://github.com/Om123Chodhary/Autonomous-AI-Research-Agent)
[![Tech Stack](https://img.shields.io/badge/Tech_Stack-FastAPI_|_Groq_|_Docker-purple?style=for-the-badge)](https://github.com/Om123Chodhary/Autonomous-AI-Research-Agent)

![Workflow Architecture](./assets/Autonomous%20AI%20Research%20Workflow.png))

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

---


## 🌐 Live Demo

Aap is project ko bina kuch install kiye seedha apne browser mein try kar sakte hain:

👉 **[Launch Autonomous AI Research Agent](https://autonomous-ai-research-agent-r3s9.onrender.com/)**

---

## 👨‍💻 Author

<div align="center">

### **Oma Ram**
**B.S. Applied AI & Data Science @ IIT Jodhpur**
*AI Engineer | GenAI | Agentic AI & RAG Systems*

I am a passionate AI Engineer who believes in understanding the core architecture behind AI systems. I built this project entirely from scratch to master the mechanics of autonomous agents, state management, and production-grade API design.

[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/Om123Chodhary)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/oma-ram-choudhary-07532024a/)
[![Email](https://img.shields.io/badge/Email-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:omaramchoudhary418@gmail.com)

</div>

---

## 🛠️ Technical Design Decisions & FAQs

This section highlights the core engineering challenges faced during the development of this project and the architectural decisions made to solve them.

<details>
<summary><b>1. Why did you build the Agent Loop from scratch instead of using LangGraph or CrewAI?</b></summary>
<br>
While frameworks like LangGraph and CrewAI are great for rapid prototyping, they abstract away the underlying mechanics. I wanted absolute control over the <b>State-Machine Enforcement</b> and API routing. Building it from scratch allowed me to implement custom fault-tolerance (like multi-key fallbacks) and real-time Server-Sent Events (SSE) streaming exactly the way I wanted, without fighting the framework's opinions.
</details>

<details>
<summary><b>2. How does the system handle LLM hallucinations and "laziness"?</b></summary>
<br>
LLMs often try to skip steps (e.g., giving an answer before verifying facts). I solved this using two methods:
<ul>
  <li><b>State-Machine Enforcement:</b> I implemented Python-level boolean flags (like <code>search_done</code>, <code>read_done</code>, <code>pending_verification</code>). If the LLM tries to give a final answer without completing the mandatory steps, the Python code intercepts it and forces the LLM back into the loop.</li>
  <li><b>LLM-as-a-Judge:</b> A secondary LLM call acts as an impartial judge to verify if the extracted evidence genuinely supports the research finding before saving it.</li>
</ul>
</details>

<details>
<summary><b>3. What happens if the Groq API rate limit (429 Error) is hit?</b></summary>
<br>
The system uses a <b>Multi-Key API Fallback Strategy</b>. I pass an array of API keys to the custom <code>call_llm()</code> function. If Key 1 hits a rate limit, the code catches the exception and automatically retries the exact same request using Key 2, then Key 3. This ensures 99.9% uptime for the end-user.
</details>

<details>
<summary><b>4. How is the real-time progress (Searching, Verifying) streamed to the frontend?</b></summary>
<br>
I implemented <b>Server-Sent Events (SSE)</b>. The backend uses <code>asyncio.Queue</code> to collect events from the agent. FastAPI's <code>StreamingResponse</code> then yields these events as JSON chunks to the frontend. The frontend reads this stream using the <code>fetch()</code> API and <code>getReader()</code>, updating the UI in real-time without needing WebSockets.
</details>

<details>
<summary><b>5. Why use `asyncio.to_thread`? Does the server block during heavy web scraping?</b></summary>
<br>
No, the server does not block. FastAPI is asynchronous, but heavy synchronous tasks like web scraping (<code>requests.get</code>) or LLM API calls can block the event loop. I wrapped these blocking functions in <code>asyncio.to_thread()</code>. This offloads the heavy work to a background thread, allowing the main event loop to continue serving other users concurrently.
</details>

<details>
<summary><b>6. What happens if a user closes the browser mid-research?</b></summary>
<br>
I implemented <b>Client Disconnect Handling</b>. The <code>/research</code> endpoint continuously checks <code>await request.is_disconnected()</code>. If the user closes the tab, the server immediately cancels the background agent task. This prevents the server from wasting API tokens and compute resources on a request no one is listening to.
</details>

<details>
<summary><b>7.How does your server handle 5 concurrent users?</b></summary>
<br>
My FastAPI server is built on an asynchronous event loop. When 5 users connect, the server creates 5 independent background tasks using asyncio.create_task. For CPU-bound or heavy I/O tasks (like web scraping and API calls), I use asyncio.to_thread so the main event loop is never blocked. Each user gets their own asyncio.Queue for real-time SSE streaming. However, currently, the agent state (research notes) is stored in a global list for demonstration. In a true multi-user production environment, I would refactor this to use session-based state management or Redis to ensure data isolation between users

</details>
<details>
<summary><b>8. How does the application handle multiple concurrent users (Data Isolation)?</b></summary>
<br>
Initially, the agent's state (research notes) was stored in a global Python list. While this worked for a single user, it caused a <b>data-race condition</b> in a multi-user environment—if two users ran research simultaneously, their notes would mix up. 

To solve this, I implemented a <b>Session-Based State Isolation</b> architecture:
<ul>
  <li>When a new research request hits the <code>/research</code> endpoint, the backend generates a unique <code>UUID</code> (Session ID) for that specific user.</li>
  <li>Instead of a single global list, the state is now stored in a Python dictionary (<code>research_notes_db</code>), mapping the <code>session_id</code> to its own list of notes.</li>
  <li>This <code>session_id</code> is seamlessly injected into the tool arguments (like <code>add_research_note</code>) behind the scenes by the agent loop, completely isolating one user's data from another's.</li>
</ul>
This ensures the application is fully concurrent and thread-safe.
</details>

---

## 🚀 Getting Started (Local Setup)

Follow these steps to run the project on your local machine.

**1. Clone the repository:**
```bash
git clone https://github.com/Om123Chodhary/Autonomous-AI-Research-Agent.git
cd Autonomous-AI-Research-Agent
