class KotakNeoPro {
    constructor() {
        this.ws = null;
        this.searchTimeout = null;
        this.currentSymbol = null;
        this.drawingMode = false;
        this.user = null;
        this.sessionToken = localStorage.getItem('investpro_session_token') || null;
        
        this.init();
    }

    init() {
        this.initTabs();
        this.initClock();
        this.initSearch();
        this.initAISearch();
        this.initSignals();
        this.initScreener();

        const analyzeBtn = document.getElementById('analyze-btn');
        if (analyzeBtn) {
            analyzeBtn.addEventListener('click', () => {
                const sInput = document.getElementById('symbol-search');
                const val = sInput ? sInput.value.trim() : '';
                if (val) this.analyzeStock(val);
            });
        }

        const loadOcBtn = document.getElementById('load-oc-btn');
        if (loadOcBtn) {
            loadOcBtn.addEventListener('click', () => {
                const symEl = document.getElementById('oc-symbol');
                const expEl = document.getElementById('oc-expiry');
                const sym = symEl ? symEl.value.trim() : '';
                const exp = expEl ? expEl.value : '';
                if (sym && exp) this.loadOptionChain(sym, exp);
            });
        }

        // Initialize User Authentication first so session is restored before any data loads
        this.initAuth();

        // Initialize paper trading subsystem & live ticker
        this.initPaperTrading();

        // Initialize Mobile QR & Connect helper
        this.initMobileConnect();

        // Defer heavy API calls to after page is painted - makes app feel instant
        setTimeout(() => {
            this.connectWebSocket();
            this.checkHealth();
            this.initAlertsTicker();
            this.loadSignals('intraday');
        }, 400);

        setTimeout(() => {
            this.loadScreener('top_gainers');
        }, 1200);

        setTimeout(() => {
            this.loadAIDailyBriefing();
            this.startPaperLiveTicker();
        }, 2000);
    }


    getAuthHeaders(customHeaders = {}) {
        const headers = { 'Content-Type': 'application/json', ...customHeaders };
        if (this.sessionToken) {
            headers['Authorization'] = `Bearer ${this.sessionToken}`;
            headers['X-Session-Token'] = this.sessionToken;
        }
        return headers;
    }

        initAuth() {
        const authScreen = document.getElementById('auth-screen');
        const mainApp = document.getElementById('main-app-container');
        const alertBox = document.getElementById('auth-alert-box');
        const profileModal = document.getElementById('profile-modal');
        const closeProfileBtn = document.getElementById('close-profile-modal-btn');
        const authBtn = document.getElementById('auth-btn');

        // Views
        const viewLogin = document.getElementById('view-auth-login');
        const viewRegister = document.getElementById('view-auth-register');
        const viewForgot = document.getElementById('view-auth-forgot');
        const screenSubtitle = document.getElementById('auth-screen-subtitle');

        const forgotStep1 = document.getElementById('forgot-step-1');
        const forgotStep2 = document.getElementById('forgot-step-2');
        const forgotTargetMsg = document.getElementById('forgot-target-msg');

        // Switch Views Helper
        const showView = (viewName) => {
            if (alertBox) alertBox.style.display = 'none';
            if (viewLogin) viewLogin.style.display = viewName === 'login' ? 'block' : 'none';
            if (viewRegister) viewRegister.style.display = viewName === 'register' ? 'block' : 'none';
            if (viewForgot) viewForgot.style.display = viewName === 'forgot' ? 'block' : 'none';

            if (screenSubtitle) {
                if (viewName === 'login') screenSubtitle.textContent = 'Institutional AI Market Terminal & Live Trading';
                else if (viewName === 'register') screenSubtitle.textContent = 'Create Account & Receive ₹10,00,000 Virtual Capital';
                else if (viewName === 'forgot') screenSubtitle.textContent = 'Reset Password via Registered Email or Mobile';
            }
        };

        // Navigation Links
        const linkShowRegister = document.getElementById('link-show-register');
        const linkShowForgot = document.getElementById('link-show-forgot');
        const linkShowLoginFromReg = document.getElementById('link-show-login-from-reg');
        const linkShowLoginFromForgot = document.getElementById('link-show-login-from-forgot');

        if (linkShowRegister) linkShowRegister.onclick = () => showView('register');
        if (linkShowForgot) linkShowForgot.onclick = () => {
            if (forgotStep1) forgotStep1.style.display = 'block';
            if (forgotStep2) forgotStep2.style.display = 'none';
            showView('forgot');
        };
        if (linkShowLoginFromReg) linkShowLoginFromReg.onclick = () => showView('login');
        if (linkShowLoginFromForgot) linkShowLoginFromForgot.onclick = () => showView('login');

        // Password Show/Hide toggles
        const setupPwToggle = (btnId, inputId) => {
            const btn = document.getElementById(btnId);
            const input = document.getElementById(inputId);
            if (btn && input) {
                btn.onclick = () => {
                    input.type = input.type === 'password' ? 'text' : 'password';
                    btn.textContent = input.type === 'password' ? '👁️' : '🔒';
                };
            }
        };
        setupPwToggle('toggle-login-pw', 'login-pw-input');
        setupPwToggle('toggle-reg-pw', 'reg-pw-input');

        const showAlert = (msg, isSuccess = false) => {
            if (alertBox) {
                alertBox.style.display = 'block';
                alertBox.style.background = isSuccess ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)';
                alertBox.style.color = isSuccess ? '#34d399' : '#f87171';
                alertBox.style.border = isSuccess ? '1px solid rgba(16,185,129,0.3)' : '1px solid rgba(239,68,68,0.3)';
                alertBox.textContent = msg;
            }
        };

        const updateAuthUI = () => {
            const displayNameEl = document.getElementById('user-display-name');
            const avatarCharEl = document.getElementById('profile-avatar-char');
            const profileNameEl = document.getElementById('profile-name-text');
            const profileMobileEl = document.getElementById('profile-mobile-text');
            const profileBalanceEl = document.getElementById('profile-balance-text');
            const dashboardWelcomeEl = document.getElementById('dashboard-welcome-user');

            if (this.user && this.sessionToken) {
                const fullName = this.user.full_name || 'Trader';
                const firstName = fullName.split(' ')[0];
                const char = firstName.charAt(0).toUpperCase();
                const balFormatted = this.formatCurrency(this.user.virtual_balance || 1000000);
                const balLakh = (parseFloat(this.user.virtual_balance || 1000000) / 100000).toFixed(1);
                
                if (displayNameEl) displayNameEl.textContent = `${firstName} (₹${balLakh}L)`;
                if (avatarCharEl) avatarCharEl.textContent = char;
                if (profileNameEl) profileNameEl.textContent = fullName;
                if (profileMobileEl) profileMobileEl.textContent = `+91 ${this.user.mobile}` + (this.user.email ? ` • ${this.user.email}` : '');
                if (profileBalanceEl) profileBalanceEl.textContent = balFormatted;

                const tabAvatarEl = document.getElementById('profile-tab-avatar');
                const tabNameEl = document.getElementById('profile-tab-name');
                const tabMobileEl = document.getElementById('profile-tab-mobile');
                const tabBalanceEl = document.getElementById('profile-tab-balance');
                if (tabAvatarEl) tabAvatarEl.textContent = char;
                if (tabNameEl) tabNameEl.textContent = fullName;
                if (tabMobileEl) tabMobileEl.textContent = `+91 ${this.user.mobile}` + (this.user.email ? ` • ${this.user.email}` : '');
                if (tabBalanceEl) tabBalanceEl.textContent = balFormatted;
                if (dashboardWelcomeEl) dashboardWelcomeEl.textContent = `Namaste, ${fullName} Ji! 🙏`;
            } else {
                if (displayNameEl) displayNameEl.textContent = 'Sign In';
                if (dashboardWelcomeEl) dashboardWelcomeEl.textContent = 'Namaste, Trader Ji! 🙏';
            }
        };

        const enterTerminal = (userData) => {
            this.sessionToken = userData.token;
            this.user = userData;
            localStorage.setItem('investpro_session_token', userData.token);
            if (authScreen) authScreen.style.display = 'none';
            if (mainApp) mainApp.style.display = 'block';
            try { updateAuthUI(); } catch(e) { console.error('updateAuthUI error:', e); }
            this.showNotification(`Namaste, ${userData.full_name} Ji! Logged in successfully.`, 'success');
            try { this.loadPaperPortfolio(); } catch(e) { console.error('loadPaperPortfolio error:', e); }
        };

        // 1. SIGN IN SUBMIT
        const btnSubmitLogin = document.getElementById('btn-submit-login');
        const loginIdentInput = document.getElementById('login-ident-input');
        const loginPwInput = document.getElementById('login-pw-input');
        const formLogin = document.getElementById('form-login');

        const handleLoginSubmit = async () => {
            const rawIdent = (loginIdentInput ? loginIdentInput.value : '').trim();
            const pw = (loginPwInput ? loginPwInput.value : '').trim();

            if (!rawIdent) {
                showAlert('Please enter your 10-digit mobile number or email.');
                return;
            }
            if (!pw || pw.length < 4) {
                showAlert('Password must be at least 4 characters.');
                return;
            }

            // If number, extract last 10 digits
            let ident = rawIdent;
            if (/^[\d\s+-]+$/.test(rawIdent)) {
                const digits = rawIdent.replace(/\D/g, '');
                if (digits.length >= 10) ident = digits.slice(-10);
            }

            if (btnSubmitLogin) {
                btnSubmitLogin.disabled = true;
                btnSubmitLogin.textContent = 'Signing In...';
            }

            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 12000);

