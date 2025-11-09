const API_BASE = window.location.origin;
const token = localStorage.getItem('token');

if (!token) {
    window.location.href = '/login';
}

const logoutLink = document.getElementById('logoutLink');
if (logoutLink) {
    logoutLink.addEventListener('click', (e) => {
        e.preventDefault();
        localStorage.clear();
        window.location.href = '/login';
    });
}

let currentStep = 1;
let personalityAnswers = [];
let skillAnswers = [];

async function loadPersonalityQuestions() {
    try {
        const response = await fetch(`${API_BASE}/api/assessment/personality/questions`);
        const questions = await response.json();
        
        const container = document.getElementById('personalityQuestions');
        questions.forEach(q => {
            const div = document.createElement('div');
            div.className = 'question-item';
            div.innerHTML = `
                <p><strong>${q.id}. ${q.question}</strong></p>
                <div class="rating-scale">
                    ${[1, 2, 3, 4, 5].map(rating => `
                        <input type="radio" id="q${q.id}_${rating}" name="q${q.id}" value="${rating}" required>
                        <label for="q${q.id}_${rating}">${rating}</label>
                    `).join('')}
                </div>
            `;
            container.appendChild(div);
        });
    } catch (error) {
        console.error('Error loading questions:', error);
    }
}

const personalityForm = document.getElementById('personalityForm');
personalityForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(personalityForm);
    personalityAnswers = [];
    let missingAnswers = false;
    
    // Check all questions are answered
    document.querySelectorAll('.question-item').forEach(item => {
        const inputs = item.querySelectorAll('input[type="radio"]');
        const questionId = parseInt(inputs[0].name.substring(1));
        const selected = Array.from(inputs).find(input => input.checked);
        
        if (!selected) {
            missingAnswers = true;
            item.classList.add('error');
        } else {
            item.classList.remove('error');
            personalityAnswers.push({
                question_id: questionId,
                rating: parseInt(selected.value)
            });
        }
    });
    
    if (missingAnswers) {
        alert('Please answer all questions before submitting.');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/assessment/personality/submit`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ answers: personalityAnswers })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to submit personality assessment');
        }
        
        const data = await response.json();
        localStorage.setItem('personality_type', data.personality_type);
        
        goToStep(2);
    } catch (error) {
        console.error('Error submitting personality test:', error);
        alert('Error submitting test. Please try again.');
    }
});

const skillCategory = document.getElementById('skillCategory');
skillCategory.addEventListener('change', async () => {
    const category = skillCategory.value;
    if (!category) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/assessment/skill/questions/${category}`);
        const questions = await response.json();
        
        const container = document.getElementById('skillQuestions');
        container.innerHTML = '';
        
        questions.forEach(q => {
            const div = document.createElement('div');
            div.className = 'question-item';
            div.innerHTML = `
                <p><strong>${q.id}. ${q.question}</strong></p>
                <div class="mcq-options">
                    ${q.options.map((option, index) => `
                        <input type="radio" id="q${q.id}_${index}" name="q${q.id}" value="${index}" required style="display:none;">
                        <label for="q${q.id}_${index}">${option}</label>
                    `).join('')}
                </div>
            `;
            container.appendChild(div);
        });
        
        document.getElementById('skillForm').style.display = 'block';
    } catch (error) {
        console.error('Error loading skill questions:', error);
    }
});

const skillForm = document.getElementById('skillForm');
skillForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const category = skillCategory.value;
    if (!category) {
        alert('Please select a skill category.');
        return;
    }
    
    const formData = new FormData(skillForm);
    skillAnswers = [];
    let missingAnswers = false;
    
    // Check all questions are answered
    document.querySelectorAll('.question-item').forEach(item => {
        const inputs = item.querySelectorAll('input[type="radio"]');
        const questionId = parseInt(inputs[0].name.substring(1));
        const selected = Array.from(inputs).find(input => input.checked);
        
        if (!selected) {
            missingAnswers = true;
            item.classList.add('error');
        } else {
            item.classList.remove('error');
            skillAnswers.push({
                question_id: questionId,
                selected_option: parseInt(selected.value)
            });
        }
    });
    
    if (missingAnswers) {
        alert('Please answer all questions before submitting.');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/assessment/skill/submit`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ category, answers: skillAnswers })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to submit skill assessment');
        }
        
        const data = await response.json();
        displayResults(data);
        goToStep(3);
    } catch (error) {
        console.error('Error submitting skill test:', error);
        alert('Error submitting test. Please try again.');
    }
});

function displayResults(skillData) {
    const container = document.getElementById('resultsContent');
    const personalityType = localStorage.getItem('personality_type');
    
    container.innerHTML = `
        <div class="result-section">
            <h3>Personality Type: ${personalityType}</h3>
            <p>You have a ${personalityType} personality, which is valuable in many career paths.</p>
        </div>
        <div class="result-section">
            <h3>Skill Assessment: ${skillData.category}</h3>
            <p>Score: <strong>${skillData.score}%</strong></p>
            <p>You answered ${skillData.correct} out of ${skillData.total} questions correctly!</p>
        </div>
        <div class="result-section">
            <p>${skillData.message}</p>
            <p>Visit your dashboard to see personalized career recommendations!</p>
        </div>
    `;

    // Fetch recommendations from backend
    try {
        fetch(`${API_BASE}/api/assessment/recommend`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ personality_type: personalityType, skill: { category: skillData.category, score: skillData.score } })
        }).then(r => r.json()).then(data => {
            if (!data.recommendations) return;
            const recs = data.recommendations;
            const list = document.createElement('div');
            list.className = 'recommendations';
            list.innerHTML = `<h3>Recommended Roles</h3>`;
            recs.forEach(r => {
                const item = document.createElement('div');
                item.className = 'rec-item';
                item.innerHTML = `
                    <h4>${r.role}</h4>
                    <p>Suggested Pods: ${r.pods.join(', ')}</p>
                    <button class="btn btn-primary" data-role="${r.role}" data-pods='${JSON.stringify(r.pods)}'>Enroll Suggested Pods</button>
                `;
                list.appendChild(item);
            });
            container.appendChild(list);

            // Attach enroll handlers
            container.querySelectorAll('.rec-item button').forEach(btn => {
                btn.addEventListener('click', async () => {
                    const pods = JSON.parse(btn.getAttribute('data-pods'));
                    for (const p of pods) {
                        await enrollPod(p);
                    }
                    alert('Suggested pods enrolled (or demo enrolled). Visit Pods to start tasks.');
                });
            });
        });
    } catch (err) {
        console.error('Error fetching recommendations', err);
    }
}

function goToStep(step) {
    document.querySelectorAll('.test-section').forEach(section => {
        section.classList.remove('active');
    });
    document.querySelectorAll('.step').forEach(s => {
        s.classList.remove('active');
    });
    
    if (step === 1) {
        document.getElementById('personalityTest').classList.add('active');
    } else if (step === 2) {
        document.getElementById('skillTest').classList.add('active');
    } else if (step === 3) {
        document.getElementById('results').classList.add('active');
    }
    
    document.querySelector(`.step[data-step="${step}"]`).classList.add('active');
}

loadPersonalityQuestions();
