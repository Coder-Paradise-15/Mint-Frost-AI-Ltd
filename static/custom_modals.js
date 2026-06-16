// Custom Modal Dialogs replacement for native alert, confirm, and prompt
// Styled matching the glassmorphic theme in style.css

window.customAlert = function(message, title = "Notification") {
    return new Promise((resolve) => {
        const modal = document.createElement('div');
        modal.className = 'mint-custom-modal';
        modal.innerHTML = `
            <div class="mint-custom-modal-content">
                <h3 class="mint-custom-modal-title"><i class="fas fa-info-circle" style="color: var(--mint); margin-right: 8px;"></i>${title}</h3>
                <p class="mint-custom-modal-text" style="font-size: 13px; color: #b3b3b3; margin: 0; line-height: 1.5;">${message}</p>
                <div class="mint-custom-modal-actions">
                    <button class="mint-custom-modal-btn mint-custom-modal-btn-confirm">OK</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        
        // Force reflow and show
        modal.offsetHeight;
        modal.classList.add('show');
        
        const confirmBtn = modal.querySelector('.mint-custom-modal-btn-confirm');
        confirmBtn.focus();
        
        const close = () => {
            modal.classList.remove('show');
            setTimeout(() => {
                modal.remove();
                resolve();
            }, 200);
        };
        
        confirmBtn.addEventListener('click', close);
        modal.addEventListener('click', (e) => {
            if (e.target === modal) close();
        });
        
        const keyHandler = (e) => {
            if (e.key === 'Enter' || e.key === 'Escape') {
                e.preventDefault();
                document.removeEventListener('keydown', keyHandler);
                close();
            }
        };
        document.addEventListener('keydown', keyHandler);
    });
};

window.customConfirm = function(message, title = "Confirm Action") {
    return new Promise((resolve) => {
        const modal = document.createElement('div');
        modal.className = 'mint-custom-modal';
        modal.innerHTML = `
            <div class="mint-custom-modal-content">
                <h3 class="mint-custom-modal-title"><i class="fas fa-question-circle" style="color: var(--mint); margin-right: 8px;"></i>${title}</h3>
                <p class="mint-custom-modal-text" style="font-size: 13px; color: #b3b3b3; margin: 0; line-height: 1.5;">${message}</p>
                <div class="mint-custom-modal-actions">
                    <button class="mint-custom-modal-btn mint-custom-modal-btn-cancel">Cancel</button>
                    <button class="mint-custom-modal-btn mint-custom-modal-btn-confirm">Confirm</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        
        // Force reflow and show
        modal.offsetHeight;
        modal.classList.add('show');
        
        const confirmBtn = modal.querySelector('.mint-custom-modal-btn-confirm');
        const cancelBtn = modal.querySelector('.mint-custom-modal-btn-cancel');
        confirmBtn.focus();
        
        const close = (value) => {
            modal.classList.remove('show');
            setTimeout(() => {
                modal.remove();
                resolve(value);
            }, 200);
        };
        
        confirmBtn.addEventListener('click', () => close(true));
        cancelBtn.addEventListener('click', () => close(false));
        modal.addEventListener('click', (e) => {
            if (e.target === modal) close(false);
        });
        
        const keyHandler = (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                document.removeEventListener('keydown', keyHandler);
                close(true);
            } else if (e.key === 'Escape') {
                e.preventDefault();
                document.removeEventListener('keydown', keyHandler);
                close(false);
            }
        };
        document.addEventListener('keydown', keyHandler);
    });
};

window.customPrompt = function(message, defaultValue = "", title = "Input Required") {
    return new Promise((resolve) => {
        const modal = document.createElement('div');
        modal.className = 'mint-custom-modal';
        modal.innerHTML = `
            <div class="mint-custom-modal-content">
                <h3 class="mint-custom-modal-title"><i class="fas fa-edit" style="color: var(--mint); margin-right: 8px;"></i>${title}</h3>
                <p class="mint-custom-modal-text" style="font-size: 13px; color: #b3b3b3; margin: 0; line-height: 1.5;">${message}</p>
                <input type="text" class="mint-custom-modal-input" value="${defaultValue}" />
                <div class="mint-custom-modal-actions">
                    <button class="mint-custom-modal-btn mint-custom-modal-btn-cancel">Cancel</button>
                    <button class="mint-custom-modal-btn mint-custom-modal-btn-confirm">Submit</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        
        // Force reflow and show
        modal.offsetHeight;
        modal.classList.add('show');
        
        const input = modal.querySelector('.mint-custom-modal-input');
        const confirmBtn = modal.querySelector('.mint-custom-modal-btn-confirm');
        const cancelBtn = modal.querySelector('.mint-custom-modal-btn-cancel');
        
        input.focus();
        if (defaultValue) {
            input.setSelectionRange(0, defaultValue.length);
        }
        
        const close = (value) => {
            modal.classList.remove('show');
            setTimeout(() => {
                modal.remove();
                resolve(value);
            }, 200);
        };
        
        confirmBtn.addEventListener('click', () => close(input.value));
        cancelBtn.addEventListener('click', () => close(null));
        modal.addEventListener('click', (e) => {
            if (e.target === modal) close(null);
        });
        
        const keyHandler = (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                document.removeEventListener('keydown', keyHandler);
                close(input.value);
            } else if (e.key === 'Escape') {
                e.preventDefault();
                document.removeEventListener('keydown', keyHandler);
                close(null);
            }
        };
        document.addEventListener('keydown', keyHandler);
    });
};
