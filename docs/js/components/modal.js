/* Modal confirmation dialog component */
const Modal = {
    show(title, message, onConfirm) {
        const overlay = document.getElementById('modal-overlay');
        overlay.innerHTML = `
            <div class="modal">
                <div class="modal-title">${title}</div>
                <div class="modal-body">${message}</div>
                <div class="modal-actions">
                    <button class="btn btn-outline" id="modal-cancel">Cancel</button>
                    <button class="btn btn-danger" id="modal-confirm">Delete</button>
                </div>
            </div>
        `;
        overlay.classList.remove('hidden');

        document.getElementById('modal-cancel').onclick = () => this.hide();
        document.getElementById('modal-confirm').onclick = () => {
            this.hide();
            onConfirm();
        };
        overlay.onclick = (e) => {
            if (e.target === overlay) this.hide();
        };
    },

    hide() {
        const overlay = document.getElementById('modal-overlay');
        overlay.classList.add('hidden');
        overlay.innerHTML = '';
    },
};
