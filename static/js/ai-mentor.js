// Lightweight AI Mentor demo: local chat UI with simulated replies
document.addEventListener('DOMContentLoaded', function() {
    // Require auth token for demo pages
    if (!localStorage.getItem('token')) {
        window.location.href = '/login';
        return;
    }

    const sendBtn = document.getElementById('sendBtn');
    const chatInput = document.getElementById('chatInput');
    const chatMessages = document.getElementById('chatMessages');

    function appendMessage(text, who = 'ai') {
        const div = document.createElement('div');
        div.className = `chat-message ${who}`;
        div.textContent = text;
        chatMessages.appendChild(div);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    sendBtn && sendBtn.addEventListener('click', () => {
        const text = chatInput.value && chatInput.value.trim();
        if (!text) return;
        appendMessage(text, 'user');
        chatInput.value = '';

        // Simulated AI response (demo only)
        appendMessage('Thinking...', 'ai');
        setTimeout(() => {
            // replace last ai placeholder
            const items = chatMessages.querySelectorAll('.chat-message.ai');
            const lastAi = items[items.length - 1];
            if (lastAi) lastAi.textContent = `AI Mentor: I recommend focusing on small daily goals and tracking progress. (Demo response to: "${text}")`;
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }, 800);
    });

    // support Enter key for sending
    chatInput && chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            sendBtn.click();
        }
    });
});