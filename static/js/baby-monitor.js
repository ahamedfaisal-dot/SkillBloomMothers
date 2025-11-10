// Simple baby monitor demo: store recent checks in localStorage and show milestones
document.addEventListener('DOMContentLoaded', function() {
    if (!localStorage.getItem('token')) {
        window.location.href = '/login';
        return;
    }

    const form = document.getElementById('monitorForm');
    const lastWeight = document.getElementById('lastWeight');
    const lastHeight = document.getElementById('lastHeight');
    const lastCheck = document.getElementById('lastCheck');
    const milestonesList = document.getElementById('milestonesList');

    function loadData() {
        const data = JSON.parse(localStorage.getItem('baby_monitor') || '{}');
        const babyNameStored = data.name || '';
        document.getElementById('babyName').textContent = babyNameStored || '—';
        document.getElementById('babyNameInput').value = babyNameStored || '';

        if (data.weight) lastWeight.textContent = data.weight + ' kg';
        else lastWeight.textContent = '—';

        if (data.height) lastHeight.textContent = data.height + ' cm';
        else lastHeight.textContent = '—';

        if (data.at) lastCheck.textContent = new Date(data.at).toLocaleString();
        else lastCheck.textContent = '—';

        if (data.cameraUrl) {
            document.getElementById('cameraUrl').value = data.cameraUrl;
            renderCamera(data.cameraUrl);
        }

        const milestones = data.milestones || [];
        milestonesList.innerHTML = '';
        if (milestones.length === 0) {
            milestonesList.innerHTML = '<li>No milestones recorded yet.</li>';
        } else {
            milestones.forEach(m => {
                const li = document.createElement('li');
                li.textContent = `${m.title} — ${m.date}`;
                milestonesList.appendChild(li);
            });
        }
    }

    async function fetchCurrentFromServer() {
        try {
            const token = localStorage.getItem('token');
            if (!token) return null;
            const res = await fetch(window.location.origin + '/api/baby/current', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!res.ok) return null;
            return await res.json();
        } catch (e) {
            console.warn('Could not fetch baby current data', e);
            return null;
        }
    }

    async function fetchProfileFromServer() {
        try {
            const token = localStorage.getItem('token');
            if (!token) return null;
            const res = await fetch(window.location.origin + '/api/baby/profile', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!res.ok) return null;
            const json = await res.json();
            // empty object means no profile
            if (!json || Object.keys(json).length === 0) return null;
            return json;
        } catch (e) {
            console.warn('Could not fetch baby profile', e);
            return null;
        }
    }

    async function saveProfileToServer(profile) {
        try {
            const token = localStorage.getItem('token');
            if (!token) return false;
            const res = await fetch(window.location.origin + '/api/baby/profile', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(profile)
            });
            return res.ok;
        } catch (e) {
            console.warn('Failed to save profile to server', e);
            return false;
        }
    }

    function renderServerData(serverData) {
        if (!serverData) return;
        document.getElementById('currentTemp').textContent = serverData.temperature + ' °C';
        document.getElementById('currentStatus').textContent = serverData.sleep_status || serverData.motion || '—';
        document.getElementById('lastCheck').textContent = new Date(serverData.timestamp).toLocaleString();

        // simple alert handling
        if (serverData.alert) {
            // show a browser alert for demo — in production use a nicer UI element
            console.warn('Baby Monitor Alert:', serverData.alert);
        }
    }

    form && form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = document.getElementById('babyNameInput').value.trim();
        const weight = document.getElementById('weight').value.trim();
        const height = document.getElementById('height').value.trim();
        const cameraUrl = document.getElementById('cameraUrl').value.trim();

        if (!name && !weight && !height && !cameraUrl) {
            alert('Enter at least one field to save.');
            return;
        }

        const stored = JSON.parse(localStorage.getItem('baby_monitor') || '{}');
        stored.name = name || stored.name;
        stored.weight = weight || stored.weight;
        stored.height = height || stored.height;
        stored.cameraUrl = cameraUrl || stored.cameraUrl;
        stored.at = new Date().toISOString();
        stored.milestones = stored.milestones || [];
        // demo milestone rule
        if (parseFloat(weight) >= 6 && !stored.milestones.find(m => m.title === 'Reached 6kg')) {
            stored.milestones.push({ title: 'Reached 6kg', date: new Date().toLocaleDateString() });
        }

        // Try to save to server first; if not available, fall back to localStorage
        const profile = {
            name: stored.name,
            weight: stored.weight,
            height: stored.height,
            camera_url: stored.cameraUrl
        };

        const savedToServer = await saveProfileToServer(profile);
        if (savedToServer) {
            // keep a local copy too
            localStorage.setItem('baby_monitor', JSON.stringify(stored));
            loadData();
            alert('Profile saved to server.');
        } else {
            localStorage.setItem('baby_monitor', JSON.stringify(stored));
            loadData();
            alert('Check and settings saved locally (demo).');
        }
        form.reset();
        // re-render camera if provided
        if (stored.cameraUrl) renderCamera(stored.cameraUrl);
    });

    function renderCamera(url) {
        const videoArea = document.getElementById('videoArea');
        const placeholder = document.getElementById('videoPlaceholder');
        // remove placeholder
        if (placeholder) placeholder.style.display = 'none';

        // remove existing frame if any
        const existing = document.getElementById('cameraFrame');
        if (existing) existing.remove();

        // For http(s) streams we can embed via iframe. For RTSP streams you'd need an intermediate proxy.
        const iframe = document.createElement('iframe');
        iframe.id = 'cameraFrame';
        iframe.src = url;
        iframe.style.width = '100%';
        iframe.style.height = '240px';
        iframe.allow = 'autoplay; encrypted-media; picture-in-picture';
        videoArea.appendChild(iframe);
    }

    async function pollServer() {
        const serverData = await fetchCurrentFromServer();
        if (serverData) {
            renderServerData(serverData);
        }
    }

    // initial load
    // Try load profile from server first, then fallback to localStorage
    (async () => {
        const prof = await fetchProfileFromServer();
        if (prof) {
            // normalize server fields to local storage format
            const stored = JSON.parse(localStorage.getItem('baby_monitor') || '{}');
            stored.name = prof.name || stored.name;
            stored.weight = prof.weight || stored.weight;
            stored.height = prof.height || stored.height;
            stored.cameraUrl = prof.camera_url || stored.cameraUrl;
            stored.at = stored.at || new Date().toISOString();
            localStorage.setItem('baby_monitor', JSON.stringify(stored));
            loadData();
        } else {
            loadData();
        }
    })();

    // poll server every 8 seconds for demo real-time updates (if authorized)
    setInterval(pollServer, 8000);
});