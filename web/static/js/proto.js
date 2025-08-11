
// Pin/Lock UI helper functions
async function postJSON(url, body) {
    return fetch(url, {
        method: "POST",
        headers: {"content-type": "application/json"},
        body: JSON.stringify(body)
    }).then(r => r.json());
}

window.pinItem = async (type, symbol) => {
    const cur = await fetch("/api/pins").then(r => r.json());
    const items = cur.items || [];
    if (!items.find(x => x.type === type && x.symbol === symbol)) {
        items.push({type, symbol});
    }
    await postJSON("/api/pins", {items});
    document.getElementById("refresh")?.click();
};

window.lockItem = async (type, id) => {
    const cur = await fetch("/api/locks").then(r => r.json());
    const items = cur.items || [];
    if (!items.find(x => x.type === type && x.id === id)) {
        items.push({type, id});
    }
    await postJSON("/api/locks", {items});
    document.getElementById("refresh")?.click();
};

// Utility function for adding pin/lock buttons to tables
function addActionButtons(container, type, identifier) {
    const pinBtn = document.createElement('button');
    pinBtn.innerHTML = '⭐';
    pinBtn.title = 'Pin item';
    pinBtn.onclick = () => pinItem(type, identifier);
    
    const lockBtn = document.createElement('button');
    lockBtn.innerHTML = '🔒';
    lockBtn.title = 'Lock item';
    lockBtn.onclick = () => lockItem(type, identifier);
    
    container.appendChild(pinBtn);
    container.appendChild(lockBtn);
}
