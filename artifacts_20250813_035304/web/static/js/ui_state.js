
// UI State Management for Fusion Dashboard
class UIState {
    constructor() {
        this.timeframe = this.getStoredTimeframe() || 'All';
        this.pinnedItems = this.getStoredPinnedItems() || [];
        this.lockedItems = this.getStoredLockedItems() || [];
    }

    // Timeframe management
    getStoredTimeframe() {
        return localStorage.getItem('fusion_timeframe');
    }

    setTimeframe(timeframe) {
        this.timeframe = timeframe;
        localStorage.setItem('fusion_timeframe', timeframe);
        this.updateTimeframeChips();
        this.triggerTimeframeChange();
    }

    updateTimeframeChips() {
        const chips = document.querySelectorAll('.chip[data-timeframe]');
        chips.forEach(chip => {
            if (chip.dataset.timeframe === this.timeframe) {
                chip.classList.add('active');
            } else {
                chip.classList.remove('active');
            }
        });
    }

    triggerTimeframeChange() {
        // Dispatch custom event for timeframe change
        window.dispatchEvent(new CustomEvent('timeframeChanged', {
            detail: { timeframe: this.timeframe }
        }));
    }

    // Pinned items management
    getStoredPinnedItems() {
        const stored = localStorage.getItem('fusion_pinned_items');
        return stored ? JSON.parse(stored) : [];
    }

    setPinnedItems(items) {
        this.pinnedItems = items;
        localStorage.setItem('fusion_pinned_items', JSON.stringify(items));
        this.updatePinnedIcons();
    }

    togglePinned(symbol) {
        const index = this.pinnedItems.indexOf(symbol);
        if (index > -1) {
            this.pinnedItems.splice(index, 1);
        } else {
            this.pinnedItems.push(symbol);
        }
        this.setPinnedItems(this.pinnedItems);
    }

    isPinned(symbol) {
        return this.pinnedItems.includes(symbol);
    }

    updatePinnedIcons() {
        const icons = document.querySelectorAll('[data-pin-symbol]');
        icons.forEach(icon => {
            const symbol = icon.dataset.pinSymbol;
            if (this.isPinned(symbol)) {
                icon.textContent = '⭐';
                icon.classList.add('pinned');
            } else {
                icon.textContent = '☆';
                icon.classList.remove('pinned');
            }
        });
    }

    // Locked items management
    getStoredLockedItems() {
        const stored = localStorage.getItem('fusion_locked_items');
        return stored ? JSON.parse(stored) : [];
    }

    setLockedItems(items) {
        this.lockedItems = items;
        localStorage.setItem('fusion_locked_items', JSON.stringify(items));
        this.updateLockedIcons();
    }

    toggleLocked(symbol) {
        const index = this.lockedItems.indexOf(symbol);
        if (index > -1) {
            this.lockedItems.splice(index, 1);
        } else {
            this.lockedItems.push(symbol);
        }
        this.setLockedItems(this.lockedItems);
    }

    isLocked(symbol) {
        return this.lockedItems.includes(symbol);
    }

    updateLockedIcons() {
        const icons = document.querySelectorAll('[data-lock-symbol]');
        icons.forEach(icon => {
            const symbol = icon.dataset.lockSymbol;
            if (this.isLocked(symbol)) {
                icon.textContent = '🔒';
                icon.classList.add('locked');
            } else {
                icon.textContent = '🔓';
                icon.classList.remove('locked');
            }
        });
    }

    // Initialize UI state on page load
    initialize() {
        this.updateTimeframeChips();
        this.updatePinnedIcons();
        this.updateLockedIcons();
        this.bindEventListeners();
    }

    bindEventListeners() {
        // Timeframe chip clicks
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('chip') && e.target.dataset.timeframe) {
                this.setTimeframe(e.target.dataset.timeframe);
            }
        });

        // Pin button clicks
        document.addEventListener('click', (e) => {
            if (e.target.dataset.pinSymbol) {
                e.preventDefault();
                this.togglePinned(e.target.dataset.pinSymbol);
            }
        });

        // Lock button clicks
        document.addEventListener('click', (e) => {
            if (e.target.dataset.lockSymbol) {
                e.preventDefault();
                this.toggleLocked(e.target.dataset.lockSymbol);
            }
        });
    }
}

// Global UI state instance
window.uiState = new UIState();

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.uiState.initialize();
});
