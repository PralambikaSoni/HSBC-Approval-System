document.addEventListener("DOMContentLoaded", function() {
    const bellBtn = document.getElementById('notification-bell');
    const badge = document.getElementById('notif-badge');
    const panel = document.getElementById('notifications-panel');
    
    if(!bellBtn) return; // Not logged in

    function fetchNotifications() {
        fetch('/notifications/unread')
            .then(r => r.json())
            .then(data => {
                if (data.length > 0) {
                    badge.textContent = data.length;
                    badge.style.display = 'inline-block';
                } else {
                    badge.style.display = 'none';
                }
                
                // Build panel HTML
                let html = '<div class="notif-header">Notifications <span id="mark-all-read" style="float:right; font-size:12px; cursor:pointer; color:var(--primary); font-weight:normal;">Mark all read</span></div>';
                html += '<div class="notif-body">';
                if (data.length === 0) {
                    html += '<div style="padding:15px; text-align:center; color:#999; font-size:13px;">No new notifications</div>';
                } else {
                    data.forEach(n => {
                        const link = n.link ? n.link : '#';
                        html += `
                            <div class="notif-item" data-id="${n.id}">
                                <a href="${link}" class="notif-link">${n.message}</a>
                                <div style="font-size:10px; color:#999; margin-top:3px;">${new Date(n.created_at).toLocaleString()}</div>
                            </div>
                        `;
                    });
                }
                html += '</div>';
                panel.innerHTML = html;
                
                const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
                // Attach mark all read logic
                const markAll = document.getElementById('mark-all-read');
                if(markAll) {
                    markAll.addEventListener('click', (e) => {
                        e.stopPropagation();
                        fetch('/notifications/mark-read', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': csrfToken
                            },
                            body: JSON.stringify({})
                        }).then(() => fetchNotifications());
                    });
                }
                
                // Attach individual click logic
                document.querySelectorAll('.notif-item').forEach(item => {
                    item.addEventListener('click', (e) => {
                        e.stopPropagation();
                        const id = item.dataset.id;
                        fetch('/notifications/mark-read', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': csrfToken
                            },
                            body: JSON.stringify({notification_id: id})
                        }).then(() => {
                            window.location.href = item.querySelector('.notif-link').href;
                        });
                    });
                });
            });
    }

    // Toggle panel
    bellBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        panel.classList.toggle('hidden');
        if(!panel.classList.contains('hidden')) {
            fetchNotifications();
        }
    });

    // Close when clicking outside
    document.addEventListener('click', (e) => {
        if(!panel.contains(e.target) && !bellBtn.contains(e.target)) {
            panel.classList.add('hidden');
        }
    });

    // Initial fetch and poll every 30s
    fetchNotifications();
    setInterval(fetchNotifications, 30000);
});
