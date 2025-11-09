const API_BASE = window.location.origin;
const token = localStorage.getItem('token');
const userName = localStorage.getItem('user_name');

if (!token) {
    window.location.href = '/login';
}

document.getElementById('userName').textContent = userName || 'User';

const logoutLink = document.getElementById('logoutLink');
if (logoutLink) {
    logoutLink.addEventListener('click', (e) => {
        e.preventDefault();
        localStorage.clear();
        window.location.href = '/login';
    });
}

async function loadDashboardData() {
    try {
        const [assessmentRes, podRes, recommendationRes] = await Promise.all([
            fetch(`${API_BASE}/api/assessment/results`, {
                headers: { 'Authorization': `Bearer ${token}` }
            }),
            fetch(`${API_BASE}/api/pods/progress`, {
                headers: { 'Authorization': `Bearer ${token}` }
            }),
            fetch(`${API_BASE}/api/ai/recommendation`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({})
            })
        ]);
        
        const assessmentData = await assessmentRes.json();
        const podData = await podRes.json();
        
        displayAssessmentResults(assessmentData);
        displayPodProgress(podData);
        
        if (recommendationRes.ok) {
            const recommendationData = await recommendationRes.json();
            displayRecommendations(recommendationData);
        } else {
            document.getElementById('recommendations').innerHTML = '<p>Complete your assessment to get career recommendations!</p>';
        }
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

function displayAssessmentResults(data) {
    const container = document.getElementById('assessmentResults');
    
    if (data.length === 0) {
        container.innerHTML = '<p>No assessment completed yet. <a href="/assessment">Take Assessment</a></p>';
        return;
    }
    
    const personality = data.find(a => a.test_type === 'personality');
    const skill = data.find(a => a.test_type === 'skill');
    
    let html = '';
    if (personality) {
        html += `<div class="result-item">
            <strong>Personality Type:</strong> ${personality.personality_type}
            <br><strong>Score:</strong> ${personality.score.toFixed(1)}%
        </div>`;
    }
    
    if (skill) {
        html += `<div class="result-item">
            <strong>Skill Category:</strong> ${skill.skill_category}
            <br><strong>Score:</strong> ${skill.score.toFixed(1)}%
        </div>`;
    }
    
    container.innerHTML = html;
}

function displayPodProgress(data) {
    const canvas = document.getElementById('podProgressChart');
    
    if (data.length === 0) {
        canvas.parentElement.innerHTML = '<p>No pod activity yet. <a href="/pods">Explore Pods</a></p>';
        return;
    }
    
    const podTypes = data.map(p => p.pod_type.replace('_', ' ').toUpperCase());
    const progress = data.map(p => p.progress);
    
    new Chart(canvas, {
        type: 'bar',
        data: {
            labels: podTypes,
            datasets: [{
                label: 'Progress (%)',
                data: progress,
                backgroundColor: 'rgba(20, 184, 166, 0.6)',
                borderColor: '#14b8a6',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    });
}

function displayRecommendations(data) {
    const container = document.getElementById('recommendations');
    
    if (!data.recommendations) {
        container.innerHTML = '<p>Complete your assessment to get recommendations!</p>';
        return;
    }
    
    let html = `<p><strong>Based on your ${data.personality} personality:</strong></p>`;
    data.recommendations.forEach(rec => {
        html += `<div class="activity-item">
                <span class="activity-icon"></span>
            <div>
                <strong>${rec.role}</strong> (${rec.match_score}% match)
                <br><small>${rec.reason}</small>
            </div>
        </div>`;
    });
    
    container.innerHTML = html;
}

const chatbotModal = document.getElementById('chatbotModal');
const openChatbot = document.getElementById('openChatbot');
const aiMentorLink = document.getElementById('aiMentorLink');
const closeModal = document.querySelector('.close');

[openChatbot, aiMentorLink].forEach(btn => {
    if (btn) {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            chatbotModal.style.display = 'block';
        });
    }
});

if (closeModal) {
    closeModal.addEventListener('click', () => {
        chatbotModal.style.display = 'none';
    });
}

window.addEventListener('click', (e) => {
    if (e.target === chatbotModal) {
        chatbotModal.style.display = 'none';
    }
});

const sendChat = document.getElementById('sendChat');
const chatInput = document.getElementById('chatInput');
const chatMessages = document.getElementById('chatMessages');

sendChat.addEventListener('click', sendMessage);
chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

async function sendMessage() {
    const query = chatInput.value.trim();
    if (!query) return;
    
    appendMessage(query, 'user');
    chatInput.value = '';
    
    try {
        const response = await fetch(`${API_BASE}/api/ai/chat`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query })
        });
        
        const data = await response.json();
        appendMessage(data.response, 'ai');
    } catch (error) {
        appendMessage('Sorry, I encountered an error. Please try again.', 'ai');
    }
}

function appendMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}`;
    messageDiv.textContent = text;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

loadDashboardData();