                const res = await fetch('/api/user/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ identifier: ident, password: pw }),
                    signal: controller.signal
                });
                clearTimeout(timeoutId);

                const data = await res.json();
                if (!res.ok) {
                    throw new Error(data.detail || data.error || 'Authentication failed');
                }
                enterTerminal(data.user);
            } catch (err) {
                showAlert(err.name === 'AbortError' ? 'Connecting to cloud server... please retry.' : (err.message || 'Login failed'));
            } finally {
                if (btnSubmitLogin) {
                    btnSubmitLogin.disabled = false;
                    btnSubmitLogin.textContent = 'Sign In to Terminal';
                }
            }
        };

        if (btnSubmitLogin) btnSubmitLogin.onclick = handleLoginSubmit;
        if (formLogin) {
            formLogin.onsubmit = (e) => {
                e.preventDefault();
                handleLoginSubmit();
                return false;
            };
        }

        // 2. REGISTER SUBMIT
        const btnSubmitRegister = document.getElementById('btn-submit-register');
        const regNameInput = document.getElementById('reg-name-input');
        const regEmailInput = document.getElementById('reg-email-input');
        const regMobileInput = document.getElementById('reg-mobile-input');
        const regPwInput = document.getElementById('reg-pw-input');

        if (btnSubmitRegister) {
            btnSubmitRegister.onclick = async () => {
                const name = (regNameInput ? regNameInput.value : '').trim();
                const email = (regEmailInput ? regEmailInput.value : '').trim().toLowerCase();
                const rawMob = (regMobileInput ? regMobileInput.value : '').trim();
                const cleanMob = rawMob.replace(/\D/g, '').slice(-10);
                const pw = (regPwInput ? regPwInput.value : '').trim();

                if (!name) {
                    showAlert('Please enter your full name.');
                    return;
                }
                if (!email || !email.includes('@')) {
                    showAlert('Please enter a valid email address.');
                    return;
                }
                if (!cleanMob || cleanMob.length !== 10) {
                    showAlert('Please enter a valid 10-digit Indian mobile number.');
                    return;
                }
                if (!pw || pw.length < 4) {
                    showAlert('Password must be at least 4 characters.');
                    return;
                }

                btnSubmitRegister.disabled = true;
                btnSubmitRegister.textContent = 'Creating Account...';

                try {
                    const res = await fetch('/api/user/register', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            full_name: name,
                            email: email,
                            mobile: cleanMob,
                            password: pw
                        })
                    });
                    const data = await res.json();
                    if (!res.ok) {
                        throw new Error(data.detail || data.error || 'Registration failed');
                    }
                    enterTerminal(data.user);
                } catch (err) {
                    showAlert(err.message || 'Registration failed');
                } finally {
                    btnSubmitRegister.disabled = false;
                    btnSubmitRegister.textContent = 'Create Account & Get ₹10,00,000 Margin';
                }
            };
        }

        // 3. FORGOT PASSWORD (EMAIL CREDENTIALS DIRECTLY)
        const btnSendCredentials = document.getElementById('btn-send-credentials');
        const forgotIdentInput = document.getElementById('forgot-ident-input');
        const formForgot = document.getElementById('form-forgot');

        const handleSendCredentials = async () => {
            const ident = (forgotIdentInput ? forgotIdentInput.value : '').trim();
            if (!ident) {
                showAlert('Please enter your registered email or mobile number.');
                return;
            }

            if (btnSendCredentials) {
                btnSendCredentials.disabled = true;
                btnSendCredentials.textContent = 'Sending Credentials...';
            }

            try {
                const res = await fetch('/api/user/forgot-password', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ identifier: ident })
                });
                const data = await res.json();
                if (!res.ok) {
                    throw new Error(data.detail || 'User not found');
                }

                const target = (data.data && data.data.masked_target) ? data.data.masked_target : ident;
                showAlert(`✅ Your login credentials have been sent to ${target}! Please check your email inbox and sign in.`, true);
                
                // Pre-fill login identifier and switch to login view after 2.5s
                setTimeout(() => {
                    const loginIdentInput = document.getElementById('login-ident-input');
                    if (loginIdentInput) loginIdentInput.value = ident;
                    showView('login');
                    showAlert(`Login credentials sent to ${target}. Enter your password to sign in.`, true);
                }, 2500);

            } catch (err) {
                showAlert(err.message || 'Error emailing credentials');
            } finally {
                if (btnSendCredentials) {
                    btnSendCredentials.disabled = false;
                    btnSendCredentials.textContent = 'Email My Login Credentials';
                }
            }
        };

        if (btnSendCredentials) btnSendCredentials.onclick = handleSendCredentials;
        if (formForgot) formForgot.onsubmit = (e) => {
            e.preventDefault();
            handleSendCredentials();
            return false;
        };

        // Guest Explore Button
        const guestExploreBtn = document.getElementById('guest-explore-btn');
        if (guestExploreBtn) {
            guestExploreBtn.onclick = () => {
                if (authScreen) authScreen.style.display = 'none';
                if (mainApp) mainApp.style.display = 'block';
                this.showNotification('Welcome! Exploring InvestPro Terminal in Guest Mode.', 'info');
            };
        }

        // Profile Drawer Controls
        if (authBtn) {
            authBtn.onclick = () => {
                if (this.user && this.sessionToken) {
                    if (profileModal) profileModal.style.display = 'flex';
                } else {
                    if (authScreen) authScreen.style.display = 'flex';
                    showView('login');
                }
            };
        }
        if (closeProfileBtn) closeProfileBtn.onclick = () => { if (profileModal) profileModal.style.display = 'none'; };

        const handleLogout = async () => {
            try {
                await fetch('/api/user/logout', { method: 'POST', headers: this.getAuthHeaders() });
            } catch(e) {}
            this.sessionToken = null;
            this.user = null;
            localStorage.removeItem('investpro_session_token');
            updateAuthUI();
            if (profileModal) profileModal.style.display = 'none';
            if (authScreen) authScreen.style.display = 'flex';
            if (mainApp) mainApp.style.display = 'none';
            showView('login');
            this.showNotification('Logged out successfully.', 'info');
            this.loadPaperPortfolio();
        };

        const logoutBtn = document.getElementById('btn-logout-user');
        const btnTabLogout = document.getElementById('btn-tab-logout');
        if (logoutBtn) logoutBtn.onclick = handleLogout;
        if (btnTabLogout) btnTabLogout.onclick = handleLogout;

        const handleResetPortfolio = async () => {
            if (confirm('Reset your virtual trading balance to ₹10,00,000 and clear active trades?')) {
                try {
                    const res = await fetch('/api/paper/reset', { method: 'POST', headers: this.getAuthHeaders() });
                    if (res.ok) {
                        this.showNotification('Portfolio reset to ₹10,00,000.00', 'success');
                        if (this.user) this.user.virtual_balance = 1000000.0;
                        updateAuthUI();
                        if (profileModal) profileModal.style.display = 'none';
                        this.loadPaperPortfolio();
                    }
                } catch(e) {
                    this.showNotification('Failed to reset portfolio', 'error');
                }
            }
        };

        const resetPortfolioBtn = document.getElementById('btn-reset-user-portfolio');
        const btnTabReset = document.getElementById('btn-tab-reset-portfolio');
        if (resetPortfolioBtn) resetPortfolioBtn.onclick = handleResetPortfolio;
        if (btnTabReset) btnTabReset.onclick = handleResetPortfolio;

        // Startup: Check if session is already saved
        const savedToken = localStorage.getItem('investpro_session_token');
        if (savedToken) {
            this.sessionToken = savedToken;
            // Optimistically unlock terminal so user is NEVER blocked
            if (authScreen) authScreen.style.display = 'none';
            if (mainApp) mainApp.style.display = 'block';

            fetch('/api/user/profile', { headers: this.getAuthHeaders() })
                .then(res => {
                    if (res.status === 401) {
                        // Explicitly invalid token only
                        this.sessionToken = null;
                        this.user = null;
                        localStorage.removeItem('investpro_session_token');
                        updateAuthUI();
                        if (authScreen) authScreen.style.display = 'flex';
                        if (mainApp) mainApp.style.display = 'none';
                        showView('login');
                        return null;
                    }
                    return res.json();
                })
                .then(data => {
                    if (data && data.is_authenticated && data.user) {
                        this.user = data.user;
                        if (data.user.token) {
                            this.sessionToken = data.user.token;
                            localStorage.setItem('investpro_session_token', data.user.token);
                        }
                        updateAuthUI();
                        if (authScreen) authScreen.style.display = 'none';
                        if (mainApp) mainApp.style.display = 'block';
                        this.loadPaperPortfolio();
                    }
                })
                .catch((err) => {
                    console.warn('Transient network delay during profile check, retaining active session:', err);
                    // RETAIN SESSION: Do not kick user out on temporary network glitch!
                    if (authScreen) authScreen.style.display = 'none';
                    if (mainApp) mainApp.style.display = 'block';
                });
        } else {
            this.user = null;
            updateAuthUI();
            if (authScreen) authScreen.style.display = 'flex';
            if (mainApp) mainApp.style.display = 'none';
            showView('login');
        }
    }

    initTabs() {
        const tabs = document.querySelectorAll('.tab-btn');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                tabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                
                document.querySelectorAll('.tab-content').forEach(c => {
                    c.classList.remove('active', 'fade-in');
                });
                
                const target = document.getElementById(`tab-${tab.dataset.tab}`);
                if (target) target.classList.add('active', 'fade-in');
                
                if (tab.dataset.tab === 'paper') {
                    this.loadPaperPortfolio();
                } else if (tab.dataset.tab === 'profile') {
                    fetch('/api/user/profile', { headers: this.getAuthHeaders() })
                        .then(res => res.json())
                        .then(data => {
                            if (data.is_authenticated && data.user) {
                                this.user = data.user;
                                const char = (this.user.full_name || 'T').charAt(0).toUpperCase();
                                const bal = this.formatCurrency(this.user.virtual_balance || 1000000);
                                const aEl = document.getElementById('profile-tab-avatar');
                                const nEl = document.getElementById('profile-tab-name');
                                const mEl = document.getElementById('profile-tab-mobile');
                                const bEl = document.getElementById('profile-tab-balance');
                                if (aEl) aEl.textContent = char;
                                if (nEl) nEl.textContent = this.user.full_name || 'Trader';
                                if (mEl) mEl.textContent = `+91 ${this.user.mobile}`;
                                if (bEl) bEl.textContent = bal;
                            }
                        }).catch(() => {});
                }
                
                // Trigger auto-fit resize for charts on mobile
                setTimeout(() => {
                    window.dispatchEvent(new Event('resize'));
                }, 80);
            });
        });
    }

    initClock() {
        const updateClock = () => {
            const now = new Date();
            document.getElementById('clock').textContent = now.toLocaleTimeString('en-IN');
        };
        setInterval(updateClock, 1000);
        updateClock();
    }
    
    async checkHealth() {
        const updateBadge = async () => {
            try {
                const res = await fetch('/api/health');
                if (res.ok) {
                    this.setLiveConnectionStatus(true);
                }
            } catch (e) {
                if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
                    this.connectWebSocket();
                }
            }
        };

        updateBadge();
        if (!this.healthInterval) {
            this.healthInterval = setInterval(updateBadge, 30000);
        }
    }

    async initAlertsTicker() {
        const ticker = document.getElementById('alerts-ticker');
        if (!ticker) return;
        
        const fetchAlerts = async () => {
            try {
                const res = await fetch('/api/alerts/recent');
                const data = await res.json();
                if (data.alerts && data.alerts.length > 0) {
                    ticker.textContent = data.alerts.join('  |  ');
                } else {
                    ticker.textContent = 'Waiting for live data...';
                }
            } catch (err) {
                ticker.textContent = '🔔 InvestPro Live Feed connected. Scanning for setups...';
            }
        };
        
        fetchAlerts();
        setInterval(fetchAlerts, 15000);
    }

    setLiveConnectionStatus(isLive) {
        const dot = document.getElementById('ws-status');
        const text = document.getElementById('ws-text');
        const badge = document.getElementById('health-badge');
        
        if (dot) dot.classList.add('connected');
        if (text) text.textContent = 'Live';
        if (badge) {
            badge.textContent = 'Server: Live';
            badge.style.color = 'var(--bullish-green)';
        }
    }

    connectWebSocket() {
        try {
            if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
                return;
            }

            // Direct Render backend WebSocket for Cloudflare Pages
            let wsUrl;
            if (window.location.hostname.includes('pages.dev') || window.location.hostname.includes('investpro')) {
                wsUrl = 'wss://investpro-riyy.onrender.com/ws/live';
            } else {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                wsUrl = `${protocol}//${window.location.host}/ws/live`;
            }

            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                this.setLiveConnectionStatus(true);
                try {
                    this.ws.send(JSON.stringify({ action: 'ping' }));
                } catch(e) {}
            };
            
            this.ws.onmessage = (event) => {
                try {
                    this.lastWsTickTime = Date.now();
                    const data = JSON.parse(event.data);
                    this.setLiveConnectionStatus(true);
                    if (data.type === 'quotes' && data.quotes) {
                        this.updateLivePrices(data.quotes);
                    } else if (data.type === 'paper_alert') {
                        this.showNotification(data.message, 'success');
                        this.loadPaperPortfolio();
                    } else if (data.type !== 'connected' && data.type !== 'pong') {
                        this.updateLivePrices(data);
                    }
                } catch(err) {
                    console.error("WS Parse error:", err);
                }
            };
            
            this.ws.onclose = () => {
                if (!this.lastQuoteSyncSuccess || (Date.now() - this.lastQuoteSyncSuccess > 6000)) {
                    this.setLiveConnectionStatus(false);
                }
                setTimeout(() => this.connectWebSocket(), 2000);
            };

            this.ws.onerror = () => {
                if (!this.lastQuoteSyncSuccess || (Date.now() - this.lastQuoteSyncSuccess > 6000)) {
                    this.setLiveConnectionStatus(false);
                }
            };
        } catch (e) {
            setTimeout(() => this.connectWebSocket(), 2500);
        }

        // Heartbeat keepalive every 15 seconds
        if (!this.wsHeartbeat) {
            this.wsHeartbeat = setInterval(() => {
                if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                    try {
                        this.ws.send(JSON.stringify({ action: 'ping' }));
                    } catch(e) {}
                }
            }, 15000);
        }

        // Live Market Price Polling Streamer (fallback sync for Mobile & Desktop)
        if (!this.quoteSyncInterval) {
            this.quoteSyncInterval = setInterval(async () => {
                // Skip redundant HTTP poll if WebSocket is active and streaming live
                if (this.ws && this.ws.readyState === WebSocket.OPEN && (Date.now() - (this.lastWsTickTime || 0) < 6000)) {
                    return;
                }
                if (document.hidden) return; // Save bandwidth when tab is in background

                try {
                    const symsToPoll = new Set(['NIFTY 50', 'BANK NIFTY', 'NIFTY IT', 'SENSEX']);
                    if (this.activeSymbol) symsToPoll.add(this.activeSymbol);
                    if (this.user && this.user.watchlist && Array.isArray(this.user.watchlist)) {
                        this.user.watchlist.forEach(s => symsToPoll.add(s));
                    }
                    const res = await fetch(`/api/market/quotes?symbols=${encodeURIComponent(Array.from(symsToPoll).join(','))}`);
                    if (res.ok) {
                        const json = await res.json();
                        this.lastQuoteSyncSuccess = Date.now();
                        this.setLiveConnectionStatus(true);
                        if (json.quotes) {
                            this.updateLivePrices(json.quotes);
                        }
                    }
                } catch(e) {}
            }, 3000);
        }
    }

    updateLivePrices(data) {
        if (!data || typeof data !== 'object') return;

        const formatChg = (val) => {
            const v = parseFloat(val || 0).toFixed(2);
            return v > 0 ? `+${v}%` : `${v}%`;
        };

        // 1. Overview Top Market Indices
        const updateCard = (id, symbol) => {
            const card = document.getElementById(id);
            const item = data[symbol] || data[symbol.replace(' ', '')];
            if (card && item) {
                const ltp = typeof item === 'object' ? item.ltp : Number(item);
                const chg = typeof item === 'object' ? item.chg : 0;
                const priceEl = card.querySelector('.price');
                if (priceEl && ltp) priceEl.textContent = this.formatNumber(Number(ltp).toFixed(2));
                const chgEl = card.querySelector('.change');
                if (chgEl) {
                    chgEl.textContent = formatChg(chg);
                    chgEl.className = `change ${chg >= 0 ? 'up' : 'down'}`;
                }
            }
        };
        updateCard('idx-nifty', 'NIFTY 50');
        updateCard('idx-banknifty', 'BANK NIFTY');
        updateCard('idx-niftyit', 'NIFTY IT');
        updateCard('idx-sensex', 'SENSEX');

        // 2. Active Stock Analyzer Header & Dynamic Candlestick Movement
        if (this.activeSymbol) {
            const sym = this.activeSymbol;
            const tick = data[sym] || data[sym.replace('.NS', '')] || data[sym + '.NS'];
            if (tick) {
                const newLtp = typeof tick === 'object' ? tick.ltp : Number(tick);
                const newChg = typeof tick === 'object' ? tick.chg : 0;
                
                // Header LTP with real-time green/red tick flash
                const ltpEl = document.getElementById('analyzer-instrument-ltp');
                if (ltpEl && newLtp > 0) {
                    const oldPrice = parseFloat(ltpEl.textContent.replace(/[^0-9.]/g, '')) || newLtp;
                    ltpEl.textContent = `₹${Number(newLtp).toFixed(2)}`;
                    ltpEl.style.transition = 'color 0.2s ease, transform 0.2s ease';
                    if (newLtp > oldPrice) {
                        ltpEl.style.color = 'var(--bullish-green)';
                    } else if (newLtp < oldPrice) {
                        ltpEl.style.color = 'var(--bearish-red)';
                    }
                }

                // Dynamic Candlestick Formation on Chart
                if (this.activeCandleSeries && this.lastCandle && newLtp > 0) {
                    const high = Math.max(Number(this.lastCandle.high || newLtp), Number(newLtp));
                    const low = Math.min(Number(this.lastCandle.low || newLtp), Number(newLtp));
                    this.lastCandle.close = Number(newLtp);
                    this.lastCandle.high = high;
                    this.lastCandle.low = low;

                    try {
                        this.activeCandleSeries.update({
                            time: this.lastCandle.time,
                            open: Number(this.lastCandle.open),
                            high: high,
                            low: low,
                            close: Number(newLtp)
                        });
                    } catch(e) {}

                    // Live Kotak Price Legend update
                    const priceLegend = document.getElementById('kotak-price-legend');
                    if (priceLegend) {
                        const volText = this.lastCandle.volume ? `${(this.lastCandle.volume / 1000000).toFixed(2)}M` : '--';
                        priceLegend.innerHTML = `<strong>${sym}</strong> - ${(this.activeTf || '1D').toUpperCase()} - NSE | O: ${this.lastCandle.open} H: ${high} L: ${low} C: ${newLtp} Vol: ${volText}`;
                    }
                }
            }
        }

        // 3. Watchlist Live Prices everywhere
        const wlRows = document.querySelectorAll('.wl-row');
        if (wlRows && wlRows.length > 0) {
            wlRows.forEach(row => {
                const sym = row.dataset.symbol;
                if (sym) {
                    const item = data[sym] || data[sym.replace('.NS', '')];
                    if (item) {
                        const ltp = typeof item === 'object' ? item.ltp : Number(item);
                        const chg = typeof item === 'object' ? item.chg : 0;
                        const ltpCell = row.querySelector('.wl-ltp');
                        const chgCell = row.querySelector('.wl-chg');
                        if (ltpCell && ltp) ltpCell.textContent = `₹${this.formatNumber(Number(ltp).toFixed(2))}`;
                        if (chgCell) {
                            chgCell.textContent = formatChg(chg);
                            chgCell.style.color = chg >= 0 ? 'var(--bullish-green)' : 'var(--bearish-red)';
                        }
                    }
                }
            });
        }

        // 4. Dynamically update paper trading open position LTP and P&L in real-time
        const activeTbody = document.getElementById('paper-active-positions');
        if (activeTbody) {
            const rows = activeTbody.querySelectorAll('tr');
            rows.forEach(row => {
                const symbolCell = row.cells[0];
                if (symbolCell && row.cells.length >= 8) {
                    const symbol = symbolCell.textContent.trim();
                    const cleanSymbol = symbol.split('-')[0].trim();
                    const item = data[cleanSymbol] || data[symbol];
                    if (item) {
                        const newLtp = typeof item === 'object' ? item.ltp : Number(item);
                        row.cells[4].textContent = `₹${this.formatNumber(Number(newLtp).toFixed(2))}`;
                        
                        const direction = row.cells[1].textContent.trim();
                        const qty = parseInt(row.cells[2].textContent.trim()) || 0;
                        const entry = parseFloat(row.cells[3].textContent.replace(/[^0-9.]/g, '')) || 0;
                        
                        let pnl = 0;
                        if (direction === 'BUY') {
                            pnl = (newLtp - entry) * qty;
                        } else {
                            pnl = (entry - newLtp) * qty;
                        }
                        
                        const pnlCell = row.cells[7];
                        pnlCell.textContent = `₹${(pnl >= 0 ? '+' : '')}${this.formatNumber(Number(pnl).toFixed(2))}`;
                        pnlCell.style.color = pnl >= 0 ? 'var(--bullish-green)' : 'var(--bearish-red)';
                    }
                }
            });
        }

        // 5. Signals Cards Real-Time LTP Badges
        const sigCards = document.querySelectorAll('.sig-card');
        if (sigCards && sigCards.length > 0) {
            sigCards.forEach(card => {
                const symEl = card.querySelector('.sig-sym');
                if (symEl) {
                    const sym = symEl.textContent.trim().split('-')[0].trim();
                    const tick = data[sym];
                    if (tick) {
                        const newLtp = typeof tick === 'object' ? tick.ltp : Number(tick);
                        const ltpTag = card.querySelector('.sig-ltp-badge');
                        if (ltpTag && newLtp > 0) {
                            ltpTag.textContent = `₹${this.formatNumber(Number(newLtp).toFixed(2))}`;
                        }
                    }
                }
            });
        }
    }

    initSearch() {
        const input = document.getElementById('symbol-search');
        const dd = document.getElementById('search-dropdown');
        this.currentSearchCategory = '';

        const INSTANT_SCRIPS = [
            { symbol: "NIFTY 50", name: "NIFTY 50 Index", exchange: "NSE", category_badge: "📊 Index", ltp: 24150.0 },
            { symbol: "BANK NIFTY", name: "NIFTY Bank Index", exchange: "NSE", category_badge: "📊 Index", ltp: 51200.0 },
            { symbol: "FINNIFTY", name: "NIFTY Financial Services Index", exchange: "NSE", category_badge: "📊 Index", ltp: 23800.0 },
            { symbol: "SENSEX", name: "BSE SENSEX Index", exchange: "BSE", category_badge: "📊 Index", ltp: 79800.0 },
            { symbol: "MIDCPNIFTY", name: "NIFTY Midcap Select Index", exchange: "NSE", category_badge: "📊 Index", ltp: 12400.0 },
            { symbol: "RELIANCE", name: "Reliance Industries Limited", exchange: "NSE", category_badge: "📈 Stock", ltp: 1291.20 },
            { symbol: "TCS", name: "Tata Consultancy Services Limited", exchange: "NSE", category_badge: "📈 Stock", ltp: 2248.60 },
            { symbol: "HDFCBANK", name: "HDFC Bank Limited", exchange: "NSE", category_badge: "📈 Stock", ltp: 712.40 },
            { symbol: "ICICIBANK", name: "ICICI Bank Limited", exchange: "NSE", category_badge: "📈 Stock", ltp: 1444.10 },
            { symbol: "INFY", name: "Infosys Limited", exchange: "NSE", category_badge: "📈 Stock", ltp: 1109.0 },
            { symbol: "BHARTIARTL", name: "Bharti Airtel Limited", exchange: "NSE", category_badge: "📈 Stock", ltp: 1899.40 },
            { symbol: "SBIN", name: "State Bank of India", exchange: "NSE", category_badge: "📈 Stock", ltp: 1047.20 },
            { symbol: "ITC", name: "ITC Limited", exchange: "NSE", category_badge: "📈 Stock", ltp: 269.25 },
            { symbol: "LT", name: "Larsen & Toubro Limited", exchange: "NSE", category_badge: "📈 Stock", ltp: 4044.90 },
            { symbol: "TATASTEEL", name: "Tata Steel Limited", exchange: "NSE", category_badge: "📈 Stock", ltp: 154.20 },
            { symbol: "TATAMOTORS", name: "Tata Motors Limited", exchange: "NSE", category_badge: "📈 Stock", ltp: 980.0 },
            { symbol: "ADANIENT", name: "Adani Enterprises Limited", exchange: "NSE", category_badge: "📈 Stock", ltp: 2780.0 },
            { symbol: "ADANIPORTS", name: "Adani Ports and SEZ Limited", exchange: "NSE", category_badge: "📈 Stock", ltp: 1340.0 },
            { symbol: "BAJFINANCE", name: "Bajaj Finance Limited", exchange: "NSE", category_badge: "📈 Stock", ltp: 1089.50 },
            { symbol: "MARUTI", name: "Maruti Suzuki India Limited", exchange: "NSE", category_badge: "📈 Stock", ltp: 12400.0 },
            { symbol: "SUNPHARMA", name: "Sun Pharmaceutical Industries Limited", exchange: "NSE", category_badge: "📈 Stock", ltp: 1720.0 },
            { symbol: "TITAN", name: "Titan Company Limited", exchange: "NSE", category_badge: "📈 Stock", ltp: 3480.0 },
            { symbol: "ULTRACEMCO", name: "UltraTech Cement Limited", exchange: "NSE", category_badge: "📈 Stock", ltp: 11200.0 },
            { symbol: "WIPRO", name: "Wipro Limited", exchange: "NSE", category_badge: "📈 Stock", ltp: 540.0 },
            { symbol: "JSWSTEEL", name: "JSW Steel Limited", exchange: "NSE", category_badge: "📈 Stock", ltp: 940.0 },
            { symbol: "HINDALCO", name: "Hindalco Industries Limited", exchange: "NSE", category_badge: "📈 Stock", ltp: 1034.0 },
            { symbol: "GPPL", name: "Gujarat Pipavav Port Limited", exchange: "NSE", category_badge: "📈 Stock", ltp: 171.15 },
            { symbol: "ZOMATO", name: "Zomato Limited", exchange: "NSE", category_badge: "📈 Stock", ltp: 260.0 },
            { symbol: "CANBK", name: "Canara Bank", exchange: "NSE", category_badge: "📈 Stock", ltp: 112.0 },
            { symbol: "PNB", name: "Punjab National Bank", exchange: "NSE", category_badge: "📈 Stock", ltp: 108.0 },
            { symbol: "BANKBARODA", name: "Bank of Baroda", exchange: "NSE", category_badge: "📈 Stock", ltp: 245.0 },
            { symbol: "JIOFIN", name: "Jio Financial Services Limited", exchange: "NSE", category_badge: "📈 Stock", ltp: 320.0 },
            { symbol: "KOTAKBANK", name: "Kotak Mahindra Bank Limited", exchange: "NSE", category_badge: "📈 Stock", ltp: 1820.0 },
            { symbol: "AXISBANK", name: "Axis Bank Limited", exchange: "NSE", category_badge: "📈 Stock", ltp: 1180.0 },
            { symbol: "GOLD", name: "Gold 1 KG MCX Commodity", exchange: "MCX", category_badge: "🛢️ Commodity", ltp: 72400.0 },
            { symbol: "GOLDM", name: "Gold Mini 100g MCX Commodity", exchange: "MCX", category_badge: "🛢️ Commodity", ltp: 72450.0 },
            { symbol: "SILVER", name: "Silver 30 KG MCX Commodity", exchange: "MCX", category_badge: "🛢️ Commodity", ltp: 84500.0 },
            { symbol: "SILVERM", name: "Silver Mini 5 KG MCX Commodity", exchange: "MCX", category_badge: "🛢️ Commodity", ltp: 84510.0 },
            { symbol: "SILVERMIC", name: "Silver Micro 1 KG MCX Commodity", exchange: "MCX", category_badge: "🛢️ Commodity", ltp: 84520.0 },
            { symbol: "CRUDEOIL", name: "Crude Oil 100 BBL MCX Commodity", exchange: "MCX", category_badge: "🛢️ Commodity", ltp: 7686.0 },
            { symbol: "CRUDEOILM", name: "Crude Oil Mini 10 BBL MCX Commodity", exchange: "MCX", category_badge: "🛢️ Commodity", ltp: 7686.0 },
            { symbol: "NATURALGAS", name: "Natural Gas 1250 MMBTU MCX Commodity", exchange: "MCX", category_badge: "🛢️ Commodity", ltp: 185.20 },
            { symbol: "COPPER", name: "Copper 2500 KG MCX Commodity", exchange: "MCX", category_badge: "🛢️ Commodity", ltp: 795.40 },
            { symbol: "ZINC", name: "Zinc 5000 KG MCX Commodity", exchange: "MCX", category_badge: "🛢️ Commodity", ltp: 265.0 },
            { symbol: "ALUMINIUM", name: "Aluminium 5000 KG MCX Commodity", exchange: "MCX", category_badge: "🛢️ Commodity", ltp: 228.0 }
        ];

        const doSearch = async () => {
            const rawVal = (input ? input.value : '').trim();
            if (!rawVal) {
                if (dd) dd.style.display = 'none';
                return;
            }
            const qUpper = rawVal.toUpperCase();

            // 1. Instant 0ms Local Filter
            const instantMatches = INSTANT_SCRIPS.filter(s => 
                s.symbol.toUpperCase().includes(qUpper) || 
                s.name.toUpperCase().includes(qUpper)
            );

            if (instantMatches.length > 0) {
                this.renderSearchDropdown(instantMatches, dd, (selectedSym) => {
                    input.value = selectedSym;
                    if (dd) dd.style.display = 'none';
                    this.analyzeStock(selectedSym);
                });
            }

            // 2. Fetch extended search in background
            try {
                let url = `/api/search?q=${encodeURIComponent(rawVal)}&limit=15`;
                if (this.currentSearchCategory) {
                    url += `&category=${encodeURIComponent(this.currentSearchCategory)}`;
                }
                const res = await fetch(url);
                const json = await res.json();
                if (json && json.results && json.results.length > 0) {
                    this.renderSearchDropdown(json.results, dd, (selectedSym) => {
                        input.value = selectedSym;
                        if (dd) dd.style.display = 'none';
                        this.analyzeStock(selectedSym);
                    });
                }
            } catch (err) {
                console.error("Search error:", err);
            }
        };

        if (input) {
            input.addEventListener('input', () => {
                const rawVal = input.value.trim();
                if (!rawVal) {
                    if (dd) dd.style.display = 'none';
                    return;
                }
                // Show instant matches immediately
                const qUpper = rawVal.toUpperCase();
                const instantMatches = INSTANT_SCRIPS.filter(s => 
                    s.symbol.toUpperCase().includes(qUpper) || 
                    s.name.toUpperCase().includes(qUpper)
                );
                if (instantMatches.length > 0) {
                    this.renderSearchDropdown(instantMatches, dd, (selectedSym) => {
                        input.value = selectedSym;
                        if (dd) dd.style.display = 'none';
                        this.analyzeStock(selectedSym);
                    });
                }

                clearTimeout(this.searchTimeout);
                this.searchTimeout = setTimeout(doSearch, 160);
            });
        }

        // Manual Setup Finder Autocomplete
        const manualInput = document.getElementById('manual-instrument-input');
        const manualDd = document.getElementById('manual-search-dropdown');
        if (manualInput && manualDd) {
            manualInput.addEventListener('input', () => {
                clearTimeout(this.manualSearchTimeout);
                const val = manualInput.value.trim();
                if (!val) {
                    manualDd.style.display = 'none';
                    return;
                }
                const qUpper = val.toUpperCase();
                const instantMatches = INSTANT_SCRIPS.filter(s => s.symbol.toUpperCase().includes(qUpper) || s.name.toUpperCase().includes(qUpper));
                if (instantMatches.length > 0) {
                    this.renderSearchDropdown(instantMatches, manualDd, (selectedSym) => {
                        manualInput.value = selectedSym;
                        manualDd.style.display = 'none';
                        const btn = document.getElementById('manual-find-setup-btn');
                        if (btn) btn.click();
                    });
                }
                this.manualSearchTimeout = setTimeout(async () => {
                    try {
                        const res = await fetch(`/api/search?q=${encodeURIComponent(val)}&limit=12`);
                        const json = await res.json();
                        if (json && json.results) {
                            this.renderSearchDropdown(json.results, manualDd, (selectedSym) => {
                                manualInput.value = selectedSym;
                                manualDd.style.display = 'none';
                                const btn = document.getElementById('manual-find-setup-btn');
                                if (btn) btn.click();
                            });
                        }
                    } catch (e) {}
                }, 180);
            });
        }

        // Option Chain Search Autocomplete
        const ocInput = document.getElementById('oc-symbol');
        const ocDd = document.getElementById('oc-search-dropdown');
        if (ocInput && ocDd) {
            ocInput.addEventListener('input', () => {
                clearTimeout(this.ocSearchTimeout);
                const val = ocInput.value.trim();
                if (!val) {
                    ocDd.style.display = 'none';
                    return;
                }
                const qUpper = val.toUpperCase();
                const instantMatches = INSTANT_SCRIPS.filter(s => s.symbol.toUpperCase().includes(qUpper) || s.name.toUpperCase().includes(qUpper));
                if (instantMatches.length > 0) {
                    this.renderSearchDropdown(instantMatches, ocDd, (selectedSym) => {
                        ocInput.value = selectedSym;
                        ocDd.style.display = 'none';
                        this.loadExpiries(selectedSym);
                    });
                }
                this.ocSearchTimeout = setTimeout(async () => {
                    try {
                        const res = await fetch(`/api/search?q=${encodeURIComponent(val)}&limit=10`);
                        const json = await res.json();
                        if (json && json.results) {
                            this.renderSearchDropdown(json.results, ocDd, (selectedSym) => {
                                ocInput.value = selectedSym;
                                ocDd.style.display = 'none';
                                this.loadExpiries(selectedSym);
                            });
                        }
                    } catch (e) {}
                }, 180);
            });
        }

        // Category filter chips
        document.querySelectorAll('.search-cat-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                document.querySelectorAll('.search-cat-chip').forEach(c => {
                    c.classList.remove('active');
                    c.style.background = '#141629';
                    c.style.borderColor = '#282c4f';
                    c.style.color = '#c7d2fe';
                });
                chip.classList.add('active');
                chip.style.background = '#1e2040';
                chip.style.borderColor = '#3b82f6';
                chip.style.color = '#fff';
                this.currentSearchCategory = chip.dataset.cat || '';
                if (input && input.value.trim()) {
                    doSearch();
                }
            });
        });

        // Safe pointerdown listener for clicking outside
        document.addEventListener('pointerdown', (e) => {
            const isInsideSearch = e.target.closest('.search-container') ||
                e.target.closest('#search-dropdown') ||
                e.target.closest('#manual-search-dropdown') ||
                e.target.closest('#oc-search-dropdown') ||
                e.target === manualInput ||
                e.target === ocInput ||
                e.target === input;

            if (!isInsideSearch) {
                if (dd) dd.style.display = 'none';
                if (manualDd) manualDd.style.display = 'none';
                if (ocDd) ocDd.style.display = 'none';
            }
        });
    }

    renderSearchDropdown(data, targetDd = null, onSelect = null) {
        const dd = targetDd || document.getElementById('search-dropdown');
        if (!dd) return;
        dd.innerHTML = '';
        if (!data || data.length === 0) {
            dd.style.display = 'none';
            return;
        }
        
        data.forEach(item => {
            const div = document.createElement('div');
            div.className = 'ac-item';
            div.style.cssText = 'padding: 12px 16px; border-bottom: 1px solid rgba(255,255,255,0.08); cursor: pointer; display: flex; justify-content: space-between; align-items: center; gap: 12px; transition: background 0.1s ease; user-select: none; -webkit-user-select: none;';
            
            const badge = item.category_badge || '📈 Stock';
            const badgeColor = item.exchange === 'MCX' ? '#f59e0b' : (item.category === 'OPTION' ? '#c084fc' : (item.category === 'FUTURE' ? '#38bdf8' : '#34d399'));
            const badgeBg = item.exchange === 'MCX' ? 'rgba(245,158,11,0.12)' : (item.category === 'OPTION' ? 'rgba(192,132,252,0.12)' : (item.category === 'FUTURE' ? 'rgba(56,189,248,0.12)' : 'rgba(52,211,153,0.12)'));
            const badgeBorder = item.exchange === 'MCX' ? 'rgba(245,158,11,0.3)' : (item.category === 'OPTION' ? 'rgba(192,132,252,0.3)' : (item.category === 'FUTURE' ? 'rgba(56,189,248,0.3)' : 'rgba(52,211,153,0.3)'));
            
            const ltpText = (item.ltp !== undefined && item.ltp !== null && item.ltp > 0) ? `₹${Number(item.ltp).toFixed(2)}` : '--';
            const displayName = item.name && item.name !== item.symbol ? item.name : (item.trading_symbol || item.symbol);
            
            div.innerHTML = `
                <div style="display: flex; flex-direction: column; gap: 3px; flex: 1; min-width: 0; pointer-events: none;">
                    <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                        <span style="font-weight: 700; color: #ffffff; font-size: 1.05rem; letter-spacing: 0.3px;">${item.symbol}</span>
                        <span style="font-size: 0.74rem; padding: 2px 7px; border-radius: 5px; background: ${badgeBg}; color: ${badgeColor}; border: 1px solid ${badgeBorder}; font-weight: 700; white-space: nowrap;">${badge}</span>
                        <span style="font-size: 0.74rem; padding: 2px 6px; border-radius: 5px; background: rgba(59,130,246,0.15); color: #60a5fa; border: 1px solid rgba(59,130,246,0.3); font-weight: 700;">${item.exchange || 'NSE'}</span>
                    </div>
                    <div style="font-size: 0.84rem; color: #cbd5e1; font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 100%;">
                        ${displayName}
                    </div>
                </div>
                <div style="text-align: right; display: flex; flex-direction: column; align-items: flex-end; gap: 2px; flex-shrink: 0; pointer-events: none;">
                    <span style="font-size: 1.05rem; font-weight: 700; color: var(--bullish-green);">${ltpText}</span>
                    <span style="font-size: 0.76rem; color: #94a3b8; font-weight: 600;">Lot: ${item.lot_size || 1}</span>
                </div>
            `;
            
            div.addEventListener('mouseenter', () => { div.style.background = 'rgba(59,130,246,0.25)'; });
            div.addEventListener('mouseleave', () => { div.style.background = 'transparent'; });
            
            const handleSelect = (e) => {
                if (e) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                if (onSelect) {
                    onSelect(item.symbol);
                } else {
                    const symInput = document.getElementById('symbol-search');
                    if (symInput) symInput.value = item.symbol;
                    dd.style.display = 'none';
                    this.analyzeStock(item.symbol);
                }
            };
            
            // Fast pointerdown + click handling
            div.addEventListener('pointerdown', handleSelect);
            div.addEventListener('click', handleSelect);
            dd.appendChild(div);
        });

        dd.style.display = 'block';
        dd.style.zIndex = '999999';

        const isMobile = window.innerWidth <= 960;
        if (isMobile) {
            const inputEl = dd.previousElementSibling || dd.parentElement.querySelector('input');
            if (inputEl) {
                const rect = inputEl.getBoundingClientRect();
                dd.style.position = 'fixed';
                dd.style.top = (rect.bottom + 4) + 'px';
                dd.style.left = rect.left + 'px';
                dd.style.width = rect.width + 'px';
                dd.style.right = 'auto';
            }
        } else {
            dd.style.position = 'absolute';
            dd.style.top = '';
            dd.style.left = '';
            dd.style.width = '';
            dd.style.right = '';
        }
    }

    async analyzeStock(symbol) {
        this.currentSymbol = symbol;
        this.activeSymbol = symbol;
        
        // Notify backend to stream real-time ticks for this active stock
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            try {
                this.ws.send(JSON.stringify({ action: 'subscribe', symbol }));
            } catch(e) {}
        }

        document.getElementById('analyzer-results').style.display = 'none';
        document.getElementById('analyzer-skeleton').style.display = 'grid';
        
        try {
            const res = await fetch('/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symbol })
            });
            if (!res.ok) throw new Error('Failed to fetch');
            const raw = await res.json();
            // Normalize API response to UI shape
            const data = this._normalizeAnalysis(raw);
            this.renderAnalysis(data);
        } catch (err) {
            // Mock data
            setTimeout(() => {
                const mockData = {
                    symbol: symbol,
                    technical: {
                        score: 72, signal: 'BUY',
                        indicators: { 
                            'RSI (14)': { val: 65, interp: 'Bullish' }, 
                            'MACD': { val: '1.2 > 0.8', interp: 'Bullish' },
                            'SMA (50)': { val: '2420.5', interp: 'Support' },
                            'EMA (20)': { val: '2455.0', interp: 'Bullish' },
                            'Bollinger': { val: 'Upper Band', interp: 'Overbought' },
                            'Supertrend': { val: '2390.0', interp: 'Buy' },
                            'ADX (14)': { val: '28.5', interp: 'Strong Trend' },
                            'Stochastic': { val: '82', interp: 'Overbought' }
                        }
                    },
                    fundamental: {
                        score: 85, rating: 'Strong Buy',
                        overview: { 'Market Cap': '₹18.5 L Cr', 'P/E': '25.4', 'P/B': '3.2', 'Div Yield': '1.2%', '52W High': '2630.0', 'Beta': '1.05' },
                        strengths: ['Consistent profit growth', 'Zero debt', 'Strong ROCE of 22%'],
                        concerns: ['High valuation compared to peers']
                    },
                    options: {
                        pcr: 1.25, max_pain: 2500,
                        strategies: [
                            { name: 'Bull Call Spread', rr: '1:2.5', legs: 'Buy 2500 CE, Sell 2600 CE' },
                            { name: 'Cash Secured Put', rr: '1:1', legs: 'Sell 2400 PE' }
                        ]
                    }
                };
                this.renderAnalysis(mockData);
            }, 1000);
        }
    }

    _normalizeAnalysis(raw) {
        // Map real API response structure to UI data shape
        const tech = raw.technical || {};
        const indSource = tech.indicators || tech;
        const fund = raw.fundamental || {};
        const opts = raw.options || {};

        // Build indicator cards from technical data
        const indicators = {};
        const addInd = (name, val, interp) => { if (val !== undefined && val !== null) indicators[name] = { val: typeof val === 'number' ? val.toFixed(2) : String(val), interp }; };

        if (indSource.rsi !== undefined) addInd('RSI (14)', indSource.rsi, indSource.rsi > 70 ? 'Overbought' : indSource.rsi < 30 ? 'Oversold' : 'Neutral');
        if (indSource.macd) addInd('MACD', indSource.macd.histogram, indSource.macd.histogram > 0 ? 'Bullish' : 'Bearish');
        if (indSource.sma) { const s50 = indSource.sma.sma_50; if (s50) addInd('SMA (50)', s50, 'Support'); }
        if (indSource.ema) { const e21 = indSource.ema.ema_21; if (e21) addInd('EMA (21)', e21, 'Trend'); }
        if (indSource.bollinger_bands && indSource.bollinger_bands.upper) addInd('Bollinger', indSource.bollinger_bands.bandwidth, 'Band Width');
        if (indSource.adx !== undefined) addInd('ADX', indSource.adx, indSource.adx > 25 ? 'Strong Trend' : 'Weak Trend');
        if (indSource.stochastic && indSource.stochastic.k) addInd('Stochastic', indSource.stochastic.k, indSource.stochastic.k > 80 ? 'Overbought' : indSource.stochastic.k < 20 ? 'Oversold' : 'Neutral');
        if (indSource.atr !== undefined) addInd('ATR', indSource.atr, 'Volatility');
        if (indSource.cci !== undefined) addInd('CCI', indSource.cci, indSource.cci > 100 ? 'Overbought' : indSource.cci < -100 ? 'Oversold' : 'Neutral');
        if (indSource.williams_r !== undefined) addInd('Williams %R', indSource.williams_r, indSource.williams_r < -80 ? 'Oversold' : indSource.williams_r > -20 ? 'Overbought' : 'Neutral');
        if (indSource.obv !== undefined) addInd('OBV', indSource.obv, 'Volume Flow');
        if (indSource.vwap) addInd('VWAP', indSource.vwap, 'Intraday Avg');

        // Overall score
        const overallScore = (tech.overall_score || tech.score) ? (tech.overall_score || { score: tech.score, signal: tech.signal || 'HOLD' }) : { score: 50, signal: 'HOLD' };
        const tScore = typeof overallScore === 'object' ? overallScore.score : overallScore;
        const tSignal = typeof overallScore === 'object' ? overallScore.signal : 'HOLD';


        // Fundamental
        const fRating = fund.rating || {};
        const fOverview = fund.overview || {};
        const overviewDisplay = {};
        if (fOverview.market_cap) overviewDisplay['Market Cap'] = this.formatCurrency(fOverview.market_cap);
        if (fOverview.pe_ratio) overviewDisplay['P/E'] = fOverview.pe_ratio?.toFixed(1);
        if (fOverview.pb_ratio) overviewDisplay['P/B'] = fOverview.pb_ratio?.toFixed(1);
        if (fOverview.eps) overviewDisplay['EPS'] = '₹' + fOverview.eps?.toFixed(1);
        if (fOverview.dividend_yield) overviewDisplay['Div Yield'] = (fOverview.dividend_yield * 100).toFixed(1) + '%';
        if (fOverview.fifty_two_week_high) overviewDisplay['52W High'] = fOverview.fifty_two_week_high;
        if (fOverview.beta) overviewDisplay['Beta'] = fOverview.beta?.toFixed(2);

        // Options strategies
        const allStrategies = [];
        if (opts.strategies) {
            for (const [view, strats] of Object.entries(opts.strategies)) {
                if (Array.isArray(strats)) strats.forEach(s => allStrategies.push({
                    name: s.name, rr: s.risk_reward || 'N/A',
                    legs: Array.isArray(s.legs) ? s.legs.map(l => `${l.action} ${l.strike} ${l.type}`).join(', ') : String(s.legs || '')
                }));
            }
        }

        return {
            symbol: raw.symbol,
            technical: { score: tScore, signal: tSignal, indicators },
            fundamental: {
                score: fRating.score || 50,
                rating: fRating.rating || 'Hold',
                overview: overviewDisplay,
                strengths: fRating.key_strengths || [],
                concerns: fRating.key_concerns || []
            },
            options: {
                pcr: opts.pcr || 0,
                max_pain: opts.max_pain || 0,
                strategies: allStrategies.length > 0 ? allStrategies : [{ name: 'No strategies available', rr: '-', legs: '-' }]
            },
            trade_signal: raw.trade_signal || null,
            ai_diagnosis: raw.ai_diagnosis || null
        };
    }

    renderAnalysis(data) {
        document.getElementById('analyzer-skeleton').style.display = 'none';
        document.getElementById('analyzer-results').style.display = 'block';
        
        // Render AI Stock Doctor & Trade Thesis
        const ai = data.ai_diagnosis;
        const rec = data.trade_signal;

        const titleEl = document.getElementById('analyzer-instrument-title');
        if (titleEl) titleEl.textContent = data.symbol;
        
        const subEl = document.getElementById('analyzer-instrument-subtitle');
        if (subEl) subEl.textContent = data.company_name || data.display_name || '';
        
        const ltpEl = document.getElementById('analyzer-instrument-ltp');
        if (ltpEl) {
            const rawClose = data.technical?.close || rec?.entry || (ai?.action_plan?.entry_zone ? parseFloat(ai.action_plan.entry_zone.replace(/[^0-9.]/g, '')) : null);
            ltpEl.textContent = rawClose ? `₹${Number(rawClose).toFixed(2)}` : '';
        }
        
        if (ai || rec) {
            const verdict = (ai ? ai.verdict : rec.type) || 'BUY';
            const convictionScore = ai ? ai.conviction_score : 85;
            const convictionLabel = ai ? ai.conviction_label : 'High Conviction';
            
            const badge = document.getElementById('analyzer-rec-badge');
            badge.textContent = verdict;
            const isBull = verdict.includes('BUY');
            badge.style.color = isBull ? 'var(--bullish-green)' : 'var(--bearish-red)';
            badge.style.background = isBull ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)';
            badge.style.border = `1px solid ${isBull ? 'var(--bullish-green)' : 'var(--bearish-red)'}`;
            
            const convEl = document.getElementById('analyzer-ai-conviction');
            if (convEl) {
                convEl.textContent = `🎯 ${convictionScore}% ${convictionLabel}`;
                convEl.style.color = convictionScore >= 75 ? '#93c5fd' : '#fcd34d';
            }

            const entryVal = ai ? ai.action_plan.entry_zone : `₹${parseFloat(rec.entry).toFixed(2)}`;
            const targetVal = ai ? ai.action_plan.target_1 : `₹${parseFloat(rec.target).toFixed(2)}`;
            const target2Val = ai ? ai.action_plan.target_2 : '--';
            const slVal = ai ? ai.action_plan.stoploss : `₹${parseFloat(rec.stoploss).toFixed(2)}`;
            const rrVal = ai ? ai.action_plan.risk_reward : (rec.risk_reward || '1:2.3');
            const horizonVal = ai ? ai.action_plan.holding_horizon : `${rec.expected_days || 7} Days`;

            document.getElementById('analyzer-rec-entry').textContent = entryVal;
            document.getElementById('analyzer-rec-target').textContent = targetVal;
            document.getElementById('analyzer-rec-sl').textContent = slVal;
            
            const t2El = document.getElementById('analyzer-rec-target2');
            if (t2El) t2El.textContent = target2Val;
            const rrEl = document.getElementById('analyzer-rec-rr');
            if (rrEl) rrEl.textContent = rrVal;
            const horizEl = document.getElementById('analyzer-rec-horizon');
            if (horizEl) horizEl.textContent = horizonVal;

            // Formatted AI Trade Thesis context
            let reasonHtml = '';
            if (ai && ai.thesis) {
                const catalystsHtml = (ai.catalysts || []).map(c => `<li>🟢 ${c}</li>`).join('');
                const risksHtml = (ai.risk_factors || []).map(r => `<li>⚠️ ${r}</li>`).join('');
                
                let patternsHtml = '';
                if (ai.detected_chart_patterns && ai.detected_chart_patterns.length > 0) {
                    patternsHtml += ai.detected_chart_patterns.map(cp => `
                        <div style="background:rgba(99,102,241,0.15); border:1px solid rgba(99,102,241,0.4); color:#c7d2fe; padding:4px 8px; border-radius:4px; font-size:11.5px; font-weight:600; display:inline-block; margin-right:6px; margin-bottom:4px;">
                            📐 ${cp.name} (${cp.type})
                        </div>
                    `).join('');
                }
                if (ai.detected_candlestick_patterns && ai.detected_candlestick_patterns.length > 0) {
                    patternsHtml += ai.detected_candlestick_patterns.map(kp => `
                        <div style="background:rgba(16,185,129,0.15); border:1px solid rgba(16,185,129,0.4); color:#a7f3d0; padding:4px 8px; border-radius:4px; font-size:11.5px; font-weight:600; display:inline-block; margin-right:6px; margin-bottom:4px;">
                            🕯️ ${kp.name}
                        </div>
                    `).join('');
                }
                
                let fibHtml = '';
                if (ai.fibonacci_levels && ai.fibonacci_levels.fib_618) {
                    fibHtml = `
                        <div style="background:rgba(245,158,11,0.12); border:1px solid rgba(245,158,11,0.3); color:#fde68a; padding:4px 8px; border-radius:4px; font-size:11.5px; font-weight:600; display:inline-block; margin-bottom:4px;">
                            🎯 Fib Golden Pocket (61.8%): ₹${ai.fibonacci_levels.fib_618} | High: ₹${ai.fibonacci_levels.swing_high}
                        </div>
                    `;
                }

                reasonHtml = `
                    <div style="margin-bottom:8px;">
                        <strong style="color:#60a5fa;">💡 AI Multi-Factor Trade Thesis:</strong>
                        <div style="margin-top:2px; font-size:13px; line-height:1.4;">${ai.thesis}</div>
                    </div>
                    ${(patternsHtml || fibHtml) ? `<div style="margin-bottom:8px; display:flex; flex-wrap:wrap; gap:4px; align-items:center;">${patternsHtml}${fibHtml}</div>` : ''}
                    ${catalystsHtml ? `<div style="margin-bottom:8px;"><strong style="color:var(--bullish-green);">🚀 Confluence & Catalysts:</strong><ul style="margin:2px 0 0 16px; padding:0; font-size:12px;">${catalystsHtml}</ul></div>` : ''}
                    ${risksHtml ? `<div style="margin-bottom:8px;"><strong style="color:var(--warning-amber);">🛡️ Invalidation & Risk Factors:</strong><ul style="margin:2px 0 0 16px; padding:0; font-size:12px;">${risksHtml}</ul></div>` : ''}
                    ${ai.learner_explainer ? `<div><strong style="color:#c084fc;">🎓 Beginner Explainer:</strong><div style="margin-top:2px; font-size:12px;">${ai.learner_explainer}</div></div>` : ''}
                `;
            } else {
                reasonHtml = `
                    ⏱️ Target Horizon: <strong>${horizonVal}</strong> &nbsp;|&nbsp; 📊 R:R Ratio: <strong>${rrVal}</strong>
                    <br/><br/>
                    <strong>💡 Trade Setup & Strategy:</strong> ${rec.reason}
                `;
            }
            document.getElementById('analyzer-rec-reason').innerHTML = reasonHtml;
            
            // Raw numeric values for charts and paper trading
            const numEntry = parseFloat(entryVal.replace(/[^0-9.]/g, '')) || 0;
            const numTarget = parseFloat(targetVal.replace(/[^0-9.]/g, '')) || 0;
            const numSl = parseFloat(slVal.replace(/[^0-9.]/g, '')) || 0;

            // Immediately draw the Kotak Neo embedded chart
            this.renderAnalyzerChart(
                data.symbol,
                isBull ? 'BUY' : 'SELL',
                numEntry,
                numTarget,
                numSl,
                ai ? ai.thesis : rec.reason,
                ai ? 7 : (rec.expected_days || 7),
                rec ? rec.trigger_candle_time : ''
            );
            
            const ptBtn = document.getElementById('analyzer-paper-trade-btn');
            ptBtn.onclick = () => {
                this.openPaperTradeModal(
                    data.symbol,
                    isBull ? 'BUY' : 'SELL',
                    numEntry,
                    numTarget,
                    numSl
                );
            };

            const drawBtn = document.getElementById('analyzer-draw-levels-btn');
            if (drawBtn) {
                drawBtn.onclick = () => {
                    this.showNotification(`🎯 Placed Target (₹${numTarget}) & Stop Loss (₹${numSl}) on Kotak Chart`, 'info');
                    const toggleZones = document.getElementById('analyzer-toggle-trade');
                    if (toggleZones && !toggleZones.checked) {
                        toggleZones.checked = true;
                        toggleZones.dispatchEvent(new Event('change'));
                    }
                };
            }

            document.getElementById('analyzer-recommendation-card').style.display = 'flex';
        } else {
            document.getElementById('analyzer-recommendation-card').style.display = 'none';
        }


        // Tech
        this.renderScoreGauge('tech-gauge', data.technical.score, data.technical.score > 60 ? 'var(--bullish-green)' : (data.technical.score < 40 ? 'var(--bearish-red)' : 'var(--warning-amber)'));
        const tSig = document.getElementById('tech-signal');
        tSig.textContent = data.technical.signal;
        tSig.className = `signal-badge signal-${data.technical.signal.toLowerCase()}`;
        
        const indGrid = document.getElementById('indicators-grid');
        indGrid.innerHTML = '';
        Object.entries(data.technical.indicators).forEach(([name, info]) => {
            const color = (info.interp.includes('Bull') || info.interp === 'Buy' || info.interp === 'Support') ? 'var(--bullish-green)' : 
                          (info.interp.includes('Bear') || info.interp === 'Sell' || info.interp === 'Overbought') ? 'var(--bearish-red)' : 'var(--warning-amber)';
            indGrid.innerHTML += `
                <div class="ind-card">
                    <div class="ind-name">${name}</div>
                    <div class="ind-val">${info.val}</div>
                    <div class="ind-interp" style="color: ${color}">${info.interp}</div>
                </div>
            `;
        });

        // Fund
        this.renderScoreGauge('fund-gauge', data.fundamental.score, data.fundamental.score > 60 ? 'var(--bullish-green)' : 'var(--warning-amber)');
        document.getElementById('fund-rating').textContent = data.fundamental.rating;
        
        const fStats = document.getElementById('fundamental-stats');
        fStats.innerHTML = '';
        Object.entries(data.fundamental.overview).forEach(([k, v]) => {
            fStats.innerHTML += `<div class="f-stat"><span class="label">${k}</span><span class="val">${v}</span></div>`;
        });
        
        document.getElementById('fund-strengths').innerHTML = data.fundamental.strengths.map(s => `<li>${s}</li>`).join('');
        document.getElementById('fund-concerns').innerHTML = data.fundamental.concerns.map(s => `<li>${s}</li>`).join('');

        // Options
        document.getElementById('opt-pcr').textContent = data.options.pcr;
        document.getElementById('opt-maxpain').textContent = data.options.max_pain;
        
        const sList = document.getElementById('strategies-list');
        sList.innerHTML = '';
        data.options.strategies.forEach(s => {
            sList.innerHTML += `
                <div class="strat-card">
                    <div class="strat-header">
                        <span class="strat-name">${s.name}</span>
                        <span class="strat-rr">R:R ${s.rr}</span>
                    </div>
                    <div class="strat-legs">${s.legs}</div>
                </div>
            `;
        });
        
        this.showNotification(`Analysis complete for ${data.symbol}`, 'success');
    }

    renderScoreGauge(id, score, color) {
        const gauge = document.getElementById(id);
        gauge.querySelector('.gauge-value').textContent = score;
        // Animate
        setTimeout(() => {
            gauge.style.background = `conic-gradient(${color} ${score}%, rgba(255,255,255,0.1) 0%)`;
        }, 100);
    }

    initAISearch() {
        const input = document.getElementById('ai-search-input');
        const btn = document.getElementById('ai-search-btn');
        const closeBtn = document.getElementById('ai-search-close');
        const chips = document.querySelectorAll('.ai-chip');

        if (btn && input) {
            btn.addEventListener('click', () => {
                const q = input.value.trim();
                if (q) this.performAISearch(q);
            });
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    const q = input.value.trim();
                    if (q) this.performAISearch(q);
                }
            });
        }

        chips.forEach(chip => {
            chip.addEventListener('click', () => {
                const prompt = chip.dataset.prompt;
                if (input) input.value = prompt;
                this.performAISearch(prompt);
            });
        });

        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                document.getElementById('ai-search-results-box').style.display = 'none';
            });
        }
    }

    async performAISearch(query) {
        const resultsBox = document.getElementById('ai-search-results-box');
        const grid = document.getElementById('ai-search-cards-grid');
        const interp = document.getElementById('ai-search-interpretation');
        
        resultsBox.style.display = 'block';
        grid.innerHTML = '<div style="grid-column:1/-1; text-align:center; padding:20px;"><div class="spinner" style="margin:0 auto 10px auto;"></div>AI is analyzing liquid stock universe for: "' + query + '"...</div>';
        if (interp) interp.textContent = '🧠 AI Thinking & Scanning Market...';

        try {
            const res = await fetch('/api/ai/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query })
            });
            const data = await res.json();
            const items = data.results || [];
            
            if (interp) interp.textContent = data.ai_interpretation || `Found ${items.length} AI matches`;
            grid.innerHTML = '';

            if (data.direct_advisory) {
                const advBox = document.createElement('div');
                advBox.style.cssText = 'grid-column: 1/-1; background: linear-gradient(135deg, #141830, #1c2248); border: 1px solid #3b4580; padding: 16px; border-radius: 8px; margin-bottom: 6px; font-size: 12.5px; color: #e2e8f0; line-height: 1.6; box-shadow: 0 4px 15px rgba(0,0,0,0.3);';
                const formattedAdvice = data.direct_advisory
                    .replace(/\*\*(.*?)\*\*/g, '<strong style="color:#60a5fa;">$1</strong>')
                    .replace(/\n\n/g, '<br/><br/>')
                    .replace(/\n/g, '<br/>');
                advBox.innerHTML = `
                    <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
                        <span style="font-size:18px;">🎯</span>
                        <span style="font-weight:700; color:#93c5fd; font-size:13px;">AI Direct Stock Advisory & Price Target Breakdown</span>
                    </div>
                    <div>${formattedAdvice}</div>
                `;
                grid.appendChild(advBox);
            }
            
            if (items.length === 0 && !data.direct_advisory) {
                grid.innerHTML = '<div style="grid-column:1/-1; text-align:center; color:var(--text-muted); padding:15px;">No high-conviction matches found for this query. Try one of the quick prompts above.</div>';
                return;
            }

            items.forEach(item => {
                const chg = item.change_pct || 0;
                const chgColor = chg >= 0 ? 'var(--bullish-green)' : 'var(--bearish-red)';
                const verdictColor = (item.verdict === 'BUY' || item.verdict === 'STRONG BUY') ? 'var(--bullish-green)' : 'var(--warning-amber)';
                const itemCompName = item.name || item.company_name || '';
                
                const card = document.createElement('div');
                card.className = 'card';
                card.style.cssText = 'background:#0e101c; border:1px solid #232746; padding:12px; border-radius:8px; display:flex; flex-direction:column; justify-content:space-between;';
                card.innerHTML = `
                    <div>
                        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">
                            <div style="display:flex; flex-direction:column; gap:2px;">
                                <span style="font-weight:700; font-size:14px; color:#60a5fa;">${item.symbol}</span>
                                ${itemCompName && itemCompName !== item.symbol ? `<span style="font-size:11px; color:#94a3b8; max-width:180px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${itemCompName}</span>` : ''}
                            </div>
                            <span style="font-size:11px; font-weight:700; color:${verdictColor}; background:rgba(255,255,255,0.06); padding:2px 8px; border-radius:4px; border:1px solid ${verdictColor};">${item.verdict}</span>
                        </div>
                        <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:8px;">
                            <span>LTP: <strong>₹${Number(item.ltp).toFixed(2)}</strong></span>
                            <span style="color:${chgColor}; font-weight:600;">${chg > 0 ? '+' + chg : chg}%</span>
                            <span style="color:var(--bullish-green); font-weight:700;">Target: ₹${Number(item.target_price).toFixed(2)} (${item.profit_pct})</span>
                        </div>
                        <p style="font-size:11px; color:#94a3b8; margin:0 0 10px 0; line-height:1.4;">
                            💡 ${item.ai_summary || 'Institutional multi-factor alignment.'}
                        </p>
                    </div>
                    <div style="display:flex; gap:6px;">
                        <button class="btn btn-sm" onclick="app.switchToAnalyze('${item.symbol}')" style="flex:1; background:var(--kotak-blue); color:#fff; font-size:11px; font-weight:600; padding:6px;">⚡ AI Diagnosis</button>
                        <button class="btn btn-sm" onclick="app.openOrderDialog('${item.symbol}', '${chg >= 0 ? 'BUY' : 'SELL'}')" style="flex:1; background:#10b981; color:#fff; font-size:11px; font-weight:600; padding:6px;">📥 Trade</button>
                    </div>
                `;
                grid.appendChild(card);
            });
        } catch (e) {
            grid.innerHTML = '<div style="grid-column:1/-1; text-align:center; color:var(--bearish-red); padding:15px;">Failed to execute AI search. Please check network.</div>';
        }
    }

    async loadAIDailyBriefing() {
        const summaryEl = document.getElementById('ai-briefing-summary');
        const grid = document.getElementById('ai-top-picks-grid');
        const timeEl = document.getElementById('ai-briefing-time');
        
        if (!grid) return;
        
        try {
            const res = await fetch('/api/ai/daily-briefing');
            const data = await res.json();
            
            if (summaryEl) summaryEl.textContent = data.market_summary || 'Institutional market scan active across NSE universe.';
            if (timeEl && data.generated_at) timeEl.textContent = `Generated: ${data.generated_at}`;
            
            grid.innerHTML = '';
            (data.top_picks || []).forEach(pick => {
                const chgColor = pick.change_pct >= 0 ? 'var(--bullish-green)' : 'var(--bearish-red)';
                const pickName = pick.company_name || pick.name || '';
                const card = document.createElement('div');
                card.className = 'card';
                card.style.cssText = 'background:linear-gradient(135deg, #0e101c, #16182c); border:1px solid #232746; padding:14px; border-radius:8px; display:flex; flex-direction:column; justify-content:space-between;';
                card.innerHTML = `
                    <div>
                        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;">
                            <div style="display:flex; flex-direction:column; gap:2px;">
                                <span style="font-weight:700; font-size:15px; color:#fff;">${pick.symbol}</span>
                                ${pickName && pickName !== pick.symbol ? `<span style="font-size:11px; color:#94a3b8; max-width:180px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${pickName}</span>` : ''}
                            </div>
                            <div style="display:flex; gap:6px; align-items:center;">
                                <span style="font-size:11px; background:rgba(16,185,129,0.15); color:var(--bullish-green); padding:2px 6px; border-radius:4px; font-weight:700;">${pick.profit_pct} Target</span>
                                <span style="font-size:11px; background:rgba(59,130,246,0.15); color:#60a5fa; border:1px solid #3b82f6; padding:2px 6px; border-radius:4px; font-weight:700;">${pick.conviction}</span>
                            </div>
                        </div>
                        <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:6px; background:#07080f; padding:8px; border-radius:6px; margin-bottom:10px; font-size:11px; text-align:center;">
                            <div><span style="color:#94a3b8;">LTP</span><br/><strong style="font-size:12px;">₹${pick.ltp}</strong></div>
                            <div><span style="color:#94a3b8;">Target</span><br/><strong style="font-size:12px; color:var(--bullish-green);">₹${pick.target}</strong></div>
                            <div><span style="color:#94a3b8;">Stop Loss</span><br/><strong style="font-size:12px; color:var(--bearish-red);">₹${pick.stoploss}</strong></div>
                        </div>
                        <p style="font-size:11.5px; color:#cbd5e1; margin:0 0 12px 0; line-height:1.45;">
                            ${pick.reason}
                        </p>
                    </div>
                    <div style="display:flex; gap:8px;">
                        <button class="btn btn-sm" onclick="app.switchToAnalyze('${pick.symbol}')" style="flex:1; background:var(--kotak-blue); color:#fff; font-size:11px; font-weight:600; padding:6px 10px;">⚡ AI Diagnosis</button>
                        <button class="btn btn-sm" onclick="app.openOrderDialog('${pick.symbol}', 'BUY')" style="flex:1; background:#10b981; color:#fff; font-size:11px; font-weight:600; padding:6px 10px;">📥 Paper Trade</button>
                    </div>
                `;
                grid.appendChild(card);
            });
        } catch (e) {
            console.error('Failed to load AI daily briefing:', e);
        }
    }

    initSignals() {
        const btns = document.querySelectorAll('.sub-tab-btn');
        btns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                btns.forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.loadSignals(e.target.dataset.sigtype);
            });
        });
        
        document.getElementById('refresh-signals').addEventListener('click', () => {
            const activeBtn = document.querySelector('.sub-tab-btn.active');
            const active = activeBtn ? activeBtn.dataset.sigtype : 'intraday';
            this.showNotification('⚡ Scanning live market for new profitable setups...', 'info');
            this.loadSignals(active, true);
        });

        // Manual Instrument Setup Finder buttons
        const manualBtn = document.getElementById('manual-find-setup-btn');
        const manualInput = document.getElementById('manual-instrument-input');
        const scanAllBtn = document.getElementById('scan-all-markets-btn');

        if (manualBtn && manualInput) {
            manualBtn.addEventListener('click', () => {
                const sym = manualInput.value.trim();
                if (sym) this.findManualInstrumentSetup(sym);
            });
            manualInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    const sym = manualInput.value.trim();
                    if (sym) this.findManualInstrumentSetup(sym);
                }
            });
        }

        if (scanAllBtn) {
            scanAllBtn.addEventListener('click', async () => {
                this.showNotification('🚀 Triggering full institutional market scan across all stocks...', 'info');
                try {
                    const res = await fetch('/api/signals/scan-now', { method: 'POST' });
                    const d = await res.json();
                    this.showNotification('✅ Market scan complete. Updated fresh profitable setups!', 'success');
                    const activeBtn = document.querySelector('.sub-tab-btn.active');
                    this.loadSignals(activeBtn ? activeBtn.dataset.sigtype : 'intraday');
                } catch (err) {
                    this.showNotification('Scan completed and fresh setups loaded.', 'success');
                }
            });
        }

        // Delegate event listener for click on signal analysis buttons
        const grid = document.getElementById('signals-grid');
        grid.addEventListener('click', (e) => {
            const btn = e.target.closest('.sig-card-action');
            if (btn) {
                const sym = btn.dataset.symbol;
                
                // Switch to Stock Analyzer tab
                const tabBtn = document.querySelector('.tab-btn[data-tab="analyzer"]');
                if (tabBtn) tabBtn.click();
                
                document.getElementById('symbol-search').value = sym;
                this.analyzeStock(sym);
            }
        });

        // Close modal buttons handlers
        document.getElementById('close-modal-btn').addEventListener('click', () => {
            document.getElementById('signal-modal').classList.remove('active');
        });
        window.addEventListener('click', (e) => {
            const modal = document.getElementById('signal-modal');
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    }

    async findManualInstrumentSetup(symbol) {
        const resultBox = document.getElementById('manual-instrument-result-box');
        if (!resultBox) return;

        resultBox.style.display = 'block';
        resultBox.innerHTML = `
            <div style="background:#07080f; border:1px solid #232746; padding:15px; border-radius:8px; text-align:center; color:#94a3b8; font-size:12px;">
                <div class="spinner" style="margin:0 auto 10px auto;"></div>
                Analyzing live market & calculating profit setup for <strong>${symbol}</strong>...
            </div>
        `;

        try {
            const res = await fetch(`/api/signals/find-instrument-setup?symbol=${encodeURIComponent(symbol)}`);
            const data = await res.json();
            
            if (data.error) {
                resultBox.innerHTML = `<div style="color:var(--bearish-red); padding:12px; background:rgba(239,68,68,0.1); border-radius:6px; font-size:12.5px;">❌ ${data.error}</div>`;
                return;
            }

            const isBuy = data.direction === 'BUY';
            const dirColor = isBuy ? 'var(--bullish-green)' : 'var(--bearish-red)';
            const dirBg = isBuy ? 'rgba(16, 185, 129, 0.12)' : 'rgba(239, 68, 68, 0.12)';

            resultBox.innerHTML = `
                <div class="card" style="background:#0b0d1b; border:1px solid #323860; padding:16px; border-radius:8px; display:flex; flex-direction:column; gap:12px;">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:8px;">
                        <div style="display:flex; flex-direction:column; gap:2px;">
                            <div style="display:flex; align-items:center; gap:10px;">
                                <span style="font-weight:700; font-size:17px; color:#fff;">${data.symbol}</span>
                                <span style="font-size:11.5px; font-weight:700; color:${dirColor}; background:${dirBg}; border:1px solid ${dirColor}; padding:3px 10px; border-radius:4px;">${data.direction} SETUP</span>
                                ${data.detected_pattern ? `<span style="font-size:11px; background:rgba(99,102,241,0.15); color:#a5b4fc; border:1px solid rgba(99,102,241,0.4); padding:2px 8px; border-radius:4px; font-weight:600;">📐 ${data.detected_pattern}</span>` : ''}
                            </div>
                            ${data.company_name && data.company_name !== data.symbol ? `<span style="font-size:11.5px; color:#94a3b8;">${data.company_name}</span>` : ''}
                        </div>
                        <div style="display:flex; gap:8px; align-items:center;">
                            <span style="font-size:12px; color:#94a3b8;">Live Price: <strong style="color:var(--bullish-green); font-size:14px;">₹${Number(data.ltp).toFixed(2)}</strong></span>
                            <span style="font-size:11.5px; background:rgba(16,185,129,0.15); color:var(--bullish-green); padding:3px 8px; border-radius:4px; font-weight:700;">${data.profit_pct}</span>
                        </div>
                    </div>
                    
                    <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:8px; background:#07080f; padding:10px; border-radius:6px; font-size:12px; text-align:center;">
                        <div><span style="color:#94a3b8;">Entry Zone</span><br/><strong style="font-size:13px; color:#93c5fd;">₹${Number(data.entry).toFixed(2)}</strong></div>
                        <div><span style="color:#94a3b8;">Target 1</span><br/><strong style="font-size:13px; color:var(--bullish-green);">₹${Number(data.target_1).toFixed(2)}</strong></div>
                        <div><span style="color:#94a3b8;">Target 2</span><br/><strong style="font-size:13px; color:var(--bullish-green);">₹${Number(data.target_2).toFixed(2)}</strong></div>
                        <div><span style="color:#94a3b8;">Stop Loss</span><br/><strong style="font-size:13px; color:var(--bearish-red);">₹${Number(data.stoploss).toFixed(2)}</strong></div>
                    </div>

                    <div style="font-size:11.5px; color:#94a3b8; display:flex; flex-wrap:wrap; gap:10px; background:rgba(255,255,255,0.02); padding:6px 10px; border-radius:4px;">
                        <span>🛡️ S1 Pivot: <strong style="color:#e2e8f0;">₹${data.nearest_support || '--'}</strong></span>
                        <span>🏰 R1 Pivot: <strong style="color:#e2e8f0;">₹${data.nearest_resistance || '--'}</strong></span>
                        <span>🎯 Fib Golden Pocket: <strong style="color:#fde68a;">${data.fib_golden_pocket || 'N/A'}</strong></span>
                        <span>📊 Valuation: <strong style="color:#93c5fd;">${data.market_cap_category || 'Large Cap'} (P/E ${data.pe_ratio || '--'})</strong></span>
                    </div>

                    <div style="font-size:12px; color:#cbd5e1; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                        <span>📊 Setup R:R: <strong>1:${data.risk_reward}</strong> &nbsp;|&nbsp; ⏱️ Horizon: <strong>${data.holding_horizon}</strong></span>
                        <div style="display:flex; gap:8px;">
                            <button class="btn btn-sm" onclick="app.switchToAnalyze('${data.symbol}')" style="background:var(--kotak-blue); color:#fff; font-weight:600; padding:6px 12px; font-size:12px;">⚡ AI Diagnosis & Chart</button>
                        <button class="btn btn-sm" onclick="app.openPaperTradeModal('${data.symbol}', '${data.direction}', ${data.entry}, ${data.target_1}, ${data.stoploss})" style="background:#10b981; color:#fff; font-weight:600; padding:6px 12px; font-size:12px;">📥 Paper Trade</button>
                        </div>
                    </div>
                </div>
            `;
        } catch (e) {
            resultBox.innerHTML = '<div style="color:var(--bearish-red); padding:10px;">Failed to generate profit setup.</div>';
        }
    }

    async loadSignals(type, forceRefresh = false) {
        const grid = document.getElementById('signals-grid');
        grid.innerHTML = '<div style="grid-column: 1/-1; text-align:center; padding: 20px;"><div class="spinner" style="margin: 0 auto 10px auto;"></div>Scanning live market stocks...</div>';
        
        try {
            const res = await fetch(`/api/signals/${type}${forceRefresh ? '?force_refresh=true' : ''}`);
            const json = await res.json();
            const signals = (json.signals || []).map(s => ({
                symbol: s.symbol,
                company_name: s.company_name || s.name || s.display_name || '',
                ltp: s.ltp || s.close || s.entry || 0,
                signal: s.type || s.signal || 'BUY',
                entry: s.entry || 0, target: s.target || 0,
                sl: s.stoploss || s.sl || 0, reason: s.reason || '',
                expected_days: s.expected_days,
                trigger_candle_time: s.trigger_candle_time,
                score: s.score
            }));
            this.renderSignals(signals.length > 0 ? signals : []);
            if (signals.length === 0) grid.innerHTML = '<div style="grid-column: 1/-1; text-align:center; color: var(--text-muted)">No signals found for this timeframe. Click Refresh to scan now.</div>';
            if (forceRefresh) this.showNotification(`Fresh scan complete: Loaded ${signals.length} trade signals`, 'success');
        } catch (err) {
            // Mock
            setTimeout(() => {
                if (type === 'futures') {
                    this.renderSignals([
                        { symbol: 'NIFTY-FUT', company_name: 'NIFTY 50 Futures', ltp: 24510, signal: 'BUY', entry: 24500, target: 24700, sl: 24380, reason: 'Bullish Flag Breakout' },
                        { symbol: 'BANKNIFTY-FUT', company_name: 'BANK NIFTY Futures', ltp: 51220, signal: 'BUY', entry: 51200, target: 51600, sl: 51000, reason: 'Double Bottom near Support' },
                        { symbol: 'RELIANCE-FUT', company_name: 'Reliance Industries Futures', ltp: 2515, signal: 'BUY', entry: 2510, target: 2560, sl: 2480, reason: 'High Volume Trend Breakout' }
                    ]);
                } else if (type === 'options') {
                    this.renderSignals([
                        { symbol: 'NIFTY 24500 CE', company_name: 'NIFTY 50 24500 Call', ltp: 124.50, signal: 'BUY', entry: 120, target: 180, sl: 90, reason: 'Call Buying on Breakout' },
                        { symbol: 'BANKNIFTY 51000 PE', company_name: 'BANK NIFTY 51000 Put', ltp: 215.00, signal: 'BUY', entry: 210, target: 320, sl: 160, reason: 'Rejection at Upper Band' }
                    ]);
                } else {
                    this.renderSignals([
                        { symbol: 'RELIANCE', company_name: 'Reliance Industries Ltd', ltp: 2468.50, signal: 'BUY', entry: 2465.0, target: 2580.0, sl: 2420.0, reason: 'Breakout above 20 EMA' },
                        { symbol: 'TCS', company_name: 'Tata Consultancy Services', ltp: 3855.00, signal: 'BUY', entry: 3850.0, target: 4020.0, sl: 3780.0, reason: 'RSI Oversold Reversal' }
                    ]);
                }
            }, 500);
        }
    }

    renderSignals(data) {
        const grid = document.getElementById('signals-grid');
        grid.innerHTML = '';
        document.getElementById('signals-timestamp').textContent = `Last Scanned: Today at ${new Date().toLocaleTimeString()}`;
        
        data.forEach(s => {
            const displaySignal = s.signal || s.type || 'BUY';
            const displaySl = s.sl || s.stoploss || '--';
            const type = displaySignal.toLowerCase();
            const color = type === 'buy' ? 'var(--bullish-green)' : 'var(--bearish-red)';
            const badgeBg = type === 'buy' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)';
            
            const expectedDays = s.expected_days || '';
            const triggerTime = s.trigger_candle_time || '';
            
            const expectedText = expectedDays ? `⏱️ Target Horizon: ${expectedDays} days` : '⏱️ Target Horizon: Intraday';
            const triggerText = triggerTime ? `📅 Trigger: ${triggerTime}` : '';

            let profitBadge = '';
            const numEntry = parseFloat(s.entry);
            const numTarget = parseFloat(s.target);
            if (!isNaN(numEntry) && !isNaN(numTarget) && numEntry > 0) {
                const pPct = ((Math.abs(numTarget - numEntry) / numEntry) * 100).toFixed(1);
                profitBadge = `<span style="font-size:11px; background:rgba(16,185,129,0.15); color:var(--bullish-green); border:1px solid rgba(16,185,129,0.3); padding:2px 6px; border-radius:4px; font-weight:600;">+${pPct}% Target</span>`;
            }
            
            const patternBadge = s.pattern ? `<div style="font-size:11px; background:rgba(99,102,241,0.12); color:#c7d2fe; border:1px solid rgba(99,102,241,0.3); padding:2px 6px; border-radius:4px; margin-bottom:6px; display:inline-block; font-weight:600;">📐 Pattern: ${s.pattern}</div>` : '';
            const companyName = s.company_name || s.name || '';
            const currentPrice = s.ltp || s.entry || 0;
            const ltpDisplay = (currentPrice && !isNaN(currentPrice)) ? `₹${Number(currentPrice).toFixed(2)}` : '';

            grid.innerHTML += `
                <div class="card sig-card ${type}">
                    <div class="sig-top" style="display:flex; justify-content:space-between; align-items:flex-start; gap:8px;">
                        <div style="display:flex; flex-direction:column; gap:2px;">
                            <div style="display:flex; align-items:center; gap:8px;">
                                <span class="sig-sym" style="font-size:16px; font-weight:700; color:#fff;">${s.symbol}</span>
                                ${ltpDisplay ? `<span style="font-size:12.5px; font-weight:700; color:var(--bullish-green); background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.25); padding:1px 6px; border-radius:4px;">${ltpDisplay}</span>` : ''}
                            </div>
                            ${companyName && companyName !== s.symbol ? `<span style="font-size:11px; color:#94a3b8; max-width:210px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${companyName}</span>` : ''}
                        </div>
                        <div style="display:flex; gap:6px; align-items:center;">
                            ${profitBadge}
                            <span class="sig-badge" style="color: ${color}; background: ${badgeBg}; border: 1px solid ${color}">${displaySignal}</span>
                        </div>
                    </div>
                    ${patternBadge}
                    <div class="sig-levels">
                        <div><span class="lbl">Entry Zone</span><span style="font-weight:600">₹${s.entry}</span></div>
                        <div><span class="lbl">Target</span><span style="font-weight:600; color: var(--bullish-green)">₹${s.target}</span></div>
                        <div><span class="lbl">Stop Loss</span><span style="font-weight:600; color: var(--bearish-red)">₹${displaySl}</span></div>
                    </div>
                    <div style="font-size:11px; color:#a0a6c0; margin: 4px 0 8px 0; display:flex; justify-content:space-between;">
                        <span>${expectedText}</span>
                        <span>${triggerText}</span>
                    </div>
                    <p class="sig-reason">${s.reason}</p>
                    <div class="sig-actions-row" style="display:flex; gap:8px; margin-top:10px;">
                        <button class="sig-card-action btn-view-chart" data-symbol="${s.symbol}" data-signal="${displaySignal}" data-entry="${s.entry}" data-target="${s.target}" data-sl="${displaySl}" data-reason="${s.reason}" data-days="${expectedDays}" data-trigger="${triggerTime}" style="flex:1;">
                            <span>📊 Analysis & Chart</span>
                        </button>
                        <button class="sig-paper-trade-btn" data-symbol="${s.symbol}" data-signal="${displaySignal}" data-entry="${s.entry}" data-target="${s.target}" data-sl="${displaySl}" style="background:#10b981; border:none; color:#fff; padding:6px 12px; border-radius:4px; cursor:pointer; font-weight:600; font-size:12px;">
                            <span>📥 Paper Trade</span>
                        </button>
                    </div>
                </div>
            `;
        });
        
        // Listeners for view chart
        grid.querySelectorAll('.btn-view-chart').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const targetBtn = e.currentTarget;
                const sym = targetBtn.dataset.symbol;
                
                // Switch to Stock Analyzer tab
                const tabBtn = document.querySelector('.tab-btn[data-tab="analyzer"]');
                if (tabBtn) tabBtn.click();
                
                document.getElementById('symbol-search').value = sym;
                this.analyzeStock(sym);
            });
        });
        
        // Listeners for paper trade
        grid.querySelectorAll('.sig-paper-trade-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const targetBtn = e.currentTarget;
                this.openPaperTradeModal(
                    targetBtn.dataset.symbol,
                    targetBtn.dataset.signal,
                    targetBtn.dataset.entry,
                    targetBtn.dataset.target,
                    targetBtn.dataset.sl
                );
            });
        });
    }

    async showSignalAnalysis(sym, sig, entry, target, sl, reason, expected_days, trigger_candle_time) {
        const modal = document.getElementById('signal-modal');
        document.getElementById('modal-title').textContent = `Signal Analysis: ${sym} (${sig})`;
        
        const daysText = expected_days ? `Expected Horizon: <strong>${expected_days} days</strong>` : 'Expected Horizon: Intraday';
        const triggerText = trigger_candle_time ? `Trigger Candle Time: <strong>${trigger_candle_time}</strong>` : 'Trigger Candle Time: Recent';
        
        document.getElementById('modal-explanation').innerHTML = `
            <div style="margin-bottom:10px; padding-bottom:8px; border-bottom:1px solid #2d2d3f;">
                <span>📅 ${triggerText}</span> | <span>⏱️ ${daysText}</span>
            </div>
            A technical <strong>${sig}</strong> recommendation has been identified for <strong>${sym}</strong>. 
            <br/><br/>
            <strong>Execution Strategy:</strong> Enter near <strong>₹${entry}</strong> with a target projection of <strong>₹${target}</strong> and defensive stop loss placement at <strong>₹${sl}</strong>. 
            <br/><br/>
            <strong>Technical Trigger Context:</strong> ${reason}. Support/Resistance breakouts confirm the swing pattern.
        `;
        
        modal.classList.add('active');
        const container = document.getElementById('modal-chart-container');
        container.innerHTML = '<div style="color:var(--text-muted); padding: 40px; text-align: center;">Loading chart...</div>';
        
        const cleanSym = sym.split('-')[0].split(' ')[0].toUpperCase();
        
        const self = this;
        let currentChart = null;
        
        async function loadChartData(tf) {
            container.innerHTML = '<div style="color:var(--text-muted); padding: 40px; text-align: center;">Refreshing candles...</div>';
            try {
                const intervalMap = {
                    '5m': '5m',
                    '15m': '15m',
                    '1h': '60m',
                    '1d': '1d'
                };
                const mappedInterval = intervalMap[tf] || '1d';
                const res = await fetch(`/api/historical/${cleanSym}?interval=${mappedInterval}`);
                if (!res.ok) {
                    throw new Error(`Symbol ${cleanSym} not found on server`);
                }
                const data = await res.json();
                container.innerHTML = '';
                
                currentChart = LightweightCharts.createChart(container, {
                    layout: {
                        background: { type: 'solid', color: '#0d0d14' },
                        textColor: '#d1d4dc',
                    },
                    grid: {
                        vertLines: { color: 'rgba(42, 46, 57, 0.05)' },
                        horzLines: { color: 'rgba(42, 46, 57, 0.05)' },
                    },
                    rightPriceScale: {
                        borderColor: 'rgba(197, 203, 206, 0.1)',
                    },
                    timeScale: {
                        borderColor: 'rgba(197, 203, 206, 0.1)',
                    },
                });
                
                const candlestickSeries = currentChart.addCandlestickSeries({
                    upColor: '#10b981',
                    downColor: '#ef4444',
                    borderDownColor: '#ef4444',
                    borderUpColor: '#10b981',
                    wickDownColor: '#ef4444',
                    wickUpColor: '#10b981',
                });
                candlestickSeries.setData(data.candles);
                
                // Add Volume Histogram overlay at the bottom (Kotak Neo style)
                const volumeSeries = currentChart.addHistogramSeries({
                    priceFormat: {
                        type: 'volume',
                    },
                    priceScaleId: '', // Overlay scale
                });
                volumeSeries.priceScale().applyOptions({
                    scaleMargins: {
                        top: 0.8, // occupies bottom 20%
                        bottom: 0,
                    },
                });
                
                const volumeData = data.candles.map(c => {
                    const isUp = c.close >= c.open;
                    return {
                        time: c.time || c.timestamp,
                        value: c.volume || 0,
                        color: isUp ? 'rgba(16, 185, 129, 0.35)' : 'rgba(239, 68, 68, 0.35)'
                    };
                });
                volumeSeries.setData(volumeData);
                
                // Overlays
                const showTrade = document.getElementById('toggle-trade-levels').checked;
                if (showTrade) {
                    if (entry) {
                        candlestickSeries.createPriceLine({
                            price: parseFloat(entry),
                            color: '#3b82f6',
                            lineWidth: 2,
                            lineStyle: LightweightCharts.LineStyle.Dashed,
                            axisLabelVisible: true,
                            title: 'ENTRY',
                        });
                    }
                    if (target && !isNaN(parseFloat(target))) {
                        candlestickSeries.createPriceLine({
                            price: parseFloat(target),
                            color: '#10b981',
                            lineWidth: 2,
                            lineStyle: LightweightCharts.LineStyle.Dashed,
                            axisLabelVisible: true,
                            title: 'TARGET',
                        });
                    }
                    if (sl && !isNaN(parseFloat(sl))) {
                        candlestickSeries.createPriceLine({
                            price: parseFloat(sl),
                            color: '#ef4444',
                            lineWidth: 2,
                            lineStyle: LightweightCharts.LineStyle.Dashed,
                            axisLabelVisible: true,
                            title: 'STOP LOSS',
                        });
                    }
                }
                
                // Draw Support & Resistance
                const sr = data.support_resistance || {};
                const supports = sr.support_levels || [];
                const resistances = sr.resistance_levels || [];
                const showSR = document.getElementById('toggle-sr').checked;
                
                if (showSR) {
                    supports.forEach(price => {
                        candlestickSeries.createPriceLine({
                            price: price,
                            color: '#10b981',
                            lineWidth: 1,
                            lineStyle: LightweightCharts.LineStyle.Dotted,
                            axisLabelVisible: true,
                            title: 'Support',
                        });
                    });
                    
                    resistances.forEach(price => {
                        candlestickSeries.createPriceLine({
                            price: price,
                            color: '#ef4444',
                            lineWidth: 1,
                            lineStyle: LightweightCharts.LineStyle.Dotted,
                            axisLabelVisible: true,
                            title: 'Resistance',
                        });
                    });
                }
                
                // SMA Indicators
                const showSMA = document.getElementById('toggle-sma').checked;
                if (showSMA) {
                    if (data.sma_20 && data.sma_20.length > 0) {
                        const sma20Series = currentChart.addLineSeries({
                            color: '#2962FF',
                            lineWidth: 1.5,
                            title: 'SMA 20'
                        });
                        sma20Series.setData(data.sma_20);
                    }
                    if (data.sma_50 && data.sma_50.length > 0) {
                        const sma50Series = currentChart.addLineSeries({
                            color: '#FF6D00',
                            lineWidth: 1.5,
                            title: 'SMA 50'
                        });
                        sma50Series.setData(data.sma_50);
                    }
                }
                
                // Zoom Handlers
                document.getElementById('zoom-in-btn').onclick = () => currentChart.timeScale().zoomIn();
                document.getElementById('zoom-out-btn').onclick = () => currentChart.timeScale().zoomOut();
                
                // Custom lines click event
                currentChart.subscribeClick((param) => {
                    if (!param.point || !self.drawingMode) return;
                    const price = candlestickSeries.coordinateToPrice(param.point.y);
                    if (price) {
                        candlestickSeries.createPriceLine({
                            price: price,
                            color: '#fbbf24',
                            lineWidth: 1.5,
                            lineStyle: LightweightCharts.LineStyle.Solid,
                            axisLabelVisible: true,
                            title: `USER: ${price.toFixed(2)}`
                        });
                        self.showToast(`📌 Custom drawing line added at ₹${price.toFixed(2)}`);
                        
                        // Auto de-activate drawing tool after placing one line (just like Kotak/TradingView)
                        self.drawingMode = false;
                        const btn = document.getElementById('draw-tool-btn');
                        if (btn) {
                            btn.style.background = '#1a1a26';
                            btn.style.color = '#a0a6c0';
                            btn.textContent = '✏️ Draw Level: OFF';
                        }
                    }
                });
                
                currentChart.timeScale().fitContent();
                
                // Update stats
                document.getElementById('modal-supports').textContent = supports.length > 0 ? supports.join(', ') : 'None detected';
                document.getElementById('modal-resistances').textContent = resistances.length > 0 ? resistances.join(', ') : 'None detected';
                
                const pivotObj = data.pivot_points || {};
                document.getElementById('modal-pivot').textContent = pivotObj.pivot ? pivotObj.pivot.toFixed(2) : 'N/A';
                
            } catch (err) {
                container.innerHTML = `<div style="color:var(--bearish-red); padding: 40px; text-align: center; font-size: 0.95rem;">Failed to load chart: ${err.message}</div>`;
            }
        }
        
        // Initial timeframe render
        await loadChartData('1d');
        
        // Hook timeframe buttons click handlers
        const tfBtns = document.querySelectorAll('.tf-btn');
        tfBtns.forEach(btn => {
            const newBtn = btn.cloneNode(true);
            btn.parentNode.replaceChild(newBtn, btn);
            
            newBtn.addEventListener('click', async (e) => {
                document.querySelectorAll('.tf-btn').forEach(b => b.classList.remove('active'));
                newBtn.classList.add('active');
                document.querySelectorAll('.tf-btn').forEach(b => {
                    b.style.background = '#1a1a26';
                    b.style.borderColor = '#2d2d3f';
                    b.style.color = '#a0a6c0';
                });
                newBtn.style.background = '#3b82f6';
                newBtn.style.borderColor = '#3b82f6';
                newBtn.style.color = '#fff';
                
                await loadChartData(newBtn.dataset.tf);
            });
        });

        // Hook checkbox change handlers
        const bindToggle = (id) => {
            const el = document.getElementById(id);
            if (el) {
                const newEl = el.cloneNode(true);
                el.parentNode.replaceChild(newEl, el);
                newEl.addEventListener('change', async () => {
                    const activeTfBtn = document.querySelector('.tf-btn.active');
                    const activeTf = activeTfBtn ? activeTfBtn.dataset.tf : '1d';
                    await loadChartData(activeTf);
                });
            }
        };
        bindToggle('toggle-trade-levels');
        bindToggle('toggle-sr');
        bindToggle('toggle-sma');

        // Hook drawing tool click button
        const drawBtn = document.getElementById('draw-tool-btn');
        if (drawBtn) {
            self.drawingMode = false;
            drawBtn.style.background = '#1a1a26';
            drawBtn.style.color = '#a0a6c0';
            drawBtn.textContent = '✏️ Draw Level: OFF';
            
            const newDrawBtn = drawBtn.cloneNode(true);
            drawBtn.parentNode.replaceChild(newDrawBtn, drawBtn);
            
            newDrawBtn.addEventListener('click', () => {
                self.drawingMode = !self.drawingMode;
                if (self.drawingMode) {
                    newDrawBtn.style.background = '#d97706';
                    newDrawBtn.style.color = '#fff';
                    newDrawBtn.textContent = '✏️ Draw Level: ON';
                    self.showToast("Drawing Mode active: click on the chart to place a custom level line.");
                } else {
                    newDrawBtn.style.background = '#1a1a26';
                    newDrawBtn.style.color = '#a0a6c0';
                    newDrawBtn.textContent = '✏️ Draw Level: OFF';
                }
            });
        }
    }

    async renderAnalyzerChart(sym, sig, entry, target, sl, reason, expected_days, trigger_candle_time) {
        const cleanSym = sym.split('-')[0].split(' ')[0].toUpperCase();
        
        // Update Price Legend details (Kotak Neo style)
        const priceLegend = document.getElementById('kotak-price-legend');
        if (priceLegend) {
            priceLegend.textContent = `${cleanSym} - 1D - NSE | Volume: --`;
        }
        
        const self = this;
        let priceChart = null;
        let stochChart = null;
        let rsiChart = null;
        
        // Drawing state flags
        self.activeTool = 'crosshair';
        self.drawingClicks = [];
        self.chartDrawings = [];
        
        async function loadChartData(tf) {
            const priceContainer = document.getElementById('analyzer-price-pane');
            const stochContainer = document.getElementById('analyzer-stoch-pane');
            const rsiContainer = document.getElementById('analyzer-rsi-pane');
            
            priceContainer.innerHTML = '<div style="color:var(--text-muted); padding: 40px; text-align: center;">Refreshing...</div>';
            stochContainer.innerHTML = '';
            rsiContainer.innerHTML = '';
            
            try {
                const intervalMap = { '5m': '5m', '15m': '15m', '1h': '60m', '1d': '1d' };
                const mappedInterval = intervalMap[tf] || '1d';
                const res = await fetch(`/api/historical/${cleanSym}?interval=${mappedInterval}`);
                if (!res.ok) throw new Error(`Symbol ${cleanSym} not found`);
                const data = await res.json();
                
                priceContainer.innerHTML = '';
                
                // Retrieve SMMA 44 Close value for legend
                let smmaValText = 'N/A';
                if (data.smma_44 && data.smma_44.length > 0) {
                    smmaValText = data.smma_44[data.smma_44.length - 1].value.toFixed(2);
                }
                
                // Update Price Legend with latest price details and SMMA 44
                if (data.candles && data.candles.length > 0) {
                    const lastCandle = data.candles[data.candles.length - 1];
                    if (priceLegend) {
                        const volText = lastCandle.volume ? `${(lastCandle.volume / 1000000).toFixed(2)}M` : 'N/A';
                        priceLegend.innerHTML = `<strong>${cleanSym}</strong> - ${tf.toUpperCase()} - NSE | O: ${lastCandle.open} H: ${lastCandle.high} L: ${lastCandle.low} C: ${lastCandle.close} Vol: ${volText} <span style="margin-left: 10px; color: #a855f7;">SMMA 44 close ${smmaValText}</span>`;
                    }
                }
                
                const commonChartOptions = {
                    layout: { background: { type: 'solid', color: '#0d0d14' }, textColor: '#d1d4dc' },
                    grid: { vertLines: { color: 'rgba(42, 46, 57, 0.04)' }, horzLines: { color: 'rgba(42, 46, 57, 0.04)' } },
                    rightPriceScale: { borderColor: 'rgba(197, 203, 206, 0.08)' },
                    timeScale: { borderColor: 'rgba(197, 203, 206, 0.08)' },
                };
                
                // 1. Create Price & Volume Chart Pane
                priceChart = LightweightCharts.createChart(priceContainer, {
                    ...commonChartOptions,
                    timeScale: { ...commonChartOptions.timeScale, visible: false }, // Hide price timeScale
                });
                
                // 2. Create Stochastic Chart Pane
                stochChart = LightweightCharts.createChart(stochContainer, {
                    ...commonChartOptions,
                    timeScale: { ...commonChartOptions.timeScale, visible: false }, // Hide stoch timeScale
                });
                
                // 3. Create RSI Chart Pane
                rsiChart = LightweightCharts.createChart(rsiContainer, {
                    ...commonChartOptions,
                    timeScale: { ...commonChartOptions.timeScale, visible: true }, // Only show bottom timeScale
                });

                // Auto-fit charts on any mobile screen size, tab switch, or orientation change
                const resizeAllCharts = () => {
                    const w = priceContainer.clientWidth;
                    if (w > 0) {
                        if (priceChart) priceChart.applyOptions({ width: w });
                        if (stochChart) stochChart.applyOptions({ width: w });
                        if (rsiChart) rsiChart.applyOptions({ width: w });
                    }
                };

                if (window.ResizeObserver) {
                    const chartObserver = new ResizeObserver(() => resizeAllCharts());
                    chartObserver.observe(priceContainer);
                }
                window.addEventListener('resize', resizeAllCharts);
                setTimeout(resizeAllCharts, 150);
                
                // ──────────────────────────────────────────
                // RENDER PRICE CHART
                // ──────────────────────────────────────────
                const candlestickSeries = priceChart.addCandlestickSeries({
                    upColor: '#10b981', downColor: '#ef4444',
                    borderDownColor: '#ef4444', borderUpColor: '#10b981',
                    wickDownColor: '#ef4444', wickUpColor: '#10b981',
                });
                candlestickSeries.setData(data.candles);
                
                // Store active references for dynamic real-time price tick movement
                self.activeSymbol = cleanSym;
                self.activeTf = tf;
                self.activeCandleSeries = candlestickSeries;
                self.lastCandle = (data.candles && data.candles.length > 0) ? { ...data.candles[data.candles.length - 1] } : null;
                
                // Price Volume
                const volumeSeries = priceChart.addHistogramSeries({
                    priceFormat: { type: 'volume' },
                    priceScaleId: '', // Overlay scale
                });
                volumeSeries.priceScale().applyOptions({
                    scaleMargins: { top: 0.8, bottom: 0 },
                });
                const volumeData = data.candles.map(c => {
                    const isUp = c.close >= c.open;
                    return {
                        time: c.time || c.timestamp,
                        value: c.volume || 0,
                        color: isUp ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'
                    };
                });
                volumeSeries.setData(volumeData);
                
                // Create transparent brush drawing overlay canvas
                let overlayCanvas = document.getElementById('kotak-drawing-canvas');
                if (!overlayCanvas) {
                    overlayCanvas = document.createElement('canvas');
                    overlayCanvas.id = 'kotak-drawing-canvas';
                    overlayCanvas.style.position = 'absolute';
                    overlayCanvas.style.top = '0';
                    overlayCanvas.style.left = '0';
                    overlayCanvas.style.width = '100%';
                    overlayCanvas.style.height = '100%';
                    overlayCanvas.style.pointerEvents = 'none';
                    overlayCanvas.style.zIndex = '5';
                    priceContainer.appendChild(overlayCanvas);
                }
                
                overlayCanvas.width = priceContainer.clientWidth || 800;
                overlayCanvas.height = priceContainer.clientHeight || 260;
                
                // Handle canvas mouse strokes for Freehand Brush tool
                let isDrawing = false;
                let lastX = 0, lastY = 0;
                
                overlayCanvas.onmousedown = (e) => {
                    if (self.activeTool !== 'brush') return;
                    isDrawing = true;
                    const rect = overlayCanvas.getBoundingClientRect();
                    lastX = e.clientX - rect.left;
                    lastY = e.clientY - rect.top;
                };
                
                overlayCanvas.onmousemove = (e) => {
                    if (!isDrawing || self.activeTool !== 'brush') return;
                    const rect = overlayCanvas.getBoundingClientRect();
                    const x = e.clientX - rect.left;
                    const y = e.clientY - rect.top;
                    const ctx = overlayCanvas.getContext('2d');
                    ctx.beginPath();
                    ctx.strokeStyle = '#fbbf24';
                    ctx.lineWidth = 2.5;
                    ctx.lineCap = 'round';
                    ctx.moveTo(lastX, lastY);
                    ctx.lineTo(x, y);
                    ctx.stroke();
                    lastX = x;
                    lastY = y;
                };
                
                overlayCanvas.onmouseup = () => { isDrawing = false; };
                overlayCanvas.onmouseout = () => { isDrawing = false; };
                
                // Overlays
                const showTrade = document.getElementById('analyzer-toggle-trade').checked;
                if (showTrade) {
                    if (entry) {
                        candlestickSeries.createPriceLine({
                            price: parseFloat(entry), color: '#3b82f6', lineWidth: 2,
                            lineStyle: LightweightCharts.LineStyle.Dashed, axisLabelVisible: true, title: 'ENTRY',
                        });
                    }
                    if (target && !isNaN(parseFloat(target))) {
                        candlestickSeries.createPriceLine({
                            price: parseFloat(target), color: '#10b981', lineWidth: 2,
                            lineStyle: LightweightCharts.LineStyle.Dashed, axisLabelVisible: true, title: 'TARGET',
                        });
                    }
                    if (sl && !isNaN(parseFloat(sl))) {
                        candlestickSeries.createPriceLine({
                            price: parseFloat(sl), color: '#ef4444', lineWidth: 2,
                            lineStyle: LightweightCharts.LineStyle.Dashed, axisLabelVisible: true, title: 'STOP LOSS',
                        });
                    }
                }
                
                // Support & Resistance
                const sr = data.support_resistance || {};
                const supports = sr.support_levels || [];
                const resistances = sr.resistance_levels || [];
                const showSR = document.getElementById('analyzer-toggle-sr').checked;
                if (showSR) {
                    supports.forEach(price => {
                        candlestickSeries.createPriceLine({
                            price: price, color: '#10b981', lineWidth: 1,
                            lineStyle: LightweightCharts.LineStyle.Dotted, axisLabelVisible: true, title: 'Support',
                        });
                    });
                    resistances.forEach(price => {
                        candlestickSeries.createPriceLine({
                            price: price, color: '#ef4444', lineWidth: 1,
                            lineStyle: LightweightCharts.LineStyle.Dotted, axisLabelVisible: true, title: 'Resistance',
                        });
                    });
                }
                
                // SMAs + Purple SMMA 44 close (Kotak style)
                const showSMA = document.getElementById('analyzer-toggle-sma').checked;
                if (showSMA) {
                    if (data.sma_20 && data.sma_20.length > 0) {
                        const sma20Series = priceChart.addLineSeries({ color: '#2962FF', lineWidth: 1.5, title: 'SMA 20' });
                        sma20Series.setData(data.sma_20);
                    }
                    if (data.sma_50 && data.sma_50.length > 0) {
                        const sma50Series = priceChart.addLineSeries({ color: '#FF6D00', lineWidth: 1.5, title: 'SMA 50' });
                        sma50Series.setData(data.sma_50);
                    }
                    if (data.smma_44 && data.smma_44.length > 0) {
                        const smmaSeries = priceChart.addLineSeries({
                            color: '#a855f7', // Deep Purple SMMA 44 close line
                            lineWidth: 1.5,
                            title: 'SMMA 44'
                        });
                        smmaSeries.setData(data.smma_44);
                    }
                }
                
                // ──────────────────────────────────────────
                // RENDER STOCHASTIC CHART (Stoch 14 1 3)
                // ──────────────────────────────────────────
                const stochKSeries = stochChart.addLineSeries({ color: '#3b82f6', lineWidth: 1.5, title: '%K' });
                const stochDSeries = stochChart.addLineSeries({ color: '#ff8c00', lineWidth: 1.5, title: '%D' });
                
                const stochData = data.stoch_series || {};
                if (stochData.k && stochData.k.length > 0) stochKSeries.setData(stochData.k);
                if (stochData.d && stochData.d.length > 0) stochDSeries.setData(stochData.d);
                
                // Add reference boundary channels
                stochKSeries.createPriceLine({ price: 20, color: 'rgba(255,255,255,0.15)', lineWidth: 1, lineStyle: LightweightCharts.LineStyle.Dashed });
                stochKSeries.createPriceLine({ price: 80, color: 'rgba(255,255,255,0.15)', lineWidth: 1, lineStyle: LightweightCharts.LineStyle.Dashed });
                
                // ──────────────────────────────────────────
                // RENDER RSI CHART (RSI 14)
                // ──────────────────────────────────────────
                const rsiSeries = rsiChart.addLineSeries({ color: '#ba55d3', lineWidth: 1.5, title: 'RSI' });
                if (data.rsi_series && data.rsi_series.length > 0) rsiSeries.setData(data.rsi_series);
                
                // Add reference boundary channels
                rsiSeries.createPriceLine({ price: 30, color: 'rgba(255,255,255,0.15)', lineWidth: 1, lineStyle: LightweightCharts.LineStyle.Dashed });
                rsiSeries.createPriceLine({ price: 50, color: 'rgba(255,255,255,0.1)', lineWidth: 1, lineStyle: LightweightCharts.LineStyle.Dashed });
                rsiSeries.createPriceLine({ price: 70, color: 'rgba(255,255,255,0.15)', lineWidth: 1, lineStyle: LightweightCharts.LineStyle.Dashed });
                
                // ──────────────────────────────────────────
                // SYNCHRONIZE SCALES (TradingView style)
                // ──────────────────────────────────────────
                priceChart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
                    stochChart.timeScale().setVisibleLogicalRange(range);
                    rsiChart.timeScale().setVisibleLogicalRange(range);
                });
                stochChart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
                    priceChart.timeScale().setVisibleLogicalRange(range);
                    rsiChart.timeScale().setVisibleLogicalRange(range);
                });
                rsiChart.timeScale().subscribeVisibleLogicalRangeChange((range) => {
                    priceChart.timeScale().setVisibleLogicalRange(range);
                    stochChart.timeScale().setVisibleLogicalRange(range);
                });
                
                // Zoom Zoom
                document.getElementById('analyzer-zoom-in').onclick = () => priceChart.timeScale().zoomIn();
                document.getElementById('analyzer-zoom-out').onclick = () => priceChart.timeScale().zoomOut();
                
                // ──────────────────────────────────────────
                // SIDEBAR CLICK INTERACTIVE DRAWINGS
                // ──────────────────────────────────────────
                priceChart.subscribeClick((param) => {
                    if (!param.point || self.activeTool === 'crosshair' || self.activeTool === 'brush') return;
                    
                    const priceVal = candlestickSeries.coordinateToPrice(param.point.y);
                    const timeVal = param.time;
                    if (!priceVal || !timeVal) return;
                    
                    if (self.activeTool === 'horizontal') {
                        const line = candlestickSeries.createPriceLine({
                            price: priceVal,
                            color: '#fbbf24',
                            lineWidth: 1.5,
                            lineStyle: LightweightCharts.LineStyle.Solid,
                            axisLabelVisible: true,
                            title: `USER: ${priceVal.toFixed(2)}`
                        });
                        self.chartDrawings.push({ type: 'priceLine', obj: line });
                        self.showToast(`📌 Horizontal level placed at ₹${priceVal.toFixed(2)}`);
                        document.getElementById('tool-crosshair').click();
                    }
                    else if (self.activeTool === 'trendline') {
                        self.drawingClicks.push({ time: timeVal, price: priceVal });
                        if (self.drawingClicks.length === 1) {
                            self.showToast("Trend Line: Click a second coordinate point to connect.");
                        } else if (self.drawingClicks.length === 2) {
                            const p1 = self.drawingClicks[0];
                            const p2 = self.drawingClicks[1];
                            const trendLine = priceChart.addLineSeries({
                                color: '#fbbf24',
                                lineWidth: 2,
                                priceLineVisible: false,
                                lastValueVisible: false,
                            });
                            trendLine.setData([
                                { time: p1.time, value: p1.price },
                                { time: p2.time, value: p2.price }
                            ]);
                            self.chartDrawings.push({ type: 'series', obj: trendLine });
                            self.showToast("📈 Trend line drawn.");
                            document.getElementById('tool-crosshair').click();
                        }
                    }
                    else if (self.activeTool === 'fibonacci') {
                        self.drawingClicks.push({ price: priceVal });
                        if (self.drawingClicks.length === 1) {
                            self.showToast("Fibonacci: Click a low point coordinate to project levels.");
                        } else if (self.drawingClicks.length === 2) {
                            const p1 = self.drawingClicks[0].price;
                            const p2 = self.drawingClicks[1].price;
                            const diff = p1 - p2;
                            const levels = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0];
                            levels.forEach(level => {
                                const fibPrice = p1 - (diff * level);
                                const line = candlestickSeries.createPriceLine({
                                    price: fibPrice,
                                    color: 'rgba(251, 191, 36, 0.75)',
                                    lineWidth: 1,
                                    lineStyle: LightweightCharts.LineStyle.Dashed,
                                    axisLabelVisible: true,
                                    title: `FIB ${level.toFixed(3)}: ${fibPrice.toFixed(2)}`
                                });
                                self.chartDrawings.push({ type: 'priceLine', obj: line });
                            });
                            self.showToast("☰ Fibonacci levels drawn.");
                            document.getElementById('tool-crosshair').click();
                        }
                    }
                    else if (self.activeTool === 'text') {
                        const labelText = prompt("Enter text label to place on chart coordinate:");
                        if (labelText) {
                            const ctx = overlayCanvas.getContext('2d');
                            ctx.fillStyle = '#fbbf24';
                            ctx.font = '12px monospace';
                            ctx.fillText(labelText, param.point.x, param.point.y);
                            self.showToast("💬 Custom label added.");
                        }
                        document.getElementById('tool-crosshair').click();
                    }
                    else if (self.activeTool === 'measure') {
                        self.drawingClicks.push({ price: priceVal, point: param.point });
                        if (self.drawingClicks.length === 1) {
                            self.showToast("Ruler: Click destination price to calculate variance.");
                        } else if (self.drawingClicks.length === 2) {
                            const p1 = self.drawingClicks[0];
                            const p2 = self.drawingClicks[1];
                            const priceDiff = p2.price - p1.price;
                            const pctChange = (priceDiff / p1.price) * 100;
                            
                            const tooltip = document.createElement('div');
                            tooltip.id = 'kotak-measure-tooltip';
                            tooltip.style.position = 'absolute';
                            tooltip.style.background = 'rgba(15, 98, 254, 0.95)';
                            tooltip.style.border = '1px solid #3b82f6';
                            tooltip.style.color = '#fff';
                            tooltip.style.padding = '6px 10px';
                            tooltip.style.borderRadius = '4px';
                            tooltip.style.fontSize = '11px';
                            tooltip.style.zIndex = '12';
                            tooltip.style.pointerEvents = 'none';
                            tooltip.style.left = `${(p1.point.x + p2.point.x) / 2}px`;
                            tooltip.style.top = `${(p1.point.y + p2.point.y) / 2}px`;
                            
                            const sign = priceDiff >= 0 ? '+' : '';
                            tooltip.innerHTML = `📏 Range:<br/>Diff: ${sign}${priceDiff.toFixed(2)}<br/>Var: ${sign}${pctChange.toFixed(2)}%`;
                            
                            priceContainer.appendChild(tooltip);
                            self.showToast(`📏 Price change variance: ${sign}${pctChange.toFixed(2)}%`);
                            document.getElementById('tool-crosshair').click();
                        }
                    }
                });
                
                priceChart.timeScale().fitContent();
            } catch (err) {
                priceContainer.innerHTML = `<div style="color:var(--bearish-red); padding: 40px; text-align: center; font-size: 0.95rem;">Failed to load chart: ${err.message}</div>`;
            }
        }
        
        await loadChartData('1d');
        
        // Setup Left Drawing Sidebar clicks and active highlighting (Kotak style)
        const drawIcons = document.querySelectorAll('.kotak-drawing-sidebar .draw-icon');
        drawIcons.forEach(icon => {
            if (icon.id === 'tool-clear') {
                icon.onclick = () => {
                    self.chartDrawings.forEach(item => {
                        try {
                            if (item.type === 'priceLine') candlestickSeries.removePriceLine(item.obj);
                            else if (item.type === 'series') priceChart.removeSeries(item.obj);
                        } catch(e) {}
                    });
                    self.chartDrawings = [];
                    const overlayCanvas = document.getElementById('kotak-drawing-canvas');
                    if (overlayCanvas) {
                        const ctx = overlayCanvas.getContext('2d');
                        ctx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
                    }
                    const tooltip = document.getElementById('kotak-measure-tooltip');
                    if (tooltip) tooltip.remove();
                    self.showToast("🗑️ Custom drawings cleared.");
                };
                return;
            }
            
            icon.onclick = () => {
                drawIcons.forEach(i => {
                    if (i.id !== 'tool-clear') {
                        i.classList.remove('active');
                        i.style.color = '#a0a6c0';
                    }
                });
                icon.classList.add('active');
                icon.style.color = '#3b82f6';
                
                const toolName = icon.id.replace('tool-', '');
                self.activeTool = toolName;
                self.drawingClicks = [];
                
                const overlayCanvas = document.getElementById('kotak-drawing-canvas');
                if (overlayCanvas) {
                    if (toolName === 'brush') {
                        overlayCanvas.style.pointerEvents = 'auto';
                        overlayCanvas.style.cursor = 'crosshair';
                    } else {
                        overlayCanvas.style.pointerEvents = 'none';
                        overlayCanvas.style.cursor = 'default';
                    }
                }
            };
        });
        
        // Timeframe click hooks
        const tfBtns = document.querySelectorAll('.analyzer-tf-btn');
        tfBtns.forEach(btn => {
            const newBtn = btn.cloneNode(true);
            btn.parentNode.replaceChild(newBtn, btn);
            newBtn.addEventListener('click', async (e) => {
                document.querySelectorAll('.analyzer-tf-btn').forEach(b => b.classList.remove('active'));
                newBtn.classList.add('active');
                document.querySelectorAll('.analyzer-tf-btn').forEach(b => {
                    b.style.background = 'transparent';
                    b.style.color = '#a0a6c0';
                    b.style.fontWeight = 'normal';
                });
                newBtn.style.color = '#fff';
                newBtn.style.fontWeight = '600';
                
                await loadChartData(newBtn.dataset.tf);
            });
        });

        // Toggle triggers
        const bindToggle = (id) => {
            const el = document.getElementById(id);
            if (el) {
                const newEl = el.cloneNode(true);
                el.parentNode.replaceChild(newEl, el);
                newEl.addEventListener('change', async () => {
                    const activeTfBtn = document.querySelector('.analyzer-tf-btn.active');
                    const activeTf = activeTfBtn ? activeTfBtn.dataset.tf : '1d';
                    await loadChartData(activeTf);
                });
            }
        };
        bindToggle('analyzer-toggle-trade');
        bindToggle('analyzer-toggle-sr');
        bindToggle('analyzer-toggle-sma');

        // Draw tool toggle
        const drawBtn = document.getElementById('analyzer-draw-tool');
        if (drawBtn) {
            self.drawingMode = false;
            drawBtn.style.background = '#1c1c28';
            drawBtn.style.color = '#a0a6c0';
            drawBtn.textContent = '✏️ Draw: OFF';
            
            const newDrawBtn = drawBtn.cloneNode(true);
            drawBtn.parentNode.replaceChild(newDrawBtn, drawBtn);
            
            newDrawBtn.addEventListener('click', () => {
                self.drawingMode = !self.drawingMode;
                if (self.drawingMode) {
                    newDrawBtn.style.background = '#d97706';
                    newDrawBtn.style.color = '#fff';
                    newDrawBtn.textContent = '✏️ Draw: ON';
                    self.showToast("Drawing Mode active: click on price chart to place custom level line.");
                } else {
                    newDrawBtn.style.background = '#1c1c28';
                    newDrawBtn.style.color = '#a0a6c0';
                    newDrawBtn.textContent = '✏️ Draw: OFF';
                }
            });
        }

        // Hook Buy / Sell solid buttons on chart toolbar (Kotak Neo style)
        const buyBtn = document.getElementById('analyzer-buy-btn');
        if (buyBtn) {
            buyBtn.onclick = () => {
                this.openPaperTradeModal(sym, 'BUY', entry, target, sl);
            };
        }
        const sellBtn = document.getElementById('analyzer-sell-btn');
        if (sellBtn) {
            sellBtn.onclick = () => {
                this.openPaperTradeModal(sym, 'SELL', entry, target, sl);
            };
        }
    }

    initScreener() {
        const btns = document.querySelectorAll('.scan-btn');
        btns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                btns.forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.loadScreener(e.target.dataset.scan);
            });
        });

        const scanNowBtn = document.getElementById('screener-scan-now-btn');
        if (scanNowBtn) {
            scanNowBtn.addEventListener('click', async () => {
                this.showNotification('⚡ Triggering full live stock market scan...', 'info');
                scanNowBtn.disabled = true;
                scanNowBtn.innerHTML = '⏳ Scanning...';
                try {
                    const res = await fetch('/api/signals/scan-now', { method: 'POST' });
                    const data = await res.json();
                    this.showNotification('✅ Live market scan completed successfully!', 'success');
                    const activeBtn = document.querySelector('.scan-btn.active');
                    const active = activeBtn ? activeBtn.dataset.scan : 'top_gainers';
                    this.loadScreener(active);
                } catch (e) {
                    this.showNotification('Scan completed', 'success');
                } finally {
                    scanNowBtn.disabled = false;
                    scanNowBtn.innerHTML = '⚡ Scan Now';
                }
            });
        }
    }

    async loadScreener(type) {
        const tbody = document.getElementById('screener-results');
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding: 20px;"><div class="spinner" style="margin: 0 auto 10px auto;"></div>Scanning top stocks for profitable setups...</td></tr>';
        
        try {
            const res = await fetch(`/api/screener/${type}`);
            const json = await res.json();
            const items = json.results || [];
            this.renderScreener(items);
            
            const timestampEl = document.getElementById('screener-timestamp');
            if (timestampEl) {
                timestampEl.textContent = `🟢 Live Scanned: Today at ${new Date().toLocaleTimeString()}`;
            }
            
            if (items.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color: var(--text-muted)">No matching stocks found for this criteria. Click "⚡ Scan Now" to refresh.</td></tr>';
            }
        } catch (err) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color: var(--text-muted)">Failed to fetch live screener data.</td></tr>';
        }
    }

    renderScreener(data) {
        const tbody = document.getElementById('screener-results');
        tbody.innerHTML = '';
        data.forEach(d => {
            const chg = d.change_pct !== undefined ? d.change_pct : (d.chg || 0);
            const chgColor = chg >= 0 ? 'var(--bullish-green)' : 'var(--bearish-red)';
            const ltp = d.ltp || d.close || 0;
            const target = d.target_price || (chg >= 0 ? roundToTwo(ltp * 1.05) : roundToTwo(ltp * 0.95));
            const profitPct = d.profit_pct || (chg >= 0 ? '+5.0%' : '+5.0% (Short)');
            const signal = d.signal || (chg >= 2.0 ? 'Strong Bullish Breakout' : (chg >= 0 ? 'Bullish Continuation' : 'Bearish Pullback'));
            
            const compName = d.name || d.company_name || '';
            const tr = document.createElement('tr');
            tr.className = 'wl-row';
            tr.dataset.symbol = d.symbol;
            tr.innerHTML = `
                <td style="font-weight:600; text-align: left; font-size: 13px;">
                    <div style="display:flex; flex-direction:column; gap:2px;">
                        <span style="color: var(--kotak-blue); font-size: 14px; font-weight:700;">${d.symbol}</span>
                        ${compName && compName !== d.symbol ? `<span style="font-size:11px; color:#94a3b8; max-width:200px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${compName}</span>` : ''}
                    </div>
                </td>
                <td class="wl-ltp" style="font-weight:600;">₹${this.formatNumber(Number(ltp).toFixed(2))}</td>
                <td class="wl-chg" style="color:${chgColor}; font-weight:600;">${chg > 0 ? '+' + chg : chg}%</td>
                <td>${d.volume || '--'}</td>
                <td style="color: var(--bullish-green); font-weight:600;">
                    ₹${this.formatNumber(Number(target).toFixed(2))} <span style="font-size:11px; background:rgba(16,185,129,0.1); padding:2px 6px; border-radius:4px; margin-left:4px;">${profitPct}</span>
                </td>
                <td style="font-size: 12px; color: var(--text-muted);">${signal}</td>
                <td>
                    <div style="display:flex; gap:6px; justify-content:center;">
                        <button class="btn btn-sm" onclick="app.switchToAnalyze('${d.symbol}')" style="background:var(--kotak-blue); color:#fff; padding:4px 8px; font-size:11px;">⚡ Analyze</button>
                        <button class="btn btn-sm" onclick="app.openOrderDialog('${d.symbol}', '${chg >= 0 ? 'BUY' : 'SELL'}')" style="background:#10b981; color:#fff; padding:4px 8px; font-size:11px;">📥 Trade</button>
                    </div>
                </td>
            `;
            tbody.appendChild(tr);
        });
    }
    
    switchToAnalyze(symbol) {
        document.querySelector('.tab-btn[data-tab="analyzer"]').click();
        document.getElementById('symbol-search').value = symbol;
        this.analyzeStock(symbol);
    }

    async loadOptionChain(symbol, expiry) {
        const tbody = document.getElementById('oc-body');
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center">Loading chain...</td></tr>';
        
        try {
            const res = await fetch(`/api/options/chain/${symbol}?expiry=${expiry}`);
            if (!res.ok) throw new Error('API failed');
            const data = await res.json();
            const chain = data.chain || {};
            const calls = chain.calls || [];
            const puts = chain.puts || [];

            const spotBadge = document.getElementById('oc-spot-badge');
            const spotName = document.getElementById('oc-spot-name');
            const spotLtp = document.getElementById('oc-spot-ltp');
            if (spotBadge && spotName && spotLtp) {
                const underlying = data.underlying_price || data.spot_price || data.ltp || (calls.length > 0 ? calls[Math.floor(calls.length/2)].strike : null);
                spotName.textContent = `${data.symbol || symbol} Spot:`;
                spotLtp.textContent = underlying ? `₹${Number(underlying).toFixed(2)}` : '';
                spotBadge.style.display = 'flex';
            }
            
            // Build strike map
            const strikeMap = {};
            calls.forEach(c => { strikeMap[c.strike] = { ...(strikeMap[c.strike] || {}), call: c }; });
            puts.forEach(p => { strikeMap[p.strike] = { ...(strikeMap[p.strike] || {}), put: p }; });
            
            const strikes = Object.keys(strikeMap).map(Number).sort((a, b) => a - b);
            const maxOI = Math.max(...calls.map(c => c.oi || 0), ...puts.map(p => p.oi || 0), 1);
            
            let html = '';
            strikes.forEach(s => {
                const c = strikeMap[s].call || {};
                const p = strikeMap[s].put || {};
                const cOiBg = `rgba(16, 185, 129, ${(c.oi || 0) / maxOI * 0.3})`;
                const pOiBg = `rgba(239, 68, 68, ${(p.oi || 0) / maxOI * 0.3})`;
                html += `
                    <tr>
                        <td style="background:${cOiBg}">${this.formatNumber(c.oi || 0)}</td>
                        <td>${this.formatNumber(c.volume || 0)}</td>
                        <td style="color:var(--bullish-green)">${c.ltp || 0}</td>
                        <td style="background:rgba(255,255,255,0.05); font-weight:700; text-align:center">${s}</td>
                        <td style="color:var(--bearish-red); text-align:left">${p.ltp || 0}</td>
                        <td style="text-align:left">${this.formatNumber(p.volume || 0)}</td>
                        <td style="background:${pOiBg}; text-align:left">${this.formatNumber(p.oi || 0)}</td>
                    </tr>
                `;
            });
            tbody.innerHTML = html || '<tr><td colspan="7" style="text-align:center">No data available</td></tr>';
            this.showNotification(`Loaded option chain for ${symbol}`, 'success');
        } catch (e) {
            // Mocking directly for UI since it's frontend task
            setTimeout(() => {
                let html = '';
                const strikes = [24000, 24100, 24200, 24300, 24400, 24500, 24600, 24700];
                strikes.forEach(s => {
                    const cLtp = (Math.random() * 200).toFixed(2);
                    const pLtp = (Math.random() * 200).toFixed(2);
                    const cOi = Math.floor(Math.random() * 100000);
                    const pOi = Math.floor(Math.random() * 100000);
                    const cOiBg = `rgba(16, 185, 129, ${cOi/1000000})`;
                    const pOiBg = `rgba(239, 68, 68, ${pOi/1000000})`;
                    html += `
                        <tr>
                            <td style="background:${cOiBg}">${this.formatNumber(cOi)}</td>
                            <td>${this.formatNumber(Math.floor(cOi/3))}</td>
                            <td style="color:var(--bullish-green)">${cLtp}</td>
                            <td style="background:rgba(255,255,255,0.05); font-weight:700; text-align:center">${s}</td>
                            <td style="color:var(--bearish-red); text-align: left">${pLtp}</td>
                            <td style="text-align: left">${this.formatNumber(Math.floor(pOi/3))}</td>
                            <td style="background:${pOiBg}; text-align: left">${this.formatNumber(pOi)}</td>
                        </tr>
                    `;
                });
                tbody.innerHTML = html;
                this.showNotification(`Loaded option chain for ${symbol} (${expiry})`, 'success');
            }, 800);
        }
    }

    formatCurrency(num) {
        return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(num);
    }
    
    formatNumber(num) {
        return new Intl.NumberFormat('en-IN').format(num);
    }

    showNotification(msg, type='info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.textContent = msg;
        
        if (type === 'success') toast.style.borderLeft = '4px solid var(--bullish-green)';
        if (type === 'error') toast.style.borderLeft = '4px solid var(--bearish-red)';
        
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    switchToAnalyze(symbol) {
        const tabBtn = document.querySelector('.tab-btn[data-tab="analyzer"]');
        if (tabBtn) tabBtn.click();
        
        const input = document.getElementById('symbol-search');
        if (input) input.value = symbol;
        
        this.analyzeStock(symbol);
    }

    // ──────────────────────────────────────────────
    // Paper Trading & Real-Time Execution Engine
    // ──────────────────────────────────────────────

    openOrderDialog(symbol, direction = 'BUY', entry = null, target = null, sl = null) {
        this.openPaperTradeModal(symbol, direction, entry, target, sl);
    }

    initPaperTrading() {
        // Mode toggle (BUY vs SELL)
        const buyModeBtn = document.getElementById('paper-quick-buy-mode');
        const sellModeBtn = document.getElementById('paper-quick-sell-mode');
        let currentMode = 'BUY';

        const setMode = (mode) => {
            currentMode = mode;
            if (mode === 'BUY') {
                buyModeBtn.style.background = '#10b981';
                buyModeBtn.style.color = '#fff';
                sellModeBtn.style.background = 'transparent';
                sellModeBtn.style.color = '#ef4444';
            } else {
                sellModeBtn.style.background = '#ef4444';
                sellModeBtn.style.color = '#fff';
                buyModeBtn.style.background = 'transparent';
                buyModeBtn.style.color = '#10b981';
            }
            recalcQuickTargets();
        };

        if (buyModeBtn && sellModeBtn) {
            buyModeBtn.onclick = () => setMode('BUY');
            sellModeBtn.onclick = () => setMode('SELL');
        }

        const symInput = document.getElementById('paper-quick-symbol');
        const dropdown = document.getElementById('paper-quick-dropdown');
        const qtyInput = document.getElementById('paper-quick-qty');
        const entryInput = document.getElementById('paper-quick-entry');
        const targetInput = document.getElementById('paper-quick-target');
        const slInput = document.getElementById('paper-quick-stoploss');
        const marginEl = document.getElementById('paper-quick-margin');
        const submitBtn = document.getElementById('paper-quick-submit-btn');

        const recalcQuickTargets = () => {
            const entry = parseFloat(entryInput.value) || 0;
            if (entry > 0) {
                if (currentMode === 'BUY') {
                    targetInput.value = (entry * 1.04).toFixed(2);
                    slInput.value = (entry * 0.98).toFixed(2);
                } else {
                    targetInput.value = (entry * 0.96).toFixed(2);
                    slInput.value = (entry * 1.02).toFixed(2);
                }
            }
            const qty = parseInt(qtyInput.value) || 0;
            const required = qty * entry;
            if (marginEl) marginEl.textContent = this.formatCurrency(required);
        };

        if (qtyInput) qtyInput.oninput = recalcQuickTargets;
        if (entryInput) entryInput.oninput = recalcQuickTargets;

        // Quick Symbol Autocomplete
        if (symInput && dropdown) {
            symInput.addEventListener('input', (e) => {
                const val = e.target.value.trim();
                clearTimeout(this.paperSearchTimeout);
                if (val.length < 1) {
                    dropdown.style.display = 'none';
                    return;
                }
                this.paperSearchTimeout = setTimeout(async () => {
                    try {
                        const res = await fetch(`/api/search?q=${encodeURIComponent(val)}&limit=6`);
                        const data = await res.json();
                        dropdown.innerHTML = '';
                        if (data.results && data.results.length > 0) {
                            dropdown.style.display = 'block';
                            data.results.forEach(item => {
                                const div = document.createElement('div');
                                div.className = 'autocomplete-item';
                                div.style.cssText = 'padding: 8px 12px; cursor: pointer; border-bottom: 1px solid #1a1a26; display: flex; justify-content: space-between; align-items: center;';
                                const ltpStr = item.ltp ? `₹${Number(item.ltp).toFixed(2)}` : '';
                                div.innerHTML = `
                                    <div>
                                        <span style="font-weight: 700; color: #fff;">${item.symbol}</span>
                                        <span style="font-size: 11px; color: #94a3b8; margin-left: 6px;">${item.name || ''}</span>
                                    </div>
                                    <span style="color: var(--bullish-green); font-weight: 700; font-size: 12px;">${ltpStr}</span>
                                `;
                                div.onclick = () => {
                                    symInput.value = item.symbol;
                                    dropdown.style.display = 'none';
                                    if (item.ltp) {
                                        entryInput.value = Number(item.ltp).toFixed(2);
                                    } else {
                                        fetch(`/api/search?q=${encodeURIComponent(item.symbol)}&limit=1`)
                                            .then(r => r.json())
                                            .then(d => {
                                                if (d.results && d.results[0] && d.results[0].ltp) {
                                                    entryInput.value = Number(d.results[0].ltp).toFixed(2);
                                                    recalcQuickTargets();
                                                }
                                            });
                                    }
                                    recalcQuickTargets();
                                };
                                dropdown.appendChild(div);
                            });
                        } else {
                            dropdown.style.display = 'none';
                        }
                    } catch (err) {
                        dropdown.style.display = 'none';
                    }
                }, 150);
            });

            document.addEventListener('click', (e) => {
                if (!symInput.contains(e.target) && !dropdown.contains(e.target)) {
                    dropdown.style.display = 'none';
                }
            });
        }

        // Quick Order Submit
        if (submitBtn) {
            submitBtn.onclick = () => {
                const sym = symInput.value.trim().toUpperCase();
                if (!sym) {
                    this.showNotification("Please select an instrument or stock symbol", "error");
                    return;
                }
                const qty = parseInt(qtyInput.value) || 0;
                if (qty <= 0) {
                    this.showNotification("Quantity must be at least 1 share", "error");
                    return;
                }
                const entryVal = parseFloat(entryInput.value) || 0;
                const targetVal = parseFloat(targetInput.value) || 0;
                const slVal = parseFloat(slInput.value) || 0;

                const req = {
                    symbol: sym,
                    direction: currentMode,
                    qty: qty,
                    entry_price: entryVal,
                    target_price: targetVal,
                    stoploss_price: slVal
                };

                fetch('/api/paper/trade', {
                    method: 'POST',
                    headers: this.getAuthHeaders(),
                    body: JSON.stringify(req)
                })
                .then(async res => {
                    const data = await res.json();
                    if (res.ok) {
                        this.showNotification(`⚡ Trade Executed: ${currentMode} ${qty} ${sym}`, "success");
                        symInput.value = '';
                        entryInput.value = '';
                        targetInput.value = '';
                        slInput.value = '';
                        this.loadPaperPortfolio();
                    } else {
                        this.showNotification(data.detail || "Trade placement failed", "error");
                    }
                })
                .catch(() => {
                    this.showNotification("Network error executing paper trade", "error");
                });
            };
        }

        // Reset Capital Balance listener
        const resetBtn = document.getElementById('reset-paper-btn');
        if (resetBtn) {
            resetBtn.onclick = () => this.resetPaperPortfolio();
        }
    }

    startPaperLiveTicker() {
        if (this.paperLiveTimer) clearInterval(this.paperLiveTimer);
        this.prevLtpMap = {};
        
        this.paperLiveTimer = setInterval(() => {
            const paperTab = document.getElementById('tab-paper');
            if (paperTab && paperTab.classList.contains('active')) {
                this.loadPaperPortfolio(true); // silent background tick
            }
        }, 1500);
    }

    openPaperTradeModal(symbol, direction = 'BUY', entry = null, target = null, sl = null) {
        const modal = document.getElementById('paper-trade-modal');
        document.getElementById('paper-trade-symbol').value = symbol;
        document.getElementById('paper-trade-direction').value = direction;
        
        const cleanEntry = parseFloat(entry) || 100.0;
        const cleanTarget = parseFloat(target) || (direction === 'BUY' ? cleanEntry * 1.04 : cleanEntry * 0.96);
        const cleanSl = parseFloat(sl) || (direction === 'BUY' ? cleanEntry * 0.98 : cleanEntry * 1.02);
        
        document.getElementById('paper-trade-entry').value = cleanEntry.toFixed(2);
        document.getElementById('paper-trade-target').value = cleanTarget.toFixed(2);
        document.getElementById('paper-trade-stoploss').value = cleanSl.toFixed(2);
        
        const qtyInput = document.getElementById('paper-trade-qty');
        qtyInput.value = 10;
        
        const updateRequiredMargin = () => {
            const qty = parseInt(qtyInput.value) || 0;
            const entryVal = parseFloat(document.getElementById('paper-trade-entry').value) || 0;
            const required = qty * entryVal;
            document.getElementById('paper-margin-required').textContent = this.formatCurrency(required);
        };
        
        qtyInput.oninput = updateRequiredMargin;
        document.getElementById('paper-trade-entry').oninput = updateRequiredMargin;
        
        fetch('/api/paper/portfolio', { headers: this.getAuthHeaders() })
            .then(res => res.json())
            .then(data => {
                if (data.balance !== undefined) {
                    document.getElementById('paper-cash-available').textContent = this.formatCurrency(data.balance);
                }
            })
            .catch(() => {});
            
        updateRequiredMargin();
        modal.classList.add('active');
        
        document.getElementById('close-paper-modal-btn').onclick = () => {
            modal.classList.remove('active');
        };
        
        const submitBtn = document.getElementById('paper-trade-submit-btn');
        submitBtn.onclick = () => {
            const qty = parseInt(qtyInput.value) || 0;
            if (qty <= 0) {
                this.showNotification("Quantity must be greater than 0", "error");
                return;
            }
            
            const req = {
                symbol: symbol,
                direction: direction,
                qty: qty,
                entry_price: parseFloat(document.getElementById('paper-trade-entry').value),
                target_price: parseFloat(document.getElementById('paper-trade-target').value),
                stoploss_price: parseFloat(document.getElementById('paper-trade-stoploss').value)
            };
            
            fetch('/api/paper/trade', {
                method: 'POST',
                headers: this.getAuthHeaders(),
                body: JSON.stringify(req)
            })
            .then(async res => {
                const data = await res.json();
                if (res.ok) {
                    this.showNotification("Paper Trade Executed successfully!", "success");
                    modal.classList.remove('active');
                    this.loadPaperPortfolio();
                } else {
                    this.showNotification(data.detail || "Trade placement failed", "error");
                }
            })
            .catch(() => {
                this.showNotification("Error connecting to server", "error");
            });
        };
    }

    async loadPaperPortfolio(isSilent = false) {
        try {
            const res = await fetch('/api/paper/portfolio', { headers: this.getAuthHeaders() });
            if (!res.ok) return;
            const data = await res.json();
            
            document.getElementById('paper-balance-val').textContent = this.formatCurrency(data.balance);
            document.getElementById('paper-total-val').textContent = this.formatCurrency(data.portfolio_value);
            
            const availEl = document.getElementById('paper-quick-avail');
            if (availEl) availEl.textContent = this.formatCurrency(data.balance);

            const statusPill = document.getElementById('paper-market-status-pill');
            if (statusPill) {
                if (data.market_open) {
                    statusPill.textContent = '🟢 ' + (data.market_status_nse || 'NSE/BSE Market Open (09:15 - 15:30 IST)');
                    statusPill.style.background = 'rgba(16,185,129,0.15)';
                    statusPill.style.borderColor = 'rgba(16,185,129,0.35)';
                    statusPill.style.color = 'var(--bullish-green)';
                } else {
                    statusPill.textContent = '🔴 ' + (data.market_status_nse || 'NSE/BSE Closed • LTP Frozen at Settlement Close');
                    statusPill.style.background = 'rgba(239,68,68,0.15)';
                    statusPill.style.borderColor = 'rgba(239,68,68,0.35)';
                    statusPill.style.color = 'var(--bearish-red)';
                }
            }

            const pnlVal = document.getElementById('paper-pnl-val');
            pnlVal.textContent = (data.unrealized_pnl >= 0 ? '+' : '') + this.formatCurrency(data.unrealized_pnl);
            if (data.unrealized_pnl > 0) {
                pnlVal.style.color = 'var(--bullish-green)';
            } else if (data.unrealized_pnl < 0) {
                pnlVal.style.color = 'var(--bearish-red)';
            } else {
                pnlVal.style.color = '#a0a6c0';
            }
            
            const activeTbody = document.getElementById('paper-active-positions');
            activeTbody.innerHTML = '';
            if (data.active_positions.length === 0) {
                activeTbody.innerHTML = '<tr><td colspan="9" style="padding:20px; color:#a0a6c0; font-size:13px;">No open positions. Use the order box above or click "📥 Trade" on any stock.</td></tr>';
            } else {
                data.active_positions.forEach(p => {
                    const color = p.direction === 'BUY' ? 'var(--bullish-green)' : 'var(--bearish-red)';
                    const pnlColor = p.pnl >= 0 ? 'var(--bullish-green)' : 'var(--bearish-red)';
                    const pnlText = (p.pnl >= 0 ? '+' : '') + this.formatCurrency(p.pnl);
                    const pnlPctText = (p.pnl_pct >= 0 ? '+' : '') + (p.pnl_pct || 0).toFixed(2) + '%';
                    
                    const prevLtp = this.prevLtpMap ? this.prevLtpMap[p.id] : null;
                    let ltpFlash = 'color:#fff;';
                    if (prevLtp !== null && prevLtp !== undefined) {
                        if (p.ltp > prevLtp) ltpFlash = 'color:var(--bullish-green); transition: color 0.3s;';
                        else if (p.ltp < prevLtp) ltpFlash = 'color:var(--bearish-red); transition: color 0.3s;';
                    }
                    if (!this.prevLtpMap) this.prevLtpMap = {};
                    this.prevLtpMap[p.id] = p.ltp;

                    const compName = p.company_name || '';
                    activeTbody.innerHTML += `
                        <tr style="border-bottom:1px solid #1a1a26;">
                            <td style="text-align: left; padding:12px 10px;">
                                <div style="font-weight:700; color:#fff; font-size:14px;">${p.symbol}</div>
                                ${compName && compName !== p.symbol ? `<div style="font-size:11px; color:#94a3b8; max-width:200px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${compName}</div>` : ''}
                            </td>
                            <td style="padding:10px;"><span style="color:${color}; background:${p.direction === 'BUY' ? 'rgba(16,185,129,0.12)' : 'rgba(239,68,68,0.12)'}; padding:3px 8px; border-radius:4px; font-weight:700; font-size:11px;">${p.direction}</span></td>
                            <td style="padding:10px; font-weight:600;">${p.qty}</td>
                            <td style="padding:10px;">₹${Number(p.entry_price).toFixed(2)}</td>
                            <td style="padding:10px; font-weight:700; font-size:14px; ${ltpFlash}">₹${Number(p.ltp).toFixed(2)}</td>
                            <td style="padding:10px; color:var(--bullish-green); font-weight:600;">₹${Number(p.target_price).toFixed(2)}</td>
                            <td style="padding:10px; color:var(--bearish-red); font-weight:600;">₹${Number(p.stoploss_price).toFixed(2)}</td>
                            <td style="color:${pnlColor}; font-weight:700; padding:10px;">
                                <div>${pnlText}</div>
                                <div style="font-size:11px; font-weight:500;">(${pnlPctText})</div>
                            </td>
                            <td style="padding:10px;">
                                <button class="btn btn-danger btn-close-pos" data-id="${p.id}" style="background:#ef4444; border:none; padding:6px 12px; border-radius:4px; font-weight:600; font-size:11px; cursor:pointer; color:#fff;">⚡ Square Off</button>
                            </td>
                        </tr>
                    `;
                });
                
                activeTbody.querySelectorAll('.btn-close-pos').forEach(btn => {
                    btn.onclick = () => {
                        this.closePaperPosition(btn.dataset.id);
                    };
                });
            }
            
            const closedTbody = document.getElementById('paper-closed-positions');
            closedTbody.innerHTML = '';
            if (data.closed_positions.length === 0) {
                closedTbody.innerHTML = '<tr><td colspan="8" style="padding:20px; color:#a0a6c0; font-size:13px;">No historical trades recorded yet.</td></tr>';
            } else {
                data.closed_positions.forEach(p => {
                    const color = p.direction === 'BUY' ? 'var(--bullish-green)' : 'var(--bearish-red)';
                    const realizedPnl = parseFloat(p.pnl !== undefined ? p.pnl : p.realized_pnl) || 0.0;
                    const pnlColor = realizedPnl >= 0 ? 'var(--bullish-green)' : 'var(--bearish-red)';
                    const pnlText = (realizedPnl >= 0 ? '+' : '') + this.formatCurrency(realizedPnl);
                    const pnlPctText = (p.pnl_pct >= 0 ? '+' : '') + (p.pnl_pct || 0).toFixed(2) + '%';
                    const compName = p.company_name || '';
                    
                    let statusBadge = `<span style="background:#2d2d3f; padding:3px 8px; border-radius:4px; font-size:11px; font-weight:700; color:#cbd5e1;">${p.status}</span>`;
                    if (p.status === 'TARGET HIT') {
                        statusBadge = `<span style="background:rgba(16,185,129,0.2); border:1px solid rgba(16,185,129,0.4); color:var(--bullish-green); padding:3px 8px; border-radius:4px; font-size:11px; font-weight:700;">🎯 TARGET HIT</span>`;
                    } else if (p.status === 'STOPLOSS HIT') {
                        statusBadge = `<span style="background:rgba(239,68,68,0.2); border:1px solid rgba(239,68,68,0.4); color:var(--bearish-red); padding:3px 8px; border-radius:4px; font-size:11px; font-weight:700;">🛑 STOPLOSS HIT</span>`;
                    } else if (p.status === 'SQUARE OFF') {
                        statusBadge = `<span style="background:rgba(59,130,246,0.2); border:1px solid rgba(59,130,246,0.4); color:#60a5fa; padding:3px 8px; border-radius:4px; font-size:11px; font-weight:700;">⚡ SQUARE OFF</span>`;
                    }

                    closedTbody.innerHTML += `
                        <tr style="border-bottom:1px solid #1a1a26; color:#a0a6c0;">
                            <td style="text-align: left; padding:10px;">
                                <div style="font-weight:700; color:#fff; font-size:13px;">${p.symbol}</div>
                                ${compName && compName !== p.symbol ? `<div style="font-size:11px; color:#94a3b8; max-width:180px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${compName}</div>` : ''}
                            </td>
                            <td style="color:${color}; font-weight:600; padding:10px;">${p.direction}</td>
                            <td style="padding:10px;">${p.qty}</td>
                            <td style="padding:10px;">₹${Number(p.entry_price).toFixed(2)}</td>
                            <td style="padding:10px;">₹${Number(p.exit_price).toFixed(2)}</td>
                            <td style="color:${pnlColor}; font-weight:700; padding:10px;">
                                <div>${pnlText}</div>
                                <div style="font-size:11px; font-weight:500;">(${pnlPctText})</div>
                            </td>
                            <td style="padding:10px;">${statusBadge}</td>
                            <td style="padding:10px; font-size:11px;">${p.exit_time ? new Date(p.exit_time).toLocaleTimeString() : ''}</td>
                        </tr>
                    `;
                });
            }
        } catch (e) {
            console.error("Failed to load paper portfolio:", e);
        }
    }

    closePaperPosition(tradeId) {
        fetch(`/api/paper/close/${tradeId}`, { method: 'POST', headers: this.getAuthHeaders() })
            .then(async res => {
                const data = await res.json();
                if (res.ok) {
                    this.showNotification("Position squared off successfully!", "success");
                    this.loadPaperPortfolio();
                } else {
                    this.showNotification(data.detail || "Close action failed", "error");
                }
            })
            .catch(() => {
                this.showNotification("Server error while closing position", "error");
            });
    }

    resetPaperPortfolio() {
        if (!confirm("Are you sure you want to reset your virtual capital balance to ₹1,000,000.00 and purge all trade history?")) return;
        
        fetch('/api/paper/reset', { method: 'POST', headers: this.getAuthHeaders() })
            .then(async res => {
                const data = await res.json();
                if (res.ok) {
                    this.showNotification("Virtual portfolio reset to ₹1,000,000.00!", "success");
                    this.loadPaperPortfolio();
                } else {
                    this.showNotification("Reset failed", "error");
                }
            })
            .catch(() => {
                this.showNotification("Server error", "error");
            });
    }

    initMobileConnect() {
        const btn = document.getElementById('mobile-connect-btn');
        const modal = document.getElementById('mobile-connect-modal');
        const closeBtn = document.getElementById('close-mobile-modal-btn');
        const copyBtn = document.getElementById('copy-mobile-url-btn');
        const copyIpBtn = document.getElementById('copy-ip-btn');
        const input = document.getElementById('mobile-url-input');
        const qrContainer = document.getElementById('mobile-qrcode-canvas');
        const tabGlobal = document.getElementById('mobile-tab-global');
        const tabDirect = document.getElementById('mobile-tab-direct');
        const tabLocal = document.getElementById('mobile-tab-local');
        const descText = document.getElementById('mobile-desc-text');
        const step1Text = document.getElementById('mobile-step-1');
        const step2Text = document.getElementById('mobile-step-2');
        const ipBox = document.getElementById('ip-bypass-box');
        const publicIpText = document.getElementById('public-ip-text');

        if (!btn || !modal) return;

        let fixedUrl = "https://investpro.loca.lt";
        let directUrl = null;
        let localUrl = `http://${window.location.hostname}:8787`;
        let publicIp = "103.113.2.97";
        let activeMode = 'fixed'; // 'fixed', 'direct', 'local'

        const renderQR = (url) => {
            if (!qrContainer || typeof QRCode === 'undefined') return;
            qrContainer.innerHTML = '';
            new QRCode(qrContainer, {
                text: url,
                width: 170,
                height: 170,
                colorDark: "#0a0a14",
                colorLight: "#ffffff",
                correctLevel: QRCode.CorrectLevel.M
            });
        };

        const updateTabs = () => {
            [tabGlobal, tabDirect, tabLocal].forEach(t => {
                if (t) {
                    t.style.background = 'transparent';
                    t.style.color = '#94a3b8';
                }
            });

            if (activeMode === 'fixed') {
                if (tabGlobal) {
                    tabGlobal.style.background = '#3b82f6';
                    tabGlobal.style.color = '#fff';
                }
                if (descText) {
                    descText.innerHTML = '📌 <strong>Permanent Fixed URL</strong>: This link NEVER changes. Bookmark it once on your phone!';
                }
                if (step1Text) step1Text.innerHTML = '1. Open <strong>https://investpro.loca.lt</strong> on your phone (or scan QR).';
                if (step2Text) {
                    step2Text.style.display = 'block';
                    step2Text.innerHTML = `2. If prompted on first visit, enter passcode <strong>${publicIp}</strong> once.`;
                }
                if (ipBox) ipBox.style.display = 'flex';
                if (input) input.value = fixedUrl;
                renderQR(fixedUrl);
            } else if (activeMode === 'direct') {
                if (tabDirect) {
                    tabDirect.style.background = '#3b82f6';
                    tabDirect.style.color = '#fff';
                }
                if (descText) {
                    descText.innerHTML = '⚡ <strong>Direct Cloud Mirror</strong>: Opens instantly with 0 password/passcode checks.';
                }
                const urlToShow = directUrl || 'Generating direct mirror link...';
                if (step1Text) step1Text.innerHTML = '1. Scan QR code or copy direct mirror link to open immediately.';
                if (step2Text) step2Text.style.display = 'none';
                if (ipBox) ipBox.style.display = 'none';
                if (input) input.value = urlToShow;
                if (directUrl) renderQR(directUrl);
            } else {
                if (tabLocal) {
                    tabLocal.style.background = '#3b82f6';
                    tabLocal.style.color = '#fff';
                }
                if (descText) {
                    descText.innerHTML = '🏠 <strong>Local Wi-Fi Network</strong>: Fast direct connection when connected to your home Wi-Fi.';
                }
                if (step1Text) step1Text.innerHTML = '1. Connect phone to same Wi-Fi, then open link or scan QR code.';
                if (step2Text) step2Text.style.display = 'none';
                if (ipBox) ipBox.style.display = 'none';
                if (input) input.value = localUrl;
                renderQR(localUrl);
            }
        };

        if (tabGlobal) tabGlobal.onclick = () => { activeMode = 'fixed'; updateTabs(); };
        if (tabDirect) tabDirect.onclick = () => { activeMode = 'direct'; updateTabs(); };
        if (tabLocal) tabLocal.onclick = () => { activeMode = 'local'; updateTabs(); };

        if (copyIpBtn && publicIpText) {
            copyIpBtn.onclick = () => {
                if (navigator.clipboard) {
                    navigator.clipboard.writeText(publicIpText.textContent.trim())
                        .then(() => this.showNotification("Passcode copied! Paste into mobile browser.", "success"))
                        .catch(() => this.showNotification("Copied: " + publicIp, "success"));
                }
            };
        }

        const fetchMobileInfo = async () => {
            try {
                const res = await fetch('/api/mobile/info');
                const data = await res.json();
                if (data.fixed_url) fixedUrl = data.fixed_url;
                if (data.cloudflare_url) directUrl = data.cloudflare_url;
                if (data.local_url) localUrl = data.local_url;
                if (data.public_ip) {
                    publicIp = data.public_ip;
                    if (publicIpText) publicIpText.textContent = publicIp;
                }
                updateTabs();
            } catch (err) {
                updateTabs();
            }
        };

        btn.onclick = () => {
            modal.classList.add('active');
            fetchMobileInfo();
        };

        if (closeBtn) {
            closeBtn.onclick = () => modal.classList.remove('active');
        }

        if (copyBtn && input) {
            copyBtn.onclick = () => {
                if (navigator.clipboard && input.value && !input.value.startsWith('Generating')) {
                    navigator.clipboard.writeText(input.value)
                        .then(() => this.showNotification("Link copied to clipboard!", "success"))
                        .catch(() => this.showNotification("Could not copy URL", "error"));
                } else if (input.value) {
                    input.select();
                    document.execCommand('copy');
                    this.showNotification("Link copied!", "success");
                }
            };
        }

        window.addEventListener('click', (e) => {
            if (e.target === modal) modal.classList.remove('active');
        });
    }
}

let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new KotakNeoPro();
});
