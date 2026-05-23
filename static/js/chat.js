/*
   Alumni Network System - Chat Engine Client
   Handles real-time chat updates via async polling.
*/

let chatPollInterval = null;
let currentChatPartnerId = null;
let lastMessageCount = 0;

document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chat-form");
    const chatInput = document.getElementById("chat-input");
    const chatMessagesContainer = document.getElementById("chat-messages-container");
    
    // Check if we are on a messaging page with an active chat selection
    if (chatMessagesContainer) {
        currentChatPartnerId = chatMessagesContainer.dataset.partnerId;
        
        if (currentChatPartnerId) {
            // Initial history fetch
            fetchChatHistory(currentChatPartnerId, true);
            
            // Poll for history updates every 3 seconds
            chatPollInterval = setInterval(() => {
                fetchChatHistory(currentChatPartnerId, false);
            }, 3000);
        }
    }

    // Handle sending message
    if (chatForm && chatInput) {
        chatForm.addEventListener("submit", (e) => {
            e.preventDefault();
            const message = chatInput.value.trim();
            if (!message || !currentChatPartnerId) return;

            // Clear input immediately to make UI feel snappy
            chatInput.value = "";

            // Send message to API
            fetch("/api/chat/send", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    receiver_id: currentChatPartnerId,
                    message: message
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    appendMessageBubble(data.message);
                    scrollToBottom();
                } else {
                    console.error("Failed to send message:", data.error);
                }
            })
            .catch(err => console.error("Error sending message:", err));
        });
    }
});

// Fetch history from database
function fetchChatHistory(partnerId, isInitial = false) {
    if (!partnerId) return;
    
    fetch(`/api/chat/history/${partnerId}`)
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const history = data.history;
                
                // Only render if count of messages has changed (to prevent flashing/flickering)
                if (isInitial || history.length !== lastMessageCount) {
                    renderChatMessages(history);
                    lastMessageCount = history.length;
                    scrollToBottom();
                }
            }
        })
        .catch(err => console.error("Error fetching chat history:", err));
}

// Render list of messages
function renderChatMessages(history) {
    const container = document.getElementById("chat-messages-container");
    if (!container) return;

    container.innerHTML = "";
    
    if (history.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; color: var(--text-secondary); margin-top: 5rem;">
                <i class="far fa-comments" style="font-size: 3rem; margin-bottom: 1rem; color: var(--text-muted);"></i>
                <p>No messages yet. Send a message to start the conversation!</p>
            </div>
        `;
        return;
    }

    // Determine current user role from session attributes or comparison
    // Let's check sender_role in message bubble class calculation
    history.forEach(msg => {
        appendMessageBubble(msg);
    });
}

// Append single message bubble
function appendMessageBubble(msg) {
    const container = document.getElementById("chat-messages-container");
    if (!container) return;

    // Remove empty state message if it's there
    const emptyState = container.querySelector(".far");
    if (emptyState) {
        container.innerHTML = "";
    }

    // Check if the current user sent it
    // Our backend route returns msg.sender_role and msg.sender_id.
    // If the message sender_id matches partnerId, then it's a received message.
    // Otherwise, it's sent by the current user.
    const isSent = String(msg.sender_id) !== String(currentChatPartnerId);
    
    const bubble = document.createElement("div");
    bubble.className = `chat-message-bubble ${isSent ? 'sent' : 'received'}`;
    bubble.innerHTML = `
        <div class="chat-message-text">${escapeHTML(msg.message)}</div>
        <div class="chat-message-time">${msg.created_at}</div>
    `;
    
    container.appendChild(bubble);
}

// Scroll to bottom helper
function scrollToBottom() {
    const container = document.getElementById("chat-messages-container");
    if (container) {
        container.scrollTop = container.scrollHeight;
    }
}

// HTML Escape helper to prevent XSS
function escapeHTML(str) {
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
