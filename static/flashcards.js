// Delete Modal Functionality
document.addEventListener('DOMContentLoaded', function () {
    const delBtn = document.getElementById('deleteBtn');
    const modal = document.getElementById('confirmDeleteModal');
    const cancel = document.getElementById('cancelDelete');
    const closeX = document.getElementById('closeDeleteModal');

    function showModal() { modal.classList.remove('d-none'); document.body.style.overflow = 'hidden'; }
    function hideModal() { modal.classList.add('d-none'); document.body.style.overflow = ''; }

    if (delBtn) delBtn.addEventListener('click', function (e) { e.preventDefault(); showModal(); });
    if (cancel) cancel.addEventListener('click', hideModal);
    if (closeX) closeX.addEventListener('click', hideModal);

    // Click outside dialog to close
    if (modal) modal.addEventListener('click', function (e) {
        if (e.target === modal) hideModal();
    });

    // Escape key to close
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && modal && !modal.classList.contains('d-none')) hideModal();
    });
});
