// Dynamic new-card rows for flashcard edit page
(function () {
    function renumberAllCards() {
        const list = document.querySelector('.list-group.list-group-flush');
        if (!list) return;
        let idx = 1;

        // Renumber existing server-rendered card items (immediate children that are card rows)
        Array.from(list.children).forEach(child => {
            if (!child.classList.contains('list-group-item')) return;
            // skip the "new cards" container and the final save area
            if (child.classList.contains('bg-light') || child.classList.contains('text-end')) return;

            // update visible number
            const strong = child.querySelector('strong');
            if (strong) strong.textContent = String(idx);

            // update input names for server-side fields
            const frontEl = child.querySelector('textarea[name^="front_"], input[name^="front_"]');
            if (frontEl) frontEl.name = 'front_' + idx;
            const backEl = child.querySelector('textarea[name^="back_"], input[name^="back_"]');
            if (backEl) backEl.name = 'back_' + idx;

            const delEl = child.querySelector('input[type="checkbox"][name^="delete_"]');
            if (delEl) {
                const newName = 'delete_' + idx;
                const newId = 'delete_' + idx;
                delEl.name = newName;
                delEl.id = newId;
                const lab = child.querySelector('label[for^="delete_"]');
                if (lab) lab.setAttribute('for', newId);
            }

            idx++;
        });

        // Now assign numbers to any new-card rows (they use new_front[] names but should display continuous numbering)
        const newContainer = document.getElementById('new-cards-container');
        if (newContainer) {
            const newRows = Array.from(newContainer.querySelectorAll('.new-card-row')).filter(r => !r.classList.contains('d-none'));
            newRows.forEach(nr => {
                const numEl = nr.querySelector('.card-number');
                if (numEl) numEl.textContent = String(idx);
                idx++;
            });
        }
    }

    function addNewCardRow(front, back) {
        const tmpl = document.getElementById('new-card-template');
        if (!tmpl) return;
        // Clone the full template so structure/classes are preserved
        const clone = tmpl.cloneNode(true);
        // Ensure it doesn't keep the template id and is visible
        clone.removeAttribute('id');
        clone.classList.remove('d-none');
        // Ensure expected wrapper class exists
        if (!clone.classList.contains('new-card-row')) clone.classList.add('new-card-row');

        // set values if provided (support textarea or input)
        if (front !== undefined && front !== null) {
            const f = clone.querySelector('textarea[name="new_front[]"], input[name="new_front[]"]');
            if (f) {
                f.value = front;
            }
        }
        if (back !== undefined && back !== null) {
            const b = clone.querySelector('textarea[name="new_back[]"], input[name="new_back[]"]');
            if (b) {
                b.value = back;
            }
        }

        // wire remove button
        const btn = clone.querySelector('.remove-new-card');
        if (btn) {
            btn.addEventListener('click', function () {
                clone.remove();
                try { window.renumberAllCards && window.renumberAllCards(); } catch (e) { }
            });
        }

        // Insert into the main list at the top when possible, otherwise prepend to new-cards container
        const list = document.querySelector('.list-group.list-group-flush');
        if (list) list.insertBefore(clone, list.firstChild);
        else {
            const container = document.getElementById('new-cards-container');
            if (container) container.insertBefore(clone, container.firstChild);
            else document.getElementById('new-cards-container').appendChild(clone);
        }
        // Trigger auto-expand on appended textareas now that they're in the DOM
        try {
            const autos = clone.querySelectorAll('.auto-expand');
            autos.forEach(el => {
                try { el.dispatchEvent(new Event('input', { bubbles: true })); } catch (e) { }
            });
        } catch (e) { }
        // Update numbering after insert
        try { window.renumberAllCards && window.renumberAllCards(); } catch (e) { }
    }

    // expose for other scripts to programmatically add new card rows and renumbering
    window.addNewCardRow = addNewCardRow;
    window.renumberAllCards = renumberAllCards;

    document.addEventListener('DOMContentLoaded', function () {
        const addBtn = document.getElementById('add-new-card');
        if (addBtn) {
            addBtn.addEventListener('click', function () {
                addNewCardRow('', '');
            });
        }

        // initialize numbering for any server-rendered cards or pre-existing new rows
        try { window.renumberAllCards && window.renumberAllCards(); } catch (e) { }

        // No prefill-handling necessary; new rows will be added by the user.
    });
})();

// Highlight header/footer nav link using the folder slug
document.addEventListener('DOMContentLoaded', function () {
    try {
        const navAreas = [];
        const header = document.querySelector('header');
        if (header) navAreas.push(header);
        const footers = Array.from(document.querySelectorAll('footer'));
        navAreas.push(...footers);

        const parts = location.pathname.split('/').filter(Boolean);
        const currentSlug = parts.length >= 2 ? parts[parts.length - 2] : (parts[0] || 'home');

        navAreas.forEach(area => {
            const links = Array.from(area.querySelectorAll('a[href]'));
            links.forEach(a => {
                try {
                    if (a.id === "logoButton") return;
                    const url = new URL(a.getAttribute('href'), location.origin);
                    const linkParts = url.pathname.split('/').filter(Boolean);
                    const linkSlug = linkParts.length >= 2 ? linkParts[linkParts.length - 2] : (linkParts[0] || 'home');

                    a.classList.remove('active', 'text-primary', 'fw-bold', 'text-white', 'btn-primary');

                    if (linkSlug === currentSlug) {
                        if (a.classList.contains('btn')) {
                            a.classList.remove('btn-light');
                            a.classList.add('btn-primary', 'text-white');
                        } else {
                            a.classList.add('text-primary', 'fw-bold');
                        }
                        a.classList.add('active');
                    } else {
                        if (!a.classList.contains('btn')) {
                            a.classList.remove('text-primary', 'fw-bold');
                            a.classList.add('text-muted');
                        }
                        if (a.classList.contains('btn') && !a.classList.contains('btn-light')) {
                            a.classList.add('btn-light');
                        }
                    }
                } catch (e) { }
            });
        });
    } catch (e) { }
});

//Chat API logic
document.addEventListener('DOMContentLoaded', function () {
    const sendBtn = document.getElementById('chat-send-btn');
    // preserve original button content so we can restore after loading
    const sendBtnOriginalHTML = sendBtn ? sendBtn.innerHTML : '';
    const messageInput = document.getElementById('chat-message-input');
    const chatBody = document.getElementById('floating-chat-body');
    const fileInput = document.getElementById('file-drop-input');
    const fileDropArea = document.getElementById('file-drop');

    // Attempt to parse AI responses that may be wrapped or slightly malformed.
    function tryParseAIJSON(text) {
        if (!text || typeof text !== 'string') return null;
        let candidate = text.trim();

        // 1) Extract fenced ```json blocks first
        const fence = candidate.match(/```(?:json)?\s*([\s\S]*?)\s*```/i);
        if (fence && fence[1]) {
            candidate = fence[1].trim();
        } else {
            // 2) Fallback: find first {...} substring
            const s = candidate.indexOf('{');
            const e = candidate.lastIndexOf('}');
            if (s !== -1 && e !== -1 && e > s) {
                candidate = candidate.slice(s, e + 1).trim();
            }
        }

        // 3) Try straight JSON.parse
        try {
            return JSON.parse(candidate);
        } catch (e) {
            // continue to fallbacks
        }

        // 4) Conservative cleanup: remove trailing commas, replace single quotes
        try {
            let cand2 = candidate.replace(/,\s*([}\]])/g, '$1');
            cand2 = cand2.replace(/\u2018|\u2019|\u201C|\u201D/g, '"'); // smart quotes
            // Replace single quotes with double quotes only when likely delimiting keys/strings
            cand2 = cand2.replace(/([:\[,\{\s])'([^']*)'/g, '$1"$2"');
            // fix a few common transcription typos (e.g. Turkish 'ş' in 'flaşcards')
            cand2 = cand2.replace(/flaşcards/gi, 'flashcards');
            // final attempt
            return JSON.parse(cand2);
        } catch (e2) {
            return null;
        }
    }

    // Helper: Add message to UI
    function appendMessage(text, sender) {
        const msgDiv = document.createElement('div');
        msgDiv.style.marginBottom = "10px";
        msgDiv.style.padding = "8px";
        msgDiv.style.borderRadius = "5px";

        if (sender === 'user') {
            msgDiv.style.background = "#e9ecef";
            msgDiv.style.textAlign = "right";
            msgDiv.innerHTML = `<strong>You:</strong> ${text}`;
        } else {
            msgDiv.style.background = "#d1e7dd";
            msgDiv.innerHTML = `<strong>AI:</strong> ${text}`;
        }
        chatBody.appendChild(msgDiv);
        chatBody.scrollTop = chatBody.scrollHeight; // Auto-scroll
    }

    // 1. Handle Sending
    async function sendMessage() {
        const text = messageInput.value.trim();
        const file = fileInput.files[0];

        if (!text && !file) return;

        // Clear input
        messageInput.value = '';

        // Show user message immediately
        appendMessage(text + (file ? ` [Attached: ${file.name}]` : ''), 'user');

        // Show loading state
        const loadingDiv = document.createElement('div');
        loadingDiv.textContent = "AI is thinking...";
        loadingDiv.classList.add("text-muted", "small");
        chatBody.appendChild(loadingDiv);

        // Prepare Data
        const formData = new FormData();
        formData.append('message', text);
        if (file) {
            // include the filename explicitly to ensure Flask/Werkzeug recognizes it correctly
            try { formData.append('file', file, file.name); } catch (e) { formData.append('file', file); }
        }

        // Show loading state on send button and disable it to prevent duplicates
        if (sendBtn) {
            try {
                sendBtn.disabled = true;
            } catch (e) { }
            sendBtn.setAttribute('aria-busy', 'true');
            sendBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>';
        }

            try {
                const response = await fetch('/api/chat-proxy', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                // Remove loading indicator from chat body
                chatBody.removeChild(loadingDiv);

                if (data.status === 'success') {
                    // Prefer structured JSON response from the AI proxy
                    const jsonResp = data.json || data.jsonResp || null;
                    const feedback = data.feedback || null;

                    if (feedback) {
                        appendMessage(feedback, 'ai');
                    }

                        if (jsonResp) {
                        try {
                            // jsonResp may already be an object or a JSON string
                            let parsed = jsonResp;
                            // parsed may be string or object
                            if (typeof parsed === 'string') {
                                // First try native parse, then fallbacks that extract code fences
                                try {
                                    parsed = JSON.parse(parsed);
                                } catch (e) {
                                    const tried = tryParseAIJSON(parsed);
                                    if (tried) {
                                        parsed = tried;
                                    } else {
                                        console.error('Failed to parse AI JSON response (client fallback)', e);
                                        appendMessage('Parsing error: ' + e.message, 'ai');
                                        parsed = null;
                                    }
                                }
                            }

                            // Normalize common alternative keys from different LLMs
                            if (parsed && typeof parsed === 'object') {
                                if (!parsed.name && parsed.deck_name) parsed.name = parsed.deck_name;
                                if (!parsed.summary && parsed.deck_summary) parsed.summary = parsed.deck_summary;
                                if (!parsed.flashcards && parsed.flaşcards) parsed.flashcards = parsed.flaşcards;
                                if (!feedback && parsed.user_feedback) {
                                    appendMessage(parsed.user_feedback, 'ai');
                                }
                            }

                            // Find flashcards array
                            let flashcardsArray = null;
                            if (parsed && typeof parsed === 'object') {
                                const candidateKeys = ['flashcards', 'cards', 'items', 'flaashcards', 'flaash_cards', 'flaashcard', 'flaşcards'];
                                for (let i = 0; i < candidateKeys.length; i++) {
                                    const k = candidateKeys[i];
                                    if (parsed[k] && Array.isArray(parsed[k])) {
                                        flashcardsArray = parsed[k];
                                        break;
                                    }
                                }
                                if (!flashcardsArray && parsed.flaashcards && Array.isArray(parsed.flaashcards)) {
                                    flashcardsArray = parsed.flaashcards;
                                    parsed.flashcards = parsed.flaashcards;
                                }
                            }

                            if (flashcardsArray && Array.isArray(flashcardsArray) && flashcardsArray.length > 0) {
                                flashcardsArray.forEach(fc => {
                                    const front = fc.front || fc.question || fc.prompt || '';
                                    const back = fc.back || fc.answer || fc.response || '';
                                    if (window.addNewCardRow) {
                                        window.addNewCardRow(front, back);
                                    } else {
                                        const tmpl = document.getElementById('new-card-template');
                                        if (tmpl) {
                                            const clone = tmpl.cloneNode(true);
                                            clone.id = '';
                                            clone.classList.remove('d-none');
                                            const f = clone.querySelector('textarea[name="new_front[]"], input[name="new_front[]"]');
                                            const b = clone.querySelector('textarea[name="new_back[]"], input[name="new_back[]"]');
                                            if (f) f.value = front;
                                            if (b) b.value = back;
                                            const btn = clone.querySelector('.remove-new-card');
                                            if (btn) btn.addEventListener('click', () => clone.remove());
                                                    const list = document.querySelector('.list-group.list-group-flush');
                                                    if (list) list.insertBefore(clone, list.firstChild);
                                                    else {
                                                        const container = document.getElementById('new-cards-container');
                                                        if (container) container.insertBefore(clone, container.firstChild);
                                                        else document.getElementById('new-cards-container').appendChild(clone);
                                                    }
                                        }
                                    }
                                });
                                // Ensure numbering is consistent after AI-inserted cards
                                try { window.renumberAllCards && window.renumberAllCards(); } catch (e) { }

                                if (parsed && parsed.name) {
                                    const nameField = document.getElementsByName('deck_name')[0];
                                    if (nameField) nameField.value = parsed.name;
                                }
                                if (parsed && parsed.summary) {
                                    const summaryField = document.getElementsByName('deck_summary')[0];
                                    if (summaryField) summaryField.value = parsed.summary;
                                }

                                const form = document.querySelector('form');
                                const noticeId = 'ai-save-notice-container';
                                let notice = document.getElementById(noticeId);
                                if (!notice) {
                                    notice = document.createElement('div');
                                    notice.id = noticeId;
                                    notice.className = 'mb-3';
                                    const saveArea = document.querySelector('.list-group-item.py-3.text-end');
                                    if (saveArea && saveArea.parentNode) {
                                        saveArea.parentNode.insertBefore(notice, saveArea);
                                    } else if (form) {
                                        form.insertBefore(notice, form.firstChild);
                                    }
                                }
                                notice.innerHTML = `\n        <div class="alert alert-info d-flex justify-content-between align-items-center mb-0">\n            <div>AI added <strong>${flashcardsArray.length}</strong> card(s) to this form. Review them and click <strong>Save changes</strong> to persist.</div>\n            <div><button type="submit" class="btn btn-sm btn-primary" id="ai-save-now">Save now</button></div>\n        </div>`;
                                appendMessage('Added ' + flashcardsArray.length + ' card(s) to the edit form. Click Save changes to persist.', 'ai');
                            } else {
                                // No flashcards were produced — surface feedback or raw reply instead
                                const noCardsMessage = (parsed && parsed.feedback) ? parsed.feedback : (data.reply || JSON.stringify(parsed));
                                appendMessage(noCardsMessage, 'ai');
                            }
                        } catch (procErr) {
                            console.error('Error processing AI response', procErr);
                            appendMessage('Processing error: ' + (procErr && procErr.message ? procErr.message : String(procErr)), 'ai');
                        }
                    } else {
                        appendMessage(data.reply || 'No structured content returned', 'ai');
                    }
                } else {
                    const errMsg = data.message || 'Unknown error from AI proxy';
                    appendMessage("Error: " + errMsg, 'ai');
                }

                // Reset file input
                fileInput.value = "";

            } catch (error) {
                // Remove loading indicator from chat body if present
                try { chatBody.removeChild(loadingDiv); } catch (e) { }
                console.error('Network/sendMessage error', error);
                appendMessage("Network Error: " + (error && error.message ? error.message : String(error)), 'ai');
            } finally {
                // Restore send button state
                if (sendBtn) {
                    sendBtn.disabled = false;
                    sendBtn.removeAttribute('aria-busy');
                    sendBtn.innerHTML = sendBtnOriginalHTML;
                }
            }
    }

    // Event Listeners
    sendBtn.addEventListener('click', sendMessage);

    messageInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') sendMessage();
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            fileDropArea.style.color = "green"; // Visual feedback
            alert(`File selected: ${fileInput.files[0].name}`);
        }
    });
});

    // Share modal logic
    document.addEventListener('DOMContentLoaded', function () {
        const shareBtn = document.getElementById('shareBtn');
        const shareModalEl = document.getElementById('shareModal');
        const shareList = document.getElementById('share-list');
        const shareSearch = document.getElementById('share-search');
        const shareSave = document.getElementById('share-save');
        const shareEmpty = document.getElementById('share-empty');
        // Use a static backdrop + disable ESC to prevent accidental closes
        const bsModal = shareModalEl ? new bootstrap.Modal(shareModalEl, { backdrop: 'static', keyboard: false }) : null;

        function renderList(users, perms) {
            // users: array of profile objects or username strings
            console.debug('renderList users=', users, 'perms=', perms);
            shareList.innerHTML = '';
            if (!users || users.length === 0) {
                shareEmpty.classList.remove('d-none');
                return;
            }
            shareEmpty.classList.add('d-none');
            users.forEach(u => {
                const tr = document.createElement('tr');
                const uname = (u && u.username) ? u.username : u;
                const display = (u && (u.display_name || u.name)) ? (u.display_name || u.name) : uname;
                const isOwner = perms && perms.owner && perms.owner === uname;
                // determine checked state from perms (perms may contain arrays of usernames)
                const isEditor = perms && Array.isArray(perms.editors) && perms.editors.includes(uname);
                const isReviewer = perms && Array.isArray(perms.reviewers) && perms.reviewers.includes(uname);

                tr.dataset.username = uname;
                tr.innerHTML = `
                    <td>${display} <div class="small text-muted">${uname}</div></td>
                    <td class="text-center"><input data-username="${uname}" class="form-check-input share-editor" type="checkbox" ${isEditor ? 'checked' : ''}></td>
                    <td class="text-center"><input data-username="${uname}" class="form-check-input share-reviewer" type="checkbox" ${isReviewer ? 'checked' : ''}></td>
                `;
                shareList.appendChild(tr);
            });
        }

        async function openShare() {
            const friends = window.SHARE_FRIENDS || [];
            let perms = null;
            try {
                const res = await fetch(`/flashcards/${window.CURRENT_DECK_ID}/permissions`);
                const body = await res.json();
                if (body.ok) perms = body.permissions;
            } catch (e) { /* ignore */ }

            // Fetch authoritative user list from server
            let allUsers = [];
            try {
                const res2 = await fetch('/flashcards/userlist');
                const data2 = await res2.json();
                if (data2 && Array.isArray(data2.users)) allUsers = data2.users;
            } catch (e) { /* ignore */ }

            // Build an ordered list: owner, editors, reviewers, then remaining users from allUsers
            const users = [];
            const seen = new Set();

            function pushUserByName(uname) {
                if (!uname || seen.has(uname)) return;
                // attempt to find full profile in friends
                const prof = friends.find(f => (f && f.username) === uname);
                users.push(prof || { username: uname });
                seen.add(uname);
            }

            if (perms) {
                if (perms.owner) pushUserByName(perms.owner);
                if (Array.isArray(perms.editors)) perms.editors.forEach(pushUserByName);
                if (Array.isArray(perms.reviewers)) perms.reviewers.forEach(pushUserByName);
            }

            // then append all users from server list
            allUsers.forEach(u => {
                const uname = (typeof u === 'string') ? u : (u.username || u);
                if (!seen.has(uname)) {
                    // prefer friend profile for richer display
                    const prof = friends.find(f => (f && f.username) === uname);
                    users.push(prof || { username: uname });
                    seen.add(uname);
                }
            });

            renderList(users, perms);
            if (bsModal) bsModal.show();
        }

        function filterList(q) {
            q = (q || '').toLowerCase();
            Array.from(shareList.querySelectorAll('tr')).forEach(tr => {
                const display = tr.children[0].textContent.toLowerCase();
                tr.style.display = display.indexOf(q) === -1 ? 'none' : '';
            });
        }

        if (shareBtn) shareBtn.addEventListener('click', openShare);
        if (shareSearch) shareSearch.addEventListener('input', (e) => filterList(e.target.value));

        if (shareSave) {
            shareSave.addEventListener('click', async function () {
                const rows = Array.from(shareList.querySelectorAll('tr'));
                const shares = rows.map(tr => {
                    const editorEl = tr.querySelector('.share-editor');
                    const reviewerEl = tr.querySelector('.share-reviewer');
                    const uname = (editorEl && editorEl.dataset && editorEl.dataset.username) || (reviewerEl && reviewerEl.dataset && reviewerEl.dataset.username) || '';
                    const editor = !!(editorEl && editorEl.checked);
                    const reviewer = !!(reviewerEl && reviewerEl.checked);
                    return { username: uname, editor: editor, reviewer: reviewer };
                });

                try {
                    const res = await fetch(`/flashcards/${window.CURRENT_DECK_ID}/share`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ shares })
                    });
                    const body = await res.json();
                    if (body.ok) {
                        if (bsModal) bsModal.hide();
                        // optional: show a brief toast/alert
                        alert('Permissions updated');
                    } else {
                        alert('Failed to update permissions');
                    }
                } catch (e) {
                    alert('Network error');
                }
            });
        }
    });

// Floating chat panel wiring (toggle, close, file-drop)
document.addEventListener('DOMContentLoaded', function () {
    try {
        const openBtn = document.getElementById('floating-chat-button');
        const panel = document.getElementById('floating-chat-panel');
        const closeBtn = document.getElementById('floating-chat-close');
        const fileDrop = document.getElementById('file-drop');
        const fileInput = document.getElementById('file-drop-input');

        function showPanel(show) {
            if (!panel) return;
            try {
                if (show) {
                    panel.classList.add('show');
                    panel.setAttribute('aria-hidden', 'false');
                    panel.style.display = 'flex';
                } else {
                    panel.classList.remove('show');
                    panel.setAttribute('aria-hidden', 'true');
                    panel.style.display = 'none';
                }
            } catch (e) { }
        }

        if (openBtn) openBtn.addEventListener('click', function (e) { e.stopPropagation(); showPanel(true); });
        if (closeBtn) closeBtn.addEventListener('click', function (e) { e.stopPropagation(); showPanel(false); });

        // Click outside chat panel closes it
        document.addEventListener('click', function (ev) {
            if (!panel || !panel.classList.contains('show')) return;
            const tgt = ev.target;
            if (tgt.closest && (tgt.closest('#floating-chat-panel') || tgt.closest('#floating-chat-button'))) return;
            showPanel(false);
        });

        if (fileDrop && fileInput) {
            fileDrop.addEventListener('click', function () { fileInput.click(); });
            fileInput.addEventListener('change', function () {
                if (fileInput.files && fileInput.files.length) fileDrop.style.color = 'green';
            });
            fileDrop.addEventListener('dragover', function (e) { e.preventDefault(); fileDrop.classList.add('dragover'); });
            fileDrop.addEventListener('dragleave', function () { fileDrop.classList.remove('dragover'); });
            fileDrop.addEventListener('drop', function (e) {
                e.preventDefault();
                fileDrop.classList.remove('dragover');
                const files = (e.dataTransfer && e.dataTransfer.files) ? e.dataTransfer.files : null;
                if (files && files.length) {
                    try {
                        // Best-effort: assign files if allowed by browser
                        fileInput.files = files;
                    } catch (err) { }
                    fileDrop.style.color = 'green';
                }
            });
        }
    } catch (e) { /* ignore */ }
});

// Add `has-mobile-footer` to body when a mobile footer is present so responsive CSS can add bottom padding
document.addEventListener('DOMContentLoaded', function () {
    try {
        const mf = document.getElementById('mobile-footer');
        if (!mf) return;
        function updateBodyClass() {
            if (window.innerWidth <= 767) document.body.classList.add('has-mobile-footer');
            else document.body.classList.remove('has-mobile-footer');
        }
        updateBodyClass();
        window.addEventListener('resize', updateBodyClass);
    } catch (e) { /* ignore */ }
});