document.addEventListener('DOMContentLoaded', () => {
    const body = document.body;

    // ====================================================
    // Dark Mode
    // ====================================================
    const toggleBtn = document.getElementById('theme-toggle');
    if (toggleBtn) {
        if (localStorage.getItem('theme') === 'dark') {
            body.classList.add('dark-mode');
            toggleBtn.innerText = '☀️';
        }
        toggleBtn.addEventListener('click', () => {
            body.classList.toggle('dark-mode');
            if (body.classList.contains('dark-mode')) {
                localStorage.setItem('theme', 'dark');
                toggleBtn.innerText = '☀️';
            } else {
                localStorage.setItem('theme', 'light');
                toggleBtn.innerText = '🌙';
            }
        });
    }

    // ====================================================
    // Compare Logic
    // ====================================================
    const compareForm = document.getElementById('compare-form');
    const compareButton = document.getElementById('compare-floating-btn');
    const overlay = document.getElementById('compare-overlay');
    const compareCheckboxes = document.querySelectorAll('.compare-checkbox');

    if (compareForm && compareButton && compareCheckboxes.length > 0) {
        const MAX_COMPARE = 2;

        const updateState = () => {
            const checked = Array.from(compareCheckboxes).filter(cb => cb.checked);
            const count = checked.length;

            compareButton.textContent = `Compare (${count}/${MAX_COMPARE})`;

            if (count >= MAX_COMPARE) {
                compareCheckboxes.forEach(cb => { if (!cb.checked) cb.disabled = true; });
                compareButton.classList.add('compare-floating-btn--active');
                if (overlay) overlay.classList.add('compare-overlay--visible');
            } else {
                compareCheckboxes.forEach(cb => { cb.disabled = false; });
                compareButton.classList.remove('compare-floating-btn--active');
                if (overlay) overlay.classList.remove('compare-overlay--visible');
            }
        };

        compareCheckboxes.forEach(cb => cb.addEventListener('change', updateState));

        compareButton.addEventListener('click', (e) => {
            const checked = Array.from(compareCheckboxes).filter(cb => cb.checked);
            if (checked.length !== MAX_COMPARE) {
                e.preventDefault();
                alert('Please select exactly 2 cars to compare.');
                return;
            }
            compareForm.submit();
        });

        updateState();
    }

    // ====================================================
    // Chatbot — يفتح/يغلق بالضغط فقط
    // ====================================================
    const chatbotWrapper = document.getElementById('chatbot-wrapper');
    const chatbotBtn = document.getElementById('chatbot-btn');
    const chatbotMessages = document.getElementById('chatbot-messages');
    const chatbotInput = document.getElementById('chatbot-input');
    const chatbotSendBtn = document.getElementById('chatbot-send-btn');
    const chatbotCloseBtn = document.getElementById('chatbot-close');

    if (chatbotWrapper) {
    // فتح وإغلاق بالضغط على الزر
    if (chatbotBtn) {
        chatbotBtn.addEventListener('click', () => {
            chatbotWrapper.classList.toggle('chatbot-open');
            // إظهار رسالة الترحيب مرة واحدة فقط
            if (chatbotWrapper.classList.contains('chatbot-open') && chatbotMessages.childElementCount === 0) {
                appendMessage('Hi! 🤖 I\'m your Car AI Advisor. Ask me anything about cars or your budget ');
            }
        });
    }

    // إغلاق بزر X
    if (chatbotCloseBtn) {
        chatbotCloseBtn.addEventListener('click', () => {
            chatbotWrapper.classList.remove('chatbot-open');
        });
    }

    // إضافة رسالة للشاشة
    var appendMessage = (text, fromUser = false, isLoading = false) => {
        if (!chatbotMessages) return;

        const wrapper = document.createElement('div');
        wrapper.className = 'chatbot-message ' + (fromUser ? 'chatbot-message--user' : 'chatbot-message--bot');
        if (isLoading) wrapper.id = 'chatbot-loading';

        const bubble = document.createElement('div');
        bubble.className = 'chatbot-bubble';

        if (isLoading) {
            bubble.innerHTML = '<span class="chatbot-dots"><span>.</span><span>.</span><span>.</span></span>';
        } else {
            bubble.textContent = text;
        }

        wrapper.appendChild(bubble);
        chatbotMessages.appendChild(wrapper);
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;

        return wrapper;
    };

    // إرسال الرسالة
    const sendMessage = () => {
        const text = chatbotInput.value.trim();
        if (!text) return;

        appendMessage(text, true);
        chatbotInput.value = '';
        chatbotSendBtn.disabled = true;

        // أظهر loading
        appendMessage('', false, true);

        fetch('/chatbot', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text })
        })
            .then(res => res.json())
            .then(data => {
                // احذف loading
                const loading = document.getElementById('chatbot-loading');
                if (loading) loading.remove();

                appendMessage(data.reply || 'Sorry, something went wrong.', false);
            })
            .catch(() => {
                const loading = document.getElementById('chatbot-loading');
                if (loading) loading.remove();
                appendMessage('Sorry, connection error. Please try again.', false);
            })
            .finally(() => {
                chatbotSendBtn.disabled = false;
                chatbotInput.focus();
            });
    };

    if (chatbotSendBtn) chatbotSendBtn.addEventListener('click', sendMessage);
    if (chatbotInput) {
        chatbotInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') { e.preventDefault(); sendMessage(); }
        });
    }
    } // end if (chatbotWrapper)

    // ====================================================
    // Hamburger Menu
    // ====================================================
    const hamburger = document.getElementById('hamburger');
    const nav = document.querySelector('nav');
    const navOverlay = document.getElementById('nav-overlay');

    if (hamburger && nav) {
        hamburger.addEventListener('click', () => {
            hamburger.classList.toggle('open');
            nav.classList.toggle('nav-open');
            if (navOverlay) navOverlay.classList.toggle('active');
        });

        if (navOverlay) {
            navOverlay.addEventListener('click', () => {
                hamburger.classList.remove('open');
                nav.classList.remove('nav-open');
                navOverlay.classList.remove('active');
            });
        }

        // أغلق القائمة لما تضغط على أي رابط
        nav.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                hamburger.classList.remove('open');
                nav.classList.remove('nav-open');
                if (navOverlay) navOverlay.classList.remove('active');
            });
        });
    }

    // ====================================================
    // 3D TILT — car cards follow the mouse for real depth
    // ====================================================
    const tiltCards = document.querySelectorAll('.car-card');
    const isTouch = window.matchMedia('(hover: none)').matches;

    if (!isTouch && tiltCards.length) {
        tiltCards.forEach(card => {
            card.addEventListener('mousemove', (e) => {
                const rect = card.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                const midX = rect.width / 2;
                const midY = rect.height / 2;
                const rotateY = ((x - midX) / midX) * 8;
                const rotateX = -((y - midY) / midY) * 8;
                card.style.transform =
                    `perspective(900px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-6px) scale(1.02)`;
            });

            card.addEventListener('mouseleave', () => {
                card.style.transform =
                    'perspective(900px) rotateX(0deg) rotateY(0deg) translateY(0) scale(1)';
            });
        });
    }

    // ====================================================
    // FAVORITES — toggle without a full page reload
    // ====================================================
    document.querySelectorAll('.wishlist-toggle').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            if (btn.classList.contains('is-loading')) return;

            const carId = btn.dataset.carId;
            const card = btn.closest('.car-card');
            const onWishlistPage = document.body.dataset.page === 'wishlist';

            btn.classList.add('is-loading');
            try {
                const res = await fetch(`/api/toggle_wishlist/${carId}`, {
                    method: 'POST',
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                });
                if (!res.ok) throw new Error('Request failed');
                const data = await res.json();

                if (onWishlistPage && data.status === 'removed' && card) {
                    // على صفحة المفضلة: احذف الكرت بأنيميشن بدل الريفريش
                    card.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                    card.style.opacity = '0';
                    card.style.transform = 'scale(0.92)';
                    setTimeout(() => {
                        card.remove();
                        const grid = document.querySelector('.cars-grid');
                        if (grid && !grid.querySelector('.car-card')) {
                            location.reload(); // بس لو صارت الصفحة فاضية، حدث حالة "empty state"
                        }
                    }, 300);
                } else {
                    btn.classList.toggle('is-active', data.status === 'added');
                }
            } catch (err) {
                console.error('Wishlist toggle failed', err);
            } finally {
                btn.classList.remove('is-loading');
            }
        });
    });
});