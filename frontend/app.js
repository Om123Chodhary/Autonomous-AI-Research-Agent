const button = document.getElementById("researchButton");
const topicInput = document.getElementById("topic");
const status = document.getElementById("status");
const result = document.getElementById("result");
const progressSection = document.getElementById("progressSection");
const resultSection = document.getElementById("resultSection");
const errorBox = document.getElementById("error");
const characterCount = document.getElementById("characterCount");
const activityList = document.getElementById("activityList"); // Make sure yeh HTML mein hai


const TOOL_DESCRIPTIONS = {
    "search_web": "🔍 Searching the web for relevant sources...",
    "read_webpage": "📖 Reading the webpage to extract information...",
    "add_research_note": "📝 Saving the important findings to notes...",
    "verify_finding": "⚖️ Verifying the evidence to ensure accuracy...",
    "get_research_notes": "🗂️ Reviewing all collected notes...",
    "get_verified_research_notes": "✅ Retrieving verified facts..."
};


topicInput.addEventListener("input", () => {
    const length = topicInput.value.length;
    characterCount.textContent = `${length} characters`;
});

// 🚨 NAYA FUNCTION: Jo backend se stream ko padhega
async function startResearch(topic) {
    // UI Reset & Show Progress
    errorBox.classList.add("hidden");
    resultSection.classList.add("hidden");
    progressSection.classList.remove("hidden");
    
    // Har nayi research par purani activity clear karein
    activityList.innerHTML = ""; 
    
    button.disabled = true;
    button.textContent = "Researching...";
    status.textContent = "Your research agent is working...";

    try {
        // 🚨 ENDPOINT CHANGE: /chat se /research (GET request)
        const response = await fetch(`/research?topic=${encodeURIComponent(topic)}`);

        if (!response.ok) {
            throw new Error("Research request failed.");
        }

        // 🚨 STREAM READER SETUP
        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";

        // 🚨 STREAM KO PADHNE KA LOOP
        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            
            // SSE events "\n\n" se separate hote hain
            const lines = buffer.split("\n\n");
            buffer = lines.pop(); // Aakhri adhura chunk buffer mein bacha lo

            for (const line of lines) {
                if (line.startsWith("data: ")) {
                    // "data: " hata kar JSON parse karein
                    const eventData = JSON.parse(line.replace("data: ", ""));
                    handleResearchEvent(eventData);
                }
            }
        }

    } catch (error) {
        progressSection.classList.add("hidden");
        errorBox.textContent = error.message || "Unable to complete research.";
        errorBox.classList.remove("hidden");
    } finally {
        button.disabled = false;
        button.innerHTML = "<span>✦</span> Start Research";
    }
}

// 🚨 NAYA FUNCTION: Jo backend se aaye events ko UI mein dikhayega
function handleResearchEvent(event) {
    const stepDiv = document.createElement("div");
    stepDiv.className = "activity-item";

    // Event type ke hisaab se message banayein
    if (event.type === "plan") {
        stepDiv.innerHTML = `✅ <strong>Plan Created:</strong> Research strategy is ready.`;
    } 
    else if (event.type === "step") {
        stepDiv.innerHTML = `⏳ <strong>Step ${event.step}:</strong> Agent is thinking...`;
    } 
    else if (event.type === "tool") {
        const humanMessage = TOOL_DESCRIPTIONS[event.tool] || `Using tool: ${event.tool}`;
        stepDiv.innerHTML = `<strong>${humanMessage}</strong>`;
    } 
    else if (event.type === "tool_complete") {
        stepDiv.innerHTML = `✅ <strong>Step Completed.</strong>`;
    } 
    else if (event.type === "verification") {
        stepDiv.innerHTML = `⚖️ <strong>Verification:</strong> Checking facts...`;
    } 
    else if (event.type === "complete") {
        stepDiv.innerHTML = `🎉 <strong>Research Completed!</strong> Generating final report...`;
        
        // Report ready hai, toh spinner hide karke result show karein
        progressSection.classList.add("hidden");
        resultSection.classList.remove("hidden");
        result.innerHTML = marked.parse(event.report); // Markdown render
    }
    else if (event.type === "error") {
        stepDiv.innerHTML = `❌ <strong>Error:</strong> ${event.message}`;
    }

    // Step ko activity list mein add karein
    activityList.appendChild(stepDiv);
    
    // Auto-scroll taaki latest step dikhe
    activityList.scrollTop = activityList.scrollHeight;
}

// Button Click Event
button.addEventListener("click", () => {
    const topic = topicInput.value.trim();

    if (!topic) {
        errorBox.textContent = "Please enter a research topic.";
        errorBox.classList.remove("hidden");
        return;
    }

    // Naya function call karein
    startResearch(topic);
});