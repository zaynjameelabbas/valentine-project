// ==========================================
// DOM ELEMENTS
// ==========================================
const chatWindow = document.getElementById('chat-window');
const protocolSelect = document.getElementById('protocol-select');
const pdfView = document.getElementById('pdf-view');
const userInput = document.getElementById('user-input');
const chatForm = document.getElementById('chat-form');

const rightSidebar = document.getElementById('right-sidebar');
const pdfToggleButton = document.getElementById('toggle-pdf');
const closePdfButton = document.getElementById('close-pdf');

const leftSidebar = document.getElementById('left-sidebar');
const closeSidebarBtn = document.getElementById('close-sidebar');
const openSidebarBtn = document.getElementById('open-sidebar');

const historyList = document.getElementById('history-list');
const newChatBtn = document.getElementById('new-chat-btn');
const introScreen = document.getElementById('intro-screen');

// MOBILE
const menuBtn = document.getElementById('mobile-menu-btn');
const sidebar = document.querySelector('.left-sidebar');
// Create the overlay once globally
const sidebarOverlay = document.createElement('div');
sidebarOverlay.className = 'sidebar-overlay';
document.body.appendChild(sidebarOverlay);

// ==========================================
// APP STATE (Upgraded for multiple chats)
// ==========================================
let currentProc = ''; 
let chatHistory = []; 
let allSessions = {}; // Stores all chats: { id: { proc: 'ACDF', history: [] } }
let currentSessionId = null; // Tracks which chat we are currently viewing

// ==========================================
// EVENT LISTENERS
// ==========================================
chatForm.addEventListener('submit', handleChatSubmit);

protocolSelect.addEventListener('change', (e) => {
    currentProc = e.target.value;
    syncProtocol(); 
});

pdfToggleButton.addEventListener('click', togglePdf);
if (closePdfButton) closePdfButton.addEventListener('click', togglePdf);

closeSidebarBtn.addEventListener('click', () => {
    leftSidebar.classList.add('collapsed');
    openSidebarBtn.style.display = 'block';
});

openSidebarBtn.addEventListener('click', () => {
    leftSidebar.classList.remove('collapsed');
    openSidebarBtn.style.display = 'none';
});

if (newChatBtn) newChatBtn.addEventListener('click', resetChat);

if (window.innerWidth <= 768) {
    userInput.addEventListener('focus', () => {
        // Small delay to allow the keyboard to animate up
        setTimeout(() => {
            window.scrollTo(0, document.body.scrollHeight);
        }, 300);
    });
}

// ==========================================
// CORE FUNCTIONS
// ==========================================
function initPortal(proc) {
    currentProc = proc;
    protocolSelect.value = proc; 
    
    document.getElementById('selection-overlay').style.display = 'none';
    document.getElementById('app-interface').style.display = 'flex';
    
    syncProtocol();
    rightSidebar.classList.remove('collapsed');
    pdfToggleButton.classList.add('hidden');
}

function syncProtocol() {
    chatWindow.innerHTML = '';
    chatHistory = []; 
    
    if (introScreen) introScreen.style.display = 'block';
    
    const files = {
        'ACDF': 'ACDF.pdf',
        'Lumbar_Fusion': 'Lumbar decompression and fusion.pdf',
        'Microdiscectomy': 'Microdiscetomy.pdf' 
    };

    if (files[currentProc]) {
        pdfView.src = `http://localhost:8000/data/${files[currentProc]}`;
    }
}

async function handleChatSubmit(e) {
    e.preventDefault(); 
    
    const query = userInput.value.trim();
    if (!query || !currentProc) return;

    if (introScreen) introScreen.style.display = 'none';

    // If there is no active session ID, create a new one
    if (!currentSessionId) {
        currentSessionId = Date.now().toString();
        allSessions[currentSessionId] = { proc: currentProc, history: [] };
        updateSidebarHistory(query, currentSessionId);
    }

    appendMsg(query, 'user-message');
    userInput.value = '';

    const loaderId = 'loader-' + Date.now();
    appendMsg('', 'bot-message typing', loaderId);

    try {
        const res = await fetch('http://localhost:8000/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                procedure_id: currentProc, 
                query: query, 
                chat_history: chatHistory 
            })
        });
        
        const data = await res.json();
        
        const loader = document.getElementById(loaderId);
        if (loader) loader.remove();
        
        appendMsg(data.response, 'bot-message');
        
        // Save to active memory for the API context
        chatHistory.push({ "type": "user-message", "text": query });
        chatHistory.push({ "type": "bot-message", "text": data.response });
        
        // Save to long-term storage for switching chats
        allSessions[currentSessionId].history.push({ "type": "user-message", "text": query });
        allSessions[currentSessionId].history.push({ "type": "bot-message", "text": data.response });

    } catch (err) {
        const loader = document.getElementById(loaderId);
        if (loader) loader.remove();
        appendMsg("System offline. Please ensure the clinical API is active.", 'bot-message error');
    }
}

