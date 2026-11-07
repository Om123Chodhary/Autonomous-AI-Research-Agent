import asyncio
import json
import uuid 

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from agent import run_agent, research_agent
from schemas import ChatRequest, ChatResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Research AI application")
    yield
    print("Shutting down Research AI application")


app = FastAPI(
    title="Research AI Agent",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/static",
    StaticFiles(directory="frontend"),
    name="static",
)


@app.get("/")
async def home():
    return FileResponse("frontend/index.html")


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty."
        )

    try:
        # Directly await the agent execution
        result = await run_agent(request.message)

        return ChatResponse(
            response=result
        )

    except Exception as exc:
        # Print the actual error to the terminal for debugging
        print(f"\n[FATAL ERROR] {type(exc).__name__}: {exc}")
        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )


@app.get("/research")
async def research(topic: str, request: Request):
    # 1. Validation: Block empty topics
    if not topic.strip():
        raise HTTPException(status_code=400, detail="Topic cannot be empty.")

    session_id = str(uuid.uuid4())
    print(f"\n[NEW REQUEST] Assigned Session ID: {session_id}")

    queue = asyncio.Queue()
    
    def progress_callback(event):
        queue.put_nowait(event)
        
    # 2. Run agent in a background task
    async def run_agent_task():
        try:
            # Directly call the agent with the progress callback
            await run_agent(topic,session_id, max_steps=12, progress_callback=progress_callback)
        except Exception as e:
            queue.put_nowait({"type": "error", "message": str(e)})

    # 3. Event Stream Generator
    async def event_stream():
        # Start the background task
        task = asyncio.create_task(run_agent_task())

        try:
            while True:
                # 🚨 FIX: Check if the client has disconnected (e.g., closed the browser)
                if await request.is_disconnected():
                    print("\n[WARNING] Client disconnected. Cancelling agent task to save tokens.")
                    task.cancel() # Forcefully cancel the agent task to save API tokens
                    break

                # Get event from queue (wait for 0.5 seconds)
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=0.5)
                    # Yield in SSE (Server-Sent Events) format
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    # If timeout occurs, check if the task is done and the queue is empty
                    if task.done() and queue.empty():
                        break
                    continue
        finally:
            # Ensure the task is cancelled when the stream closes
            if not task.done():
                task.cancel()

    # 4. Return the Streaming Response
    return StreamingResponse(event_stream(), media_type="text/event-stream")