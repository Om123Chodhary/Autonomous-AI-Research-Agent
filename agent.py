import json
import os
import inspect
import asyncio
from openai import OpenAI
from dotenv import load_dotenv

from tools import (
    search_web, read_webpage, add_research_note, 
    get_research_notes, verify_finding, get_verified_research_notes, clear_research_notes 
)
load_dotenv()

base_url = os.getenv("BASE_URL")

# 1. Load all API keys
GROQ_KEYS = [
    os.getenv("GEMINI_API_KEY_2"),
    os.getenv("GEMINI_API_KEY_2"),
    os.getenv("GEMINI_API_KEY_3")
]

# Filter out empty keys (in case one is not available)
GROQ_KEYS = [k for k in GROQ_KEYS if k]

# 2. Create a separate Client for each key
CLIENTS = [
    OpenAI(base_url=base_url, api_key=key) 
    for key in GROQ_KEYS
]

MODEL = os.getenv("MODEL", "openai/gpt-oss-120b")


# 3. 🚨 CORE FUNCTION: Smart LLM Caller with Fallback Mechanism
def call_llm(messages, tools=None, tool_choice=None, temperature=None, **kwargs):
    """
    Tries each API key. If a rate limit is hit, it automatically switches to the next key.
    """
    last_error = None
    
    for i, client in enumerate(CLIENTS, start=1):
        try:
            # Build parameters
            params = {"model": MODEL, "messages": messages, **kwargs}
            if tools: params["tools"] = tools
            if tool_choice: params["tool_choice"] = tool_choice
            if temperature is not None: params["temperature"] = temperature
            
            # Make the API Call
            response = client.chat.completions.create(**params)
            
            # If execution reaches here, it means success!
            print(f"[LLM] ✅ Used Key {i}")
            return response
            
        except Exception as e:
            error_str = str(e).lower()
            
            # Check for rate limit or token limit errors
            is_limit_error = (
                "429" in str(e) or 
                "413" in str(e) or
                "rate_limit" in error_str or 
                "tokens per" in error_str or
                "too large" in error_str
            )
            
            if is_limit_error and i < len(CLIENTS):
                print(f"[LLM] ⚠️ Key {i} hit limit. Switching to Key {i+1}...")
                last_error = e
                continue # Try the next key
            else:
                # If it's another error (like an invalid request), raise it
                raise e
    
    # If all API keys are exhausted
    raise Exception(f"All API keys exhausted. Last error: {last_error}")


# 4. Tool Schemas (Groq requires this specific JSON format)
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web for a query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_webpage",
            "description": "Read the text content of a webpage. You MUST provide a valid URL starting with http or https.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The complete URL of the webpage to read (e.g., https://example.com/page)"
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_research_note",
            "description": "Save important findings.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {"type": "string"},
                    "finding": {"type": "string"},
                    "evidence": {"type": "string"}
                },
                "required": ["source", "finding", "evidence"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "verify_finding",
            "description": "Verify if evidence supports finding.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source": {"type": "string"},
                    "finding": {"type": "string"},
                    "evidence": {"type": "string"}
                },
                "required": ["source", "finding", "evidence"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_verified_research_notes",
            "description": "Get verified notes.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_research_notes",
            "description": "Retrieve all saved research notes to review findings.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
]

AVAILABLE_TOOLS = {
    "search_web": search_web,
    "read_webpage": read_webpage,
    "add_research_note": add_research_note,
    "get_research_notes": get_research_notes, 
    "verify_finding": verify_finding,
    "get_verified_research_notes": get_verified_research_notes
}

def generate_report(user_request: str, verified_notes: list) -> str:
    
    # 1. Early Exit (Do not call the API if no data is available)
    if not verified_notes:
        return "### ⚠️ No Verified Findings\n\nI could not find and verify enough information to generate a report for this topic. Please try a different or broader query."

    # 2. Format the verified findings
    research_text = "\n\n".join([
        f"- **Source**: {note['source']}\n  **Finding**: {note['finding']}\n  **Evidence**: {note['evidence']}"
        for note in verified_notes
    ])
    
    response = call_llm(
        messages=[
            {
                "role": "system", 
                "content": (
                    "You are an expert Senior Research Analyst. Your task is to synthesize the provided verified findings into a highly professional, natural-sounding report in Markdown format.\n\n"
                    "CRITICAL RULES:\n"
                    "1. Use ONLY the provided findings. Do NOT invent facts or outside knowledge.\n"
                    "2. Let the DATA dictate the structure. If the data is rich in one area and empty in another, adapt the report accordingly.\n"
                    "3. Do NOT force standard sections (like Introduction or Limitations) if the provided data does not support them. It is better to omit a section than to fill it with fluff.\n"
                    "4. Format beautifully using Markdown (H2, H3, bold text, bullet points, and tables where appropriate to compare data).\n"
                    "5. Maintain a professional, analytical tone."
                )
            },
            {
                "role": "user", 
                "content": (
                    f"Research Request:\n{user_request}\n\n"
                    f"Verified Findings:\n{research_text}\n\n"
                    "Please synthesize these findings into a comprehensive report. "
                    "You may use sections like 'Key Findings', 'Analysis', and 'Conclusion' based on what the data actually provides. "
                    "Ensure the flow is logical and directly answers the user's request."
                )
            }
        ],
        temperature=0.3 # Balanced creativity for writing, but strictly grounded in data
    )
    print(response.choices[0].message.content)
    return response.choices[0].message.content

def create_research_plan(user_request):
    print(f"\n[Planner] Creating research plan for: {user_request}")
    response = call_llm(
        messages=[
            {
                "role": "system", 
                "content": (
                    "You are an expert Research Planner. Your task is to create a highly specific, step-by-step research plan.\n"
                    "RULES:\n"
                    "1. Break the request into 3 to 5 clear, actionable steps.\n"
                    "2. For steps that require web search, explicitly write the exact search query in quotes. (e.g., 1. Search for 'Impact of AI on healthcare 2024')\n"
                    "3. Keep it extremely concise.\n"
                    "4. Return ONLY the numbered list. Do NOT include any introductory or concluding text."
                )
            },
            {"role": "user", "content": user_request}
        ],
        temperature=0.2 
    )
    return response.choices[0].message.content

async def research_agent(user_request, session_id, max_steps=8, progress_callback=None):
    def emit(message):
        if progress_callback:
            progress_callback(message)

    clear_research_notes(session_id)
    print("\n[STATE] Research notes cleared for new task.")

    plan = await asyncio.to_thread(create_research_plan, user_request)
    print("\n--- RESEARCH PLAN ---\n" + plan + "\n---------------------")
    emit({
        "type": "plan",
        "message": "Research Plan Created",
        "plan": plan
    })

    search_done = False
    read_done = False
    note_added = False
    pending_verification = False

    system_prompt = (
        "You are an expert AI Research Agent. Your goal is to investigate the user's request based on the provided Research Plan.\n\n"
        f"--- RESEARCH PLAN ---\n{plan}\n----------------------\n\n"
        "You MUST follow this exact loop:\n"
        "1. 'search_web': Search for relevant URLs.\n"
        "2. 'read_webpage': Read the content of a specific URL. You MUST PROVIDE A VALID URL. Ignore PDFs.\n"
        "3. 'add_research_note': Save important findings (source, finding, evidence).\n"
        "4. 'verify_finding': Immediately verify the note you just saved.\n\n"
        "--- ADAPTIVE RESEARCH STRATEGY (SMART STOPPING) ---\n"
        "- For a simple factual question, one verified finding may be sufficient if it completely answers the question.\n"
        "- For a complex or broad request, gather at least 2 to 3 verified findings from different sources before finishing.\n\n"
        "--- STRICT RULES ---\n"
        "1. NEVER skip the 'verify_finding' step after saving a note.\n"
        "2. ALWAYS provide exact URLs to 'read_webpage'. Do not hallucinate arguments.\n"
        "3. Do not read PDF links. Only read HTML webpages.\n"
        "4. If a tool fails, analyze the error and try a different URL or query."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Research Request: {user_request}"}
    ]

    def required_tool():
        if pending_verification:
            return "verify_finding"
        if search_done and not read_done:
            return "read_webpage"
        if read_done and not note_added:
            return "add_research_note"
        return None

    for step in range(max_steps):
        print(f"\n--- Agent Step {step + 1} / {max_steps} ---")
        emit({
            "type": "step",
            "step": step + 1,
            "message": f"Agent Step {step + 1}"
        })

        current_state = (
            f"search_done={search_done}, read_done={read_done}, "
            f"note_added={note_added}, pending_verification={pending_verification}."
        )
        expected_tool = required_tool()

        messages[0]["content"] = (
            f"{system_prompt}\n\n"
            f"--- CURRENT STATE ---\n{current_state}\n"
            + (
                f"You MUST call '{expected_tool}' next.\n"
                if expected_tool
                else "No research step is currently pending. Begin with search_web or continue researching as appropriate.\n"
            )
        )

        if pending_verification:
            tool_choice = {
                "type": "function",
                "function": {"name": "verify_finding"}
            }
        elif not read_done and search_done:
            tool_choice = {
                "type": "function",
                "function": {"name": "read_webpage"}
            }
        elif not note_added and read_done:
            tool_choice = {
                "type": "function",
                "function": {"name": "add_research_note"}
            }
        else:
            tool_choice = "auto"

        # Groq API Call with Threadpool to prevent Event Loop blocking
        try:
            response = await asyncio.to_thread(
                call_llm,
                messages=messages,
                tools=TOOLS,
                tool_choice=tool_choice,
                temperature=0.0
            )
        except Exception as e:
            print(f"\nAPI ERROR: {e}")
            emit({"type": "error", "message": f"API Error: {str(e)}"})
            return "API Error occurred during research."

        message = response.choices[0].message
        messages.append(message)

        if not message.tool_calls:
            if expected_tool == "read_webpage":
                print("\n[ENFORCEMENT] Forcing read_webpage...")
                messages.append({
                    "role": "system",
                    "content": "You must read a webpage first."
                })
                continue
            elif expected_tool == "add_research_note":
                print("\n[ENFORCEMENT] Read pages but didn't save notes. Forcing add_research_note...")
                messages.append({
                    "role": "system",
                    "content": "You MUST use 'add_research_note' to save your findings before answering."
                })
                continue
            elif expected_tool == "verify_finding":
                print("\n[ENFORCEMENT] You saved a note but didn't verify it! Forcing verify_finding...")
                messages.append({
                    "role": "system",
                    "content": "You MUST use 'verify_finding' on the note you just saved before doing anything else."
                })
                continue
            else:
                print("\nReturning final answer.")
                return message.content

        retry_after_tool_error = False

        for tool_index, tool_call in enumerate(message.tool_calls):
            tool_name = tool_call.function.name

            # Catch hallucinated tool names without crashing the agent.
            if tool_name not in AVAILABLE_TOOLS:
                print(f"\n[TOOL ERROR] Unknown tool requested: {tool_name}")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": f"Error: Unknown tool '{tool_name}'. Available tools are: {', '.join(AVAILABLE_TOOLS.keys())}."
                })
                retry_after_tool_error = True

            else:
                required_now = required_tool()
                out_of_sequence = (
                    (required_now is not None and tool_name != required_now)
                    or (
                        required_now is None
                        and tool_name in {"read_webpage", "add_research_note", "verify_finding"}
                    )
                )

                if out_of_sequence:
                    expected = required_now or "search_web"
                    print(f"\n[ENFORCEMENT] Blocked {tool_name}. Forcing {expected}.")
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": f"Error: '{tool_name}' is not allowed at this stage. You must call '{expected}' next."
                    })
                    retry_after_tool_error = True

                else:
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except Exception:
                        print(f"[JSON ERROR] Invalid arguments: {tool_call.function.arguments}")
                        arguments = {}

                    if tool_name in {
                        "add_research_note",
                        "verify_finding",
                        "get_research_notes",
                        "get_verified_research_notes"
                    }:
                        arguments["session_id"] = session_id

                    print(f"\nCalling tool: {tool_name} | Args: {arguments}")
                    emit({
                        "type": "tool",
                        "tool": tool_name,
                        "message": f"Using tool: {tool_name}"
                    })

                    tool_function = AVAILABLE_TOOLS[tool_name]
                    tool_succeeded = False

                    try:
                        if inspect.iscoroutinefunction(tool_function):
                            result = await tool_function(**arguments)
                        else:
                            result = await asyncio.to_thread(tool_function, **arguments)
                        tool_succeeded = True
                        emit({
                            "type": "tool_complete",
                            "tool": tool_name,
                            "message": f"Completed: {tool_name}"
                        })
                    except Exception as e:
                        result = f"Error: {e}"

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": str(result)
                    })

                    if tool_succeeded:
                        if tool_name == "search_web":
                            search_done = True
                            read_done = False
                            note_added = False
                            pending_verification = False
                        elif tool_name == "read_webpage":
                            read_done = True
                        elif tool_name == "add_research_note":
                            note_added = True
                            pending_verification = True
                        elif tool_name == "verify_finding":
                            emit({
                                "type": "verification",
                                "message": "Verifying Research Evidence..."
                            })
                            # A successful verification completes this cycle.
                            search_done = False
                            read_done = False
                            note_added = False
                            pending_verification = False

            if retry_after_tool_error:
                # Close out any remaining tool calls from this assistant response
                # so the next API request has a complete tool-call history.
                for remaining_call in message.tool_calls[tool_index + 1:]:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": remaining_call.id,
                        "content": "Error: Not executed because an earlier tool call in this response was rejected. Retry with the required tool."
                    })
                break

        if retry_after_tool_error:
            continue

    return "Max steps reached without final answer."

async def run_agent(request,session_id, max_steps=8, progress_callback=None):
    # Helper function to emit events to the frontend
    def emit(event):
        if progress_callback:
            progress_callback(event)
            
    try:
        # 1. Run the agent loop
        await research_agent(request, session_id, max_steps=max_steps, progress_callback=progress_callback)
    
        # 2. Retrieve the verified notes
        verified_notes = get_verified_research_notes(session_id)
        print(f"\n[STATUS] Verified findings: {len(verified_notes)}")
    
        # 3. Emit status for report generation
        emit({"type": "status", "message": "Generating professional Report..."})
    
        # 4. Generate the final report (using threadpool to avoid blocking)
        report = await asyncio.to_thread(
            generate_report, 
            user_request=request, 
            verified_notes=verified_notes
        )
    
        # 5. CRITICAL: Emit the 'complete' event containing the report
        emit({"type": "complete", "message": "Research completed!", "report": report})
        return report
        
    except Exception as e:
        # FIX: Notify frontend if an API limit or any other error occurs
        error_msg = f"Agent Execution Failed: {str(e)}"
        print(f"\n[FATAL ERROR] {error_msg}")
        emit({"type": "error", "message": error_msg})
        return error_msg