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

const modal = document.getElementById('podModal');
const closeModal = document.querySelector('.close');
let babyMonitorInterval;

async function loadPodProgress() {
    try {
        // Load general pods progress
        const podsResponse = await fetch(`${API_BASE}/api/pods/progress`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const pods = await podsResponse.json();
        
        pods.forEach(pod => {
            const progressBar = document.querySelector(`[data-pod="${pod.pod_type}"] .progress-fill`);
            if (progressBar) {
                progressBar.style.width = `${pod.progress}%`;
                progressBar.setAttribute('data-progress', pod.progress);
            }
        });

        // Load skill paths progress
        const skillPathsResponse = await fetch(`${API_BASE}/api/skill-pods/paths`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const skillPaths = await skillPathsResponse.json();

        skillPaths.paths.forEach(async path => {
            try {
                const progressResponse = await fetch(`${API_BASE}/api/skill-pods/progress/${path.id}`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                
                if (progressResponse.ok) {
                    const progress = await progressResponse.json();
                    const pathCard = document.querySelector(`[data-path-id="${path.id}"]`);
                    if (pathCard) {
                        const progressBar = pathCard.querySelector('.progress-fill');
                        if (progressBar) {
                            progressBar.style.width = `${progress.progress}%`;
                            progressBar.setAttribute('data-progress', progress.progress);
                        }
                    }
                }
            } catch (error) {
                console.error(`Error loading progress for skill path ${path.id}:`, error);
            }
        });

    } catch (error) {
        console.error('Error loading pod progress:', error);
    }
}

document.querySelectorAll('.pod-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
        const podType = btn.getAttribute('data-pod');
        await openPodModal(podType);
    });
});

async function openPodModal(podType) {
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    
    await enrollPod(podType);

    // fetch pod details (tasks)
    let tasks = [];
    try {
        const resp = await fetch(`${API_BASE}/api/pods/details/${podType}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const details = await resp.json();
        tasks = details.tasks || [];
    } catch (err) {
        console.error('Error fetching pod details', err);
    }

    const podTitles = {
        skill: 'Skill Pod',
        company: 'Company Pod',
        health: 'Health Pod',
        baby_monitor: 'Baby Monitor Pod',
        mental_health: 'Mental Health Pod',
        post_placement: 'Post-Placement Pod'
    };

    modalTitle.textContent = podTitles[podType] || 'Pod Details';
    
    if (podType === 'skill') {
        // getSkillPodContent is async, await it
        modalBody.innerHTML = await getSkillPodContent(tasks);
        renderPodTasks(podType, tasks);
    } else if (podType === 'company') {
        modalBody.innerHTML = getCompanyPodContent(tasks);
    } else if (podType === 'health') {
        modalBody.innerHTML = getHealthPodContent(tasks);
        setupHealthPod();
    } else if (podType === 'baby_monitor') {
        modalBody.innerHTML = getBabyMonitorContent(tasks);
        setupBabyMonitor();
    } else if (podType === 'mental_health') {
        modalBody.innerHTML = getMentalHealthContent(tasks);
        setupMentalHealthPod();
    } else if (podType === 'post_placement') {
        modalBody.innerHTML = getPostPlacementContent(tasks);
    }
    
    modal.style.display = 'block';
}

async function enrollPod(podType) {
    try {
        await fetch(`${API_BASE}/api/pods/enroll`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ pod_type: podType })
        });
    } catch (error) {
        console.error('Error enrolling in pod:', error);
    }
}

async function getSkillPodContent(tasks) {
    // Fetch available skill paths
    let skillPaths = [];
    try {
        const response = await fetch(`${API_BASE}/api/skill-pods/paths`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await response.json();
        skillPaths = data.paths;
    } catch (error) {
        console.error('Error fetching skill paths:', error);
    }

    return `
        <div class="pod-content">
            <h4>Skill Building Paths</h4>
            <p>Choose your career path and start learning:</p>
            <div class="skill-paths">
                ${skillPaths.map(path => `
                    <div class="skill-path-card" data-path-id="${path.id}">
                        <h5>${path.title}</h5>
                        <p>${path.description}</p>
                        <div class="skills-list">
                            ${path.skills.map(skill => `<span class="skill-tag">${skill}</span>`).join('')}
                        </div>
                                    <div class="path-actions">
                                        <button class="btn btn-primary enroll-btn" data-path="${path.id}">Start Learning</button>
                                        <button class="btn btn-secondary mentor-btn" data-path="${path.id}">Ask AI Mentor</button>
                                        <button class="btn btn-info assessment-btn" data-path="${path.id}">Take Assessment</button>
                                    </div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: 0%"></div>
                        </div>
                    </div>
                `).join('')}
            </div>
            <div id="podTasks"></div>
            
            <!-- AI Mentor Modal -->
            <div id="mentorModal" class="modal">
                <div class="modal-content">
                    <span class="close">&times;</span>
                    <h4>AI Mentor</h4>
                    <div class="mentor-chat">
                        <div class="chat-messages" id="chatMessages"></div>
                        <div class="chat-input">
                            <input type="text" id="mentorQuestion" placeholder="Ask your question...">
                            <button id="sendQuestion" class="btn btn-primary">Send</button>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Assessment Modal -->
            <div id="assessmentModal" class="modal">
                <div class="modal-content">
                    <span class="close">&times;</span>
                    <h4>Skill Assessment</h4>
                    <div id="assessmentContent"></div>
                </div>
            </div>
        </div>

    `;
}

// helper to render tasks into the modal
// helper to render tasks into the modal
function renderPodTasks(podType, tasks) {
    const container = document.getElementById('podTasks');
    if (!container) return;
    container.innerHTML = '';
    tasks.forEach(t => {
        const div = document.createElement('div');
        div.className = 'task-item';
        div.innerHTML = `
            <div><strong>${t.title}</strong></div>
            <div>${t.desc}</div>
            <div>
                <button class="btn btn-primary task-complete" data-taskid="${t.id}" data-progress="${t.progress}" ${t.completed ? 'disabled' : ''}>${t.completed ? 'Completed' : 'Mark Complete'}</button>
            </div>
        `;
        container.appendChild(div);
    });

    container.querySelectorAll('.task-complete').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const taskId = parseInt(btn.getAttribute('data-taskid'));
            const inc = parseInt(btn.getAttribute('data-progress')) || 10;

            // Update progress and mark task completed in pod data
            try {
                // fetch current pod data to get completed tasks
                const resp = await fetch(`${API_BASE}/api/pods/details/${podType}`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                const details = await resp.json();
                const tasksList = details.tasks || [];
                const completed = tasksList.filter(t => t.completed).map(t => t.id);
                if (!completed.includes(taskId)) completed.push(taskId);

                await fetch(`${API_BASE}/api/pods/update`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ pod_type: podType, progress: inc, data: { completed_tasks: completed } })
                });

                btn.textContent = 'Completed';
                btn.disabled = true;
                // refresh progress bars on page
                loadPodProgress();
            } catch (err) {
                console.error('Error completing task', err);
            }
        });
    });
}

function getCompanyPodContent() {
    return `
        <div class="pod-content">
            <h4>Mock Company Project</h4>
            <p><strong>Partner:</strong> TechCorp Solutions</p>
            <p><strong>Project:</strong> Design a user onboarding flow for a mobile app</p>
            <div class="progress-bar">
                <div class="progress-fill" style="width: 60%"></div>
            </div>
            <p>Progress: 60%</p>
            <p>Upon completion: <strong>Guaranteed Interview Unlocked!</strong></p>
            <button class="btn btn-primary" onclick="updatePodProgress('company', 100)">Submit Project</button>
        </div>
    `;
}

function getHealthPodContent() {
    return `
        <div class="pod-content">
            <h4>Daily Wellness Tracker</h4>
            <form id="healthForm">
                <div class="form-group">
                    <label>Mood:</label>
                    <select id="mood" class="form-control">
                        <option value="happy">Happy</option>
                            <option value="calm">Calm</option>
                            <option value="tired">Tired</option>
                            <option value="anxious">Anxious</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Sleep (hours):</label>
                    <input type="number" id="sleep" class="form-control" min="0" max="24" value="7">
                </div>
                <div class="form-group">
                    <label>Energy Level (1-10):</label>
                    <input type="number" id="energy" class="form-control" min="1" max="10" value="5">
                </div>
                <button type="submit" class="btn btn-primary">Log Health Data</button>
            </form>
        </div>
    `;
}

function getBabyMonitorContent() {
    return `
        <div class="pod-content">
            <h4>Real-Time Baby Monitoring</h4>
            <div id="babyStats" class="baby-stats">
                <div class="stat-item">
                    <strong>Temperature:</strong> <span id="babyTemp">--</span>°C
                </div>
                <div class="stat-item">
                    <strong>Motion:</strong> <span id="babyMotion">--</span>
                </div>
                <div class="stat-item">
                    <strong>Sleep Status:</strong> <span id="babySleep">--</span>
                </div>
            </div>
            <div id="babyAlert" style="display:none; background: var(--warning); padding: 1rem; border-radius: 8px; margin-top: 1rem;">
                <strong>Alert:</strong> <span id="alertMessage"></span>
            </div>
            <canvas id="babyChart" style="margin-top: 2rem;"></canvas>
        </div>
    `;
}

function getMentalHealthContent() {
    return `
        <div class="pod-content">
            <h4>Mental Health Journal</h4>
            <form id="journalForm">
                <div class="form-group">
                    <label>Today's Emotion:</label>
                    <select id="emotion" class="form-control">
                        <option value="happy">Happy</option>
                        <option value="calm">Calm</option>
                        <option value="anxious">Anxious</option>
                        <option value="stressed">Stressed</option>
                        <option value="grateful">Grateful</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Journal Entry:</label>
                    <textarea id="journalEntry" class="form-control" rows="5" placeholder="Write about your day..."></textarea>
                </div>
                <button type="submit" class="btn btn-primary">Save Entry</button>
            </form>
        </div>
    `;
}

function getPostPlacementContent() {
    return `
        <div class="pod-content">
            <h4>Career Growth Tracker</h4>
            <p>Track your post-placement progress and salary growth:</p>
            <div class="progress-section">
                <p><strong>Current Salary:</strong> $65,000</p>
                <p><strong>Target Salary:</strong> $85,000</p>
                <p><strong>Skills Acquired:</strong> 12/20</p>
                <p><strong>Time in Role:</strong> 6 months</p>
            </div>
            <canvas id="salaryChart"></canvas>
        </div>
    `;
}

function setupHealthPod() {
    const form = document.getElementById('healthForm');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const data = {
            mood: document.getElementById('mood').value,
            sleep: parseInt(document.getElementById('sleep').value),
            energy: parseInt(document.getElementById('energy').value)
        };
        
        try {
            await fetch(`${API_BASE}/api/pods/health/log`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            alert('Health data logged successfully!');
            updatePodProgress('health', 10);
        } catch (error) {
            console.error('Error logging health data:', error);
        }
    });
}

function setupBabyMonitor() {
    updateBabyMonitor();
    babyMonitorInterval = setInterval(updateBabyMonitor, 10000);
}

async function updateBabyMonitor() {
    try {
        const response = await fetch(`${API_BASE}/api/baby/current`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await response.json();
        
        document.getElementById('babyTemp').textContent = data.temperature;
        document.getElementById('babyMotion').textContent = data.motion;
        document.getElementById('babySleep').textContent = data.sleep_status;
        
        if (data.alert) {
            document.getElementById('babyAlert').style.display = 'block';
            document.getElementById('alertMessage').textContent = data.alert;
        } else {
            document.getElementById('babyAlert').style.display = 'none';
        }
    } catch (error) {
        console.error('Error updating baby monitor:', error);
    }
}

function setupMentalHealthPod() {
    const form = document.getElementById('journalForm');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const data = {
            emotion: document.getElementById('emotion').value,
            entry: document.getElementById('journalEntry').value
        };
        
        try {
            await fetch(`${API_BASE}/api/pods/mental/journal`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            alert('Journal entry saved!');
            document.getElementById('journalEntry').value = '';
            updatePodProgress('mental_health', 5);
        } catch (error) {
            console.error('Error saving journal:', error);
        }
    });
}

async function updatePodProgress(podType, progressIncrease) {
    const progressBar = document.querySelector(`[data-pod="${podType}"] .progress-fill`);
    const currentProgress = parseInt(progressBar.getAttribute('data-progress')) || 0;
    const newProgress = Math.min(currentProgress + progressIncrease, 100);
    
    try {
        const response = await fetch(`${API_BASE}/api/pods/update`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ pod_type: podType, progress: newProgress })
        });
        
        const data = await response.json();
        
        progressBar.style.width = `${newProgress}%`;
        progressBar.setAttribute('data-progress', newProgress);
        
        if (data.badge_earned) {
            alert(data.message);
        }
    } catch (error) {
        console.error('Error updating progress:', error);
    }
}

closeModal.addEventListener('click', () => {
    modal.style.display = 'none';
    if (babyMonitorInterval) {
        clearInterval(babyMonitorInterval);
    }
});

window.addEventListener('click', (e) => {
    if (e.target === modal) {
        modal.style.display = 'none';
        if (babyMonitorInterval) {
            clearInterval(babyMonitorInterval);
        }
    }
});

loadPodProgress();