function resetChat() {
    currentSessionId = null; // Clear active session tracker
    chatHistory = [];
    syncProtocol();
    
    // Remove highlighting from sidebar items
    document.querySelectorAll('.history-item').forEach(el => el.classList.remove('active'));
}

// NEW: Function to load a previous chat session
function loadSession(id) {
    currentSessionId = id;
    const session = allSessions[id];
    
    currentProc = session.proc;
    protocolSelect.value = currentProc;
    chatHistory = [...session.history]; // Copy the history back to active memory
    
    // Clear the screen and hide intro
    chatWindow.innerHTML = '';
    if (introScreen) introScreen.style.display = 'none';
    
    // Reload the correct PDF
    const files = {
        'ACDF': 'ACDF.pdf',
        'Lumbar_Fusion': 'Lumbar decompression and fusion.pdf',
        'Microdiscectomy': 'Microdiscetomy.pdf' 
    };
    if (files[currentProc]) pdfView.src = `http://localhost:8000/data/${files[currentProc]}`;

    // Re-render all messages from this session
    chatHistory.forEach(msg => {
        appendMsg(msg.text, msg.type);
    });

    // Update the sidebar highlighting
    document.querySelectorAll('.history-item').forEach(el => {
        if (el.dataset.id === id) el.classList.add('active');
        else el.classList.remove('active');
    });
}

function togglePdf() {
    // Check if user is on mobile
    if (window.innerWidth <= 768) {
        // Open PDF in a new tab for mobile users
        const pdfUrl = pdfView.src;
        if (pdfUrl) {
            window.open(pdfUrl, '_blank');
        }
    } else {
        // Desktop behavior: Toggle the right sidebar
        const isCollapsed = rightSidebar.classList.contains('collapsed');
        if (isCollapsed) {
            rightSidebar.classList.remove('collapsed');
            pdfToggleButton.classList.add('hidden'); 
        } else {
            rightSidebar.classList.add('collapsed');
            pdfToggleButton.classList.remove('hidden'); 
        }
    }
}

function appendMsg(text, type, id = null) {
    const div = document.createElement('div');
    div.className = `message ${type}`; 
    if (id) div.id = id;
    
    if (type.includes('typing')) {
        div.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
    } else {
        div.innerText = text;
    }
    
    chatWindow.appendChild(div);
    chatWindow.scrollTop = chatWindow.scrollHeight; 
}

function updateSidebarHistory(query, id) {
    if (!historyList) return;
    const item = document.createElement('div');
    item.className = 'history-item active'; // Set to active immediately
    item.dataset.id = id; // Store the ID on the HTML element
    
    // Remove active class from all other items
    document.querySelectorAll('.history-item').forEach(el => el.classList.remove('active'));
    
    const truncated = query.length > 25 ? query.substring(0, 25) + '...' : query;
    item.innerHTML = `<i class="fa-solid fa-message"></i> ${truncated}`;
    
    // Attach the click listener to switch chats
    item.addEventListener('click', () => loadSession(id));
    
    historyList.prepend(item); 
}

// ==========================================
// MOBILE LOGIC
// ==========================================

function toggleMobileMenu(e) {
    // Only execute if we are actually on a mobile screen size
    if (window.innerWidth <= 768) {
        if (e) e.stopPropagation();
        
        const isActive = leftSidebar.classList.toggle('active');
        sidebarOverlay.classList.toggle('active', isActive);
        
        // Prevent background "rubber-band" scrolling when menu is open
        document.body.style.overflow = isActive ? 'hidden' : '';
    }
}

// 1. Hamburger Click
if (menuBtn) {
    menuBtn.addEventListener('click', toggleMobileMenu);
}

// 2. Click on the darkened overlay to close
sidebarOverlay.addEventListener('click', toggleMobileMenu);

// 3. Close menu when clicking items inside the sidebar (History or Exit)
leftSidebar.addEventListener('click', (e) => {
    if (window.innerWidth <= 768) {
        // If they clicked a history item or the exit button
        if (e.target.closest('.history-item') || e.target.closest('.exit-btn')) {
            toggleMobileMenu();
        }
    }
});