
<old_str>FILE_NOT_FOUND</old_str>
<new_str>/**
 * Pins and Locks Frontend Handler
 * Manages pin/lock icons, API calls, and UI updates across all pages
 */

class PinsLocksManager {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadCurrentState();
    }

    setupEventListeners() {
        // Delegate click events for pin/lock buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('pin-btn')) {
                this.handlePinToggle(e.target);
            } else if (e.target.classList.contains('lock-btn')) {
                this.handleLockToggle(e.target);
            }
        });
    }

    async loadCurrentState() {
        try {
            const [pinsResponse, locksResponse] = await Promise.all([
                fetch('/api/pins'),
                fetch('/api/locks')
            ]);

            const pinsData = await pinsResponse.json();
            const locksData = await locksResponse.json();

            this.currentPins = pinsData.pins || {};
            this.currentLocks = locksData.locks || {};

            this.updateUI();
        } catch (error) {
            console.error('Error loading pins/locks state:', error);
        }
    }

    async handlePinToggle(button) {
        const type = button.dataset.type;
        const symbol = button.dataset.symbol;

        try {
            const response = await fetch('/api/pins', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type, symbol })
            });

            const data = await response.json();
            
            if (data.success) {
                this.currentPins = data.pins;
                this.updatePinButton(button, type, symbol);
                this.showToast(`${symbol} ${data.action}`, 'success');
                this.updatePinnedCounts();
            } else {
                this.showToast('Failed to update pin', 'error');
            }
        } catch (error) {
            console.error('Error toggling pin:', error);
            this.showToast('Error updating pin', 'error');
        }
    }

    async handleLockToggle(button) {
        const type = button.dataset.type;
        const id = button.dataset.id || button.dataset.symbol;

        try {
            const response = await fetch('/api/locks', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type, id })
            });

            const data = await response.json();
            
            if (data.success) {
                this.currentLocks = data.locks;
                this.updateLockButton(button, type, id);
                this.updateRowLockState(button.closest('tr'), type, id);
                this.showToast(`${id} ${data.action}`, 'success');
            } else {
                this.showToast('Failed to update lock', 'error');
            }
        } catch (error) {
            console.error('Error toggling lock:', error);
            this.showToast('Error updating lock', 'error');
        }
    }

    updatePinButton(button, type, symbol) {
        const isPinned = this.currentPins[type.toUpperCase()]?.includes(symbol);
        button.innerHTML = isPinned ? '★' : '☆';
        button.classList.toggle('pinned', isPinned);
        button.title = isPinned ? 'Unpin item' : 'Pin item';
    }

    updateLockButton(button, type, id) {
        const isLocked = this.currentLocks[type.toUpperCase()]?.includes(id);
        button.innerHTML = isLocked ? '🔓' : '🔒';
        button.classList.toggle('locked', isLocked);
        button.title = isLocked ? 'Unlock item' : 'Lock item';
    }

    updateRowLockState(row, type, id) {
        if (!row) return;
        
        const isLocked = this.currentLocks[type.toUpperCase()]?.includes(id);
        row.classList.toggle('locked-row', isLocked);
        
        // Disable action buttons in locked rows
        const actionButtons = row.querySelectorAll('.action-btn:not(.lock-btn)');
        actionButtons.forEach(btn => {
            btn.disabled = isLocked;
            btn.style.opacity = isLocked ? '0.5' : '1';
        });
    }

    updateUI() {
        // Update all pin buttons
        document.querySelectorAll('.pin-btn').forEach(button => {
            const type = button.dataset.type;
            const symbol = button.dataset.symbol;
            this.updatePinButton(button, type, symbol);
        });

        // Update all lock buttons and row states
        document.querySelectorAll('.lock-btn').forEach(button => {
            const type = button.dataset.type;
            const id = button.dataset.id || button.dataset.symbol;
            this.updateLockButton(button, type, id);
            this.updateRowLockState(button.closest('tr'), type, id);
        });
    }

    updatePinnedCounts() {
        // Update pinned rollup counts in dashboard
        const totalPinned = Object.values(this.currentPins).reduce((sum, arr) => sum + arr.length, 0);
        const pinnedCountEl = document.querySelector('.pinned-count');
        if (pinnedCountEl) {
            pinnedCountEl.textContent = totalPinned;
        }

        // Trigger dashboard refresh if available
        if (window.fusionDashboard && typeof window.fusionDashboard.loadDashboardData === 'function') {
            window.fusionDashboard.loadDashboardData();
        }
    }

    showToast(message, type = 'info') {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <span class="toast-message">${message}</span>
                <button class="toast-close">&times;</button>
            </div>
        `;

        // Add to page
        document.body.appendChild(toast);

        // Auto remove after 3 seconds
        setTimeout(() => {
            toast.remove();
        }, 3000);

        // Manual close
        toast.querySelector('.toast-close').addEventListener('click', () => {
            toast.remove();
        });
    }

    // Utility method to add pin/lock buttons to table rows
    static addActionButtons(tableRow, type, symbol, id = null) {
        const actionsCell = document.createElement('td');
        actionsCell.className = 'actions-cell';
        
        const pinBtn = document.createElement('button');
        pinBtn.className = 'pin-btn action-btn';
        pinBtn.dataset.type = type;
        pinBtn.dataset.symbol = symbol;
        pinBtn.innerHTML = '☆';
        pinBtn.title = 'Pin item';

        const lockBtn = document.createElement('button');
        lockBtn.className = 'lock-btn action-btn';
        lockBtn.dataset.type = type;
        lockBtn.dataset.id = id || symbol;
        lockBtn.innerHTML = '🔒';
        lockBtn.title = 'Lock item';

        actionsCell.appendChild(pinBtn);
        actionsCell.appendChild(lockBtn);
        tableRow.appendChild(actionsCell);

        return actionsCell;
    }

    // Check if action is blocked by lock
    async checkActionBlocked(type, id) {
        try {
            const response = await fetch('/api/locks/check', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type, id })
            });

            if (response.status === 423) {
                const data = await response.json();
                this.showToast(data.error, 'warning');
                return true;
            }

            return false;
        } catch (error) {
            console.error('Error checking lock status:', error);
            return false;
        }
    }
}

// Initialize pins/locks manager
const pinsLocksManager = new PinsLocksManager();

// Make available globally
window.pinsLocksManager = pinsLocksManager;

// CSS for pins/locks UI
const style = document.createElement('style');
style.textContent = `
    .pin-btn, .lock-btn {
        background: none;
        border: none;
        cursor: pointer;
        font-size: 16px;
        padding: 4px;
        margin: 0 2px;
        opacity: 0.7;
        transition: opacity 0.15s ease;
    }

    .pin-btn:hover, .lock-btn:hover {
        opacity: 1;
    }

    .pin-btn.pinned {
        color: #facc15;
    }

    .lock-btn.locked {
        color: #ef4444;
    }

    .locked-row {
        background-color: rgba(239, 68, 68, 0.1);
    }

    .actions-cell {
        white-space: nowrap;
        width: 80px;
    }

    .toast {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1000;
        min-width: 250px;
        padding: 12px;
        border-radius: 8px;
        color: white;
        animation: slideIn 0.3s ease;
    }

    .toast-success {
        background-color: #22c55e;
    }

    .toast-error {
        background-color: #ef4444;
    }

    .toast-warning {
        background-color: #f59e0b;
    }

    .toast-info {
        background-color: #3b82f6;
    }

    .toast-content {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .toast-close {
        background: none;
        border: none;
        color: white;
        font-size: 20px;
        cursor: pointer;
        margin-left: 10px;
    }

    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
`;
document.head.appendChild(style);
</new_str>
