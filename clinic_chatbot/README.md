# Toor Clinic - Surgical Recovery Portal

A high-performance, AI-driven web application designed for Dr. Jay Toor's orthopaedic spine surgery patients. This portal allows patients to interact with a clinical AI assistant while simultaneously viewing their official, procedure-specific recovery protocols to ensure zero-hallucination guidance.

## 🎯 Key Features

* **The "Zero-Hallucination" 3-Pane Layout:** A highly functional UI featuring a persistent history sidebar, a central AI chat interface, and a collapsible PDF viewer that displays the source-of-truth medical documentation side-by-side with the AI's answers.
* **Clinical Context Switching:** Patients select their specific procedure (ACDF, Lumbar Fusion, or Microdiscectomy) upon entry. The app dynamically loads the corresponding PDF and routes the procedure ID to the backend to ground the AI's context.
* **Persistent Session Memory:** The frontend maintains an active `chatHistory` array, allowing the patient to ask conversational follow-up questions without needing to restate their procedure or previous context.
* **"Academic Elite" Aesthetic:** Styled strictly with the University of Manitoba color palette:
    * **Bison Brown (`#381D12`)** & **Navy Blue (`#003B5C`)** for grounded authority.
    * **UM Gold (`#F5A800`)** for high-contrast primary actions.
    * **Crisp White (`#FFFFFF`)** for clean, readable medical data.

## 📁 Project Structure

The frontend is built with pure HTML, CSS, and Vanilla JavaScript for maximum performance and zero dependency overhead.

```text
/toor-clinic-portal
├── index.html       # The main marketing landing page featuring Dr. Toor's bio and procedure overviews.
├── portal.html      # The interactive 3-pane patient application.
├── style.css        # Unified master stylesheet covering both the landing page and the portal app.
├── app.js           # Core logic: UI state management, PDF syncing, and backend API communication.
└── /assets          
    └── um.png       # University of Manitoba branding logo.
```

## 🚀 How to Run It (Local Development)
This application requires both the Python/FastAPI backend and the Vanilla JS frontend to be running simultaneously.

### Part 1: Start the Backend (API & File Server)
The backend handles the LLM processing and serves the PDF files to the frontend iframe.

Verify Local LLM: Ensure your local LLM instance (e.g., Ollama) is running in the background.

Prepare Data: Verify that your PDF files are located in the data/ directory of your backend folder. The filenames must match exactly:

ACDF.pdf

Lumbar decompression and fusion.pdf

Microdiscetomy.pdf

Start the FastAPI Server: Open your terminal, navigate to your backend directory, and run:

```Bash

uvicorn main:app --reload
```

Note: The frontend expects the API to be running on http://localhost:8000.

### Part 2: Start the Frontend (User Interface)
Since the frontend uses standard web technologies, there are no node modules or build steps required.

Option A (Simple): Simply double-click index.html to open it directly in your web browser (Chrome, Edge, Safari, etc.).

Option B (Recommended for Dev): If you are using VS Code, install the Live Server extension. Right-click index.html and select "Open with Live Server". This will run the frontend on a local port (e.g., http://127.0.0.1:5500) and auto-refresh when you save changes.

Navigate to the Portal: Click "Patient Portal" or "Access Patient Portal" from the landing page to enter the app, select a surgery, and begin chatting.

## 🎨 Modifying the Codebase
Adding New Procedures: 1. Add the new procedure to the dropdown <select> in portal.html.
2. Add the corresponding PDF mapping to the files dictionary inside the syncProtocol() function in app.js.

Changing API Endpoints: If deploying to a live server (AWS, Heroku, etc.), update the fetch URL inside the handleChatSubmit() function in app.js.