/**
 * MatchAI - Client-side JavaScript
 * Chatbot, sidebar toggle, and UI interactions
 */

document.addEventListener('DOMContentLoaded', function () {

    // ===== CHATBOT =====
    const chatToggle = document.getElementById('chatToggle');
    const chatWindow = document.getElementById('chatWindow');
    const chatClose = document.getElementById('chatClose');
    const chatMessages = document.getElementById('chatMessages');
    const chatInput = document.getElementById('chatInput');
    const chatSend = document.getElementById('chatSend');

    if (chatToggle && chatWindow) {
        chatToggle.addEventListener('click', () => {
            chatWindow.classList.toggle('open');
            if (chatWindow.classList.contains('open')) {
                chatInput.focus();
            }
        });

        chatClose.addEventListener('click', () => {
            chatWindow.classList.remove('open');
        });

        function addMessage(text, sender) {
            const msg = document.createElement('div');
            msg.className = 'chat-msg ' + sender;
            msg.textContent = text;
            chatMessages.appendChild(msg);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function sendMessage() {
            const text = chatInput.value.trim();
            if (!text) return;

            addMessage(text, 'user');
            chatInput.value = '';

            fetch('/api/chatbot', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            })
                .then(res => res.json())
                .then(data => {
                    addMessage(data.reply, 'bot');
                })
                .catch(() => {
                    addMessage('Sorry, something went wrong. Please try again.', 'bot');
                });
        }

        chatSend.addEventListener('click', sendMessage);
        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    }

    // ===== SIDEBAR TOGGLE (mobile) =====
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        // Create a mobile toggle button
        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'btn btn-primary-custom d-lg-none position-fixed';
        toggleBtn.style.cssText = 'bottom:24px;left:24px;z-index:1050;width:48px;height:48px;border-radius:50%;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 12px rgba(0,0,0,.15)';
        toggleBtn.innerHTML = '<i class="fas fa-bars"></i>';
        toggleBtn.id = 'sidebarToggle';

        // Only add if we're on a dashboard page
        if (document.querySelector('.dashboard-wrapper')) {
            document.body.appendChild(toggleBtn);

            toggleBtn.addEventListener('click', () => {
                sidebar.classList.toggle('open');
            });

            // Close sidebar when clicking outside
            document.addEventListener('click', (e) => {
                if (!sidebar.contains(e.target) && e.target !== toggleBtn && !toggleBtn.contains(e.target)) {
                    sidebar.classList.remove('open');
                }
            });
        }
    }

    // ===== ANIMATIONS ON SCROLL =====
    const animateElements = document.querySelectorAll('.animate-in');
    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });

        animateElements.forEach(el => {
            el.style.opacity = '0';
            observer.observe(el);
        });
    }

    // ===== AUTO-DISMISS ALERTS =====
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, 5000);
    });

    // ===== TOOLTIP INIT =====
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipTriggerList.forEach(el => new bootstrap.Tooltip(el));
});
