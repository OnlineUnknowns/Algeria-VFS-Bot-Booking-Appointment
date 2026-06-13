// src/web/app.js

document.addEventListener('DOMContentLoaded', () => {
    // --- State Variables ---
    let decryptedPassport = "";
    let activeSlots = [];
    let previousState = {
        is_running: false,
        slots_count: 0
    };
    
    // Track unique events for the timeline
    let timelineEvents = [];

    // --- DOM Elements ---
    const navButtons = document.querySelectorAll('.nav-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');
    const pageTitle = document.getElementById('page-title');
    const pageDescription = document.getElementById('page-description');
    
    // Status Indicators
    const agentPulse = document.getElementById('agent-pulse');
    const agentStatusText = document.getElementById('agent-status-text');
    const toggleMonitorBtn = document.getElementById('toggle-monitor-btn');
    const refreshDataBtn = document.getElementById('refresh-data-btn');
    
    // Stats cards
    const statEngineStatus = document.getElementById('stat-engine-status');
    const statSlotsCount = document.getElementById('stat-slots-count');
    const statLastChecked = document.getElementById('stat-last-checked');
    const statCountdown = document.getElementById('stat-countdown');
    const statCountdownBar = document.getElementById('stat-countdown-bar');
    const slotsCountBadge = document.getElementById('slots-count-badge');
    
    // Logs
    const logsTerminal = document.getElementById('logs-terminal');
    const clearLogsBtn = document.getElementById('clear-logs-btn');
    
    // Slots List
    const slotsListContainer = document.getElementById('slots-list-container');
    const slotsTimeline = document.getElementById('slots-timeline');
    
    // Settings Profile Form
    const settingsForm = document.getElementById('settings-form');
    const profFullname = document.getElementById('prof-fullname');
    const profPassport = document.getElementById('prof-passport');
    const profVisaType = document.getElementById('prof-visa-type');
    const profCountry = document.getElementById('prof-country');
    const profCity = document.getElementById('prof-city');
    const passportMaskedLbl = document.getElementById('passport-masked-lbl');
    const togglePassportBtn = document.getElementById('toggle-passport-btn');
    
    // Notification inputs
    const notifTgToken = document.getElementById('notif-tg-token');
    const notifTgChatid = document.getElementById('notif-tg-chatid');
    const notifEmailSender = document.getElementById('notif-email-sender');
    const notifEmailPass = document.getElementById('notif-email-pass');
    const notifEmailReceiver = document.getElementById('notif-email-receiver');
    const notifSmtpServer = document.getElementById('notif-smtp-server');
    const notifSmtpPort = document.getElementById('notif-smtp-port');
    const notifWebhook = document.getElementById('notif-webhook');
    
    // Tuning
    const schedInterval = document.getElementById('sched-interval');
    const schedJitter = document.getElementById('sched-jitter');
    const testNotificationsBtn = document.getElementById('test-notifications-btn');
    
    // Booking Helper Clipboard
    const copyFullname = document.getElementById('copy-fullname');
    const copyPassport = document.getElementById('copy-passport');
    const copyVisatype = document.getElementById('copy-visatype');
    const copyCity = document.getElementById('copy-city');
    const copyButtons = document.querySelectorAll('.btn-copy');
    const reloadBookingFrame = document.getElementById('reload-booking-frame');
    const bookingPortalIframe = document.getElementById('booking-portal-iframe');
    
    // Mock simulation
    const simAddDate = document.getElementById('sim-add-date');
    const simAddCity = document.getElementById('sim-add-city');
    const simAddBtn = document.getElementById('sim-add-btn');
    const simDeleteSelect = document.getElementById('sim-delete-select');
    const simDeleteBtn = document.getElementById('sim-delete-btn');
    const presetNewSlotBtn = document.getElementById('preset-new-slot-btn');
    const presetClearSlotsBtn = document.getElementById('preset-clear-slots-btn');
    const mockAvailabilityIframe = document.getElementById('mock-availability-iframe');
    
    // Document List Header
    const docVisaCategoryTitle = document.getElementById('doc-visa-category-title');
    const visaDocList = document.getElementById('visa-doc-list');

    // Toast Notification
    const toast = document.getElementById('app-toast');
    const toastIcon = document.getElementById('toast-icon');
    const toastMessage = document.getElementById('toast-message');

    // --- Tab Switching Logic ---
    const tabHeaders = {
        'dashboard': { title: 'Monitoring Dashboard', desc: 'Real-time visa appointment status and tracking overview.' },
        'profile': { title: 'Settings & Profile', desc: 'Manage your personal details securely, configure notification channels, and tune the check scheduler.' },
        'booking': { title: 'Manual Booking Assistant', desc: 'Autofill details and complete your appointment booking manually.' },
        'mock-portal': { title: 'Mock Visa Portal Simulation', desc: 'Test and debug slot scenarios against our local mockup portal.' },
        'docs': { title: 'Required Documents Checklist', desc: 'Check visa requirements and plan booking timeline.' }
    };

    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');
            
            // Activate button
            navButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Activate Pane
            tabPanes.forEach(pane => pane.classList.remove('active'));
            document.getElementById(`tab-${targetTab}`).classList.add('active');
            
            // Change Header Text
            if (tabHeaders[targetTab]) {
                pageTitle.textContent = tabHeaders[targetTab].title;
                pageDescription.textContent = tabHeaders[targetTab].desc;
            }

            // Sync iframe heights or reloads on view
            if (targetTab === 'booking') {
                reloadBookingIframe();
            } else if (targetTab === 'mock-portal') {
                reloadMockAvailabilityIframe();
                loadMockSlotsDropdown();
            }
        });
    });

    // --- Toast Helper ---
    function showToast(message, type = 'info') {
        toastMessage.textContent = message;
        toast.className = 'toast show';
        toast.classList.add(type);
        
        // Icon matching
        toastIcon.className = 'fa-solid toast-icon';
        if (type === 'success') toastIcon.classList.add('fa-circle-check');
        else if (type === 'error') toastIcon.classList.add('fa-circle-exclamation');
        else toastIcon.classList.add('fa-circle-info');
        
        setTimeout(() => {
            toast.classList.remove('show');
            // Allow transition to finish before cleaning class
            setTimeout(() => { toast.className = 'toast'; }, 300);
        }, 3000);
    }

    // --- Toggle Passport Visibility ---
    togglePassportBtn.addEventListener('click', () => {
        if (profPassport.type === 'password') {
            profPassport.type = 'text';
            togglePassportBtn.innerHTML = '<i class="fa-solid fa-eye-slash"></i>';
        } else {
            profPassport.type = 'password';
            togglePassportBtn.innerHTML = '<i class="fa-solid fa-eye"></i>';
        }
    });

    // --- Copy To Clipboard Helpers ---
    copyButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-target');
            const element = document.getElementById(targetId);
            
            if (element) {
                let textToCopy = element.textContent;
                
                // For passport number copy, if it is currently masked, copy the real decrypted one
                if (targetId === 'copy-passport' && decryptedPassport) {
                    textToCopy = decryptedPassport;
                }
                
                navigator.clipboard.writeText(textToCopy).then(() => {
                    // Visual feedback
                    const originalIcon = btn.innerHTML;
                    btn.innerHTML = '<i class="fa-solid fa-check" style="color: var(--success);"></i>';
                    btn.classList.add('copied');
                    showToast(`Copied: ${textToCopy.substring(0, 3)}...`, 'success');
                    
                    setTimeout(() => {
                        btn.innerHTML = originalIcon;
                        btn.classList.remove('copied');
                    }, 1500);
                }).catch(err => {
                    showToast('Failed to copy to clipboard', 'error');
                });
            }
        });
    });

    // --- Load Data from Server ---
    function loadProfileData() {
        fetch('/api/profile')
            .then(res => res.json())
            .then(data => {
                const profile = data.profiles.user1;
                
                // Fill profile forms
                profFullname.value = profile.full_name || '';
                profVisaType.value = profile.visa_type || 'tourism';
                profCountry.value = profile.country || 'Italy';
                profCity.value = profile.preferred_cities[0] || 'Algiers';
                
                // Mask label
                passportMaskedLbl.textContent = `Currently encrypted: ${profile.passport_number_masked || 'None'}`;
                profPassport.value = '********'; // placeholder password representation
                
                // Fill notification settings
                notifTgToken.value = data.notifications.telegram_bot_token || '';
                notifTgChatid.value = data.notifications.telegram_chat_id || '';
                notifEmailSender.value = data.notifications.email_sender || '';
                notifEmailReceiver.value = data.notifications.email_receiver || '';
                notifSmtpServer.value = data.notifications.email_smtp_server || 'smtp.gmail.com';
                notifSmtpPort.value = data.notifications.email_smtp_port || 587;
                notifWebhook.value = data.notifications.webhook_url || '';
                
                // Fill scheduler settings
                schedInterval.value = data.monitor.check_interval_normal_seconds || 60;
                schedJitter.value = data.monitor.jitter_max_seconds || 5;

                // Sync UI widgets with profiles
                copyFullname.textContent = profile.full_name || 'N/A';
                copyVisatype.textContent = (profile.visa_type || 'tourism').toUpperCase();
                copyCity.textContent = profile.preferred_cities[0] || 'N/A';
                
                // Update docs section category
                docVisaCategoryTitle.textContent = (profile.visa_type || 'tourism').toUpperCase();
                updateDocChecklist(profile.visa_type);
                
                // Fetch decrypted passport only for local Booking Assistant clipboard copies
                fetch('/api/profile/decrypt')
                    .then(r => r.json())
                    .then(decData => {
                        decryptedPassport = decData.user1 || "";
                        copyPassport.textContent = decryptedPassport ? maskString(decryptedPassport) : 'Not Configured';
                    });
            })
            .catch(err => {
                logger.error('Error loading configuration profiles:', err);
                showToast('Connection error with monitor API', 'error');
            });
    }

    function maskString(str) {
        if(str.length <= 4) return '****';
        return str.substring(0,2) + '*'.repeat(str.length-4) + str.substring(str.length-2);
    }

    function updateDocChecklist(visaType) {
        // Simple helper to load document specifications dynamically based on visa category
        const tourismDocs = [
            '<strong>Visa Application Form:</strong> Fully completed and signed.',
            '<strong>Passport:</strong> Original passport valid for at least 3 months after departure, with at least 2 empty pages.',
            '<strong>Passport Copy:</strong> Copy of the biometric details page and all stamped pages.',
            '<strong>Photos:</strong> Two recent passport-size biometric color photos on a white background.',
            '<strong>Travel Insurance:</strong> Valid for all Schengen countries covering medical/repatriation (min €30,000).',
            '<strong>Proof of Accommodation:</strong> Confirmed hotel reservation or hospitality host declaration.',
            '<strong>Proof of Financial Sufficiency:</strong> Bank statements for the last 3 months, proof of salary/income.',
            '<strong>Flight Booking:</strong> Confirmed round-trip flight reservation.'
        ];

        const studyDocs = [
            '<strong>Visa Application Form:</strong> Completed and signed.',
            '<strong>Passport:</strong> Valid for the duration of studies, with photo page copies.',
            '<strong>Letter of Acceptance:</strong> Official enrolment certificate from the host school/university in Italy.',
            '<strong>Educational Diplomas:</strong> Previous qualifications and transcripts.',
            '<strong>Financial Resources:</strong> Proof of scholarship, parents\' financial guarantee, or bank deposit (minimum €500/month).',
            '<strong>Travel Insurance:</strong> Medical insurance covering the first week/month of stay.',
            '<strong>Accommodation Proof:</strong> Rental contract, student residence letter, or university dorm booking.'
        ];

        const businessDocs = [
            '<strong>Visa Application Form:</strong> Completed and signed.',
            '<strong>Passport:</strong> Valid for 3+ months, with stamped copies.',
            '<strong>Invitation Letter:</strong> Official invite from the Italian company detailing business activities and travel dates.',
            '<strong>Company Letter:</strong> Letter from your employer confirming job role, salary, and purpose of travel.',
            '<strong>Commercial Register:</strong> Copy of company registration (for self-employed/business owners).',
            '<strong>Proof of Funding:</strong> Employer guarantee letter, bank statements, or expense coverage by invitee.',
            '<strong>Travel Insurance:</strong> Corporate travel coverage valid for Schengen.'
        ];

        let docs = tourismDocs;
        if(visaType === 'study') docs = studyDocs;
        else if(visaType === 'business') docs = businessDocs;

        visaDocList.innerHTML = docs.map(d => `<li><i class="fa-regular fa-square-check"></i> ${d}</li>`).join('');
    }

    // --- Save Settings ---
    settingsForm.addEventListener('submit', (e) => {
        e.preventDefault();
        
        const payload = {
            profile: {
                full_name: profFullname.value,
                visa_type: profVisaType.value,
                country: profCountry.value,
                city: profCity.value,
                // Only send passport number if user has edited the default masked entry
                passport_number: profPassport.value === '********' ? '' : profPassport.value
            },
            notifications: {
                telegram_bot_token: notifTgToken.value,
                telegram_chat_id: notifTgChatid.value,
                email_sender: notifEmailSender.value,
                email_password: notifEmailPass.value, // Blank is handled as unchanged on server
                email_receiver: notifEmailReceiver.value,
                email_smtp_server: notifSmtpServer.value,
                email_smtp_port: parseInt(notifSmtpPort.value) || 587,
                webhook_url: notifWebhook.value
            },
            monitor: {
                check_interval_normal_seconds: parseInt(schedInterval.value) || 60,
                jitter_max_seconds: parseInt(schedJitter.value) || 5
            }
        };

        fetch('/api/profile', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: json.stringify(payload)
        })
        .then(res => res.json())
        .then(data => {
            if (data.message) {
                showToast('Configurations saved successfully!', 'success');
                // Reload data to reset password fields
                loadProfileData();
            } else {
                showToast('Error saving configurations', 'error');
            }
        })
        .catch(err => {
            showToast('Failed to save configuration settings', 'error');
        });
    });

    // --- Test Notifications ---
    testNotificationsBtn.addEventListener('click', () => {
        testNotificationsBtn.disabled = true;
        const origContent = testNotificationsBtn.innerHTML;
        testNotificationsBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Dispatched test...';
        
        fetch('/api/profile/test_notification', { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                testNotificationsBtn.disabled = false;
                testNotificationsBtn.innerHTML = origContent;
                
                if (data.message) {
                    showToast(data.message, 'success');
                } else {
                    showToast(data.error || 'Test notification failed', 'error');
                }
            })
            .catch(err => {
                testNotificationsBtn.disabled = false;
                testNotificationsBtn.innerHTML = origContent;
                showToast('Network error sending test notification', 'error');
            });
    });

    // --- Toggle Monitoring Start/Stop ---
    toggleMonitorBtn.addEventListener('click', () => {
        const isRunning = toggleMonitorBtn.getAttribute('data-running') === 'true';
        const endpoint = isRunning ? '/api/monitor/stop' : '/api/monitor/start';
        
        toggleMonitorBtn.disabled = true;
        toggleMonitorBtn.innerHTML = isRunning ? 
            '<i class="fa-solid fa-spinner fa-spin"></i> Stopping...' : 
            '<i class="fa-solid fa-spinner fa-spin"></i> Starting...';

        fetch(endpoint, { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                toggleMonitorBtn.disabled = false;
                if(data.message) {
                    showToast(data.message, 'success');
                    pollStatus(); // Immediate status poll
                } else {
                    showToast(data.error || 'Failed to toggle monitor state', 'error');
                }
            })
            .catch(err => {
                toggleMonitorBtn.disabled = false;
                toggleMonitorBtn.innerHTML = isRunning ? '<i class="fa-solid fa-stop"></i> Stop Monitor' : '<i class="fa-solid fa-play"></i> Start Monitor';
                showToast('Failed to communicate with monitor thread', 'error');
            });
    });

    // --- Iframe reloading helpers ---
    function reloadBookingIframe() {
        if (bookingPortalIframe) {
            bookingPortalIframe.src = `/mock/vfs/italy/book?date=${activeSlots[0]?.date || ''}&city=${profCity.value || 'Algiers'}&r=${Math.random()}`;
        }
    }

    function reloadMockAvailabilityIframe() {
        if (mockAvailabilityIframe) {
            mockAvailabilityIframe.src = `/mock/vfs/italy/availability?city=${profCity.value || 'Algiers'}&r=${Math.random()}`;
        }
    }

    reloadBookingFrame.addEventListener('click', reloadBookingIframe);

    // --- Mock Slot Actions (Simulator) ---
    simAddBtn.addEventListener('click', () => {
        const date = simAddDate.value;
        const city = simAddCity.value;
        if(!date) {
            showToast('Please select a valid date to add', 'error');
            return;
        }

        fetch('/api/mock/slots', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: json.stringify({
                action: 'add',
                date: date,
                city: city,
                type: profVisaType.value
            })
        })
        .then(res => res.json())
        .then(data => {
            if(data.message) {
                showToast(data.message, 'success');
                reloadMockAvailabilityIframe();
                loadMockSlotsDropdown();
            } else {
                showToast(data.error || 'Failed to add mock slot', 'error');
            }
        })
        .catch(err => showToast('Network error modifying slots', 'error'));
    });

    simDeleteBtn.addEventListener('click', () => {
        const val = simDeleteSelect.value;
        if(!val) {
            showToast('Please select a slot to delete', 'error');
            return;
        }

        const [date, city] = val.split('|');

        fetch('/api/mock/slots', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: json.stringify({
                action: 'delete',
                date: date,
                city: city
            })
        })
        .then(res => res.json())
        .then(data => {
            if(data.message) {
                showToast(data.message, 'success');
                reloadMockAvailabilityIframe();
                loadMockSlotsDropdown();
            } else {
                showToast(data.error || 'Failed to remove mock slot', 'error');
            }
        })
        .catch(err => showToast('Network error deleting slot', 'error'));
    });

    presetNewSlotBtn.addEventListener('click', () => {
        // Simulate adding a slot 15 days out
        const futureDate = new Date();
        futureDate.setDate(futureDate.getDate() + 15);
        const dateStr = futureDate.toISOString().split('T')[0];

        fetch('/api/mock/slots', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: json.stringify({
                action: 'add',
                date: dateStr,
                city: 'Algiers',
                type: 'tourism'
            })
        })
        .then(res => res.json())
        .then(data => {
            if(data.message) {
                showToast(`Simulated slot for ${dateStr} successfully!`, 'success');
                reloadMockAvailabilityIframe();
                loadMockSlotsDropdown();
            } else {
                showToast(data.error || 'Preset failed', 'error');
            }
        });
    });

    presetClearSlotsBtn.addEventListener('click', () => {
        // Clear slots by fetching current and deleting them
        fetch('/mock/vfs/italy/availability')
            .then(res => res.text())
            .then(() => {
                // Fetch list of current slots from select items
                const promises = Array.from(simDeleteSelect.options)
                    .filter(opt => opt.value !== '')
                    .map(opt => {
                        const [date, city] = opt.value.split('|');
                        return fetch('/api/mock/slots', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: json.stringify({ action: 'delete', date, city })
                        });
                    });
                
                Promise.all(promises).then(() => {
                    showToast('Cleared all simulation slots.', 'info');
                    reloadMockAvailabilityIframe();
                    loadMockSlotsDropdown();
                });
            });
    });

    function loadMockSlotsDropdown() {
        // Retrieve slots data via raw html scraping or standard api load
        fetch('/mock/vfs/italy/availability')
            .then(res => res.text())
            .then(html => {
                // Quick parse using DOMParser
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const rows = doc.querySelectorAll('.slot-row');
                
                simDeleteSelect.innerHTML = '';
                
                if (rows.length > 0) {
                    rows.forEach(row => {
                        const cols = row.querySelectorAll('td');
                        const date = cols[0].textContent.trim();
                        const city = cols[1].textContent.trim();
                        
                        const option = document.createElement('option');
                        option.value = `${date}|${city}`;
                        option.textContent = `${date} (${city})`;
                        simDeleteSelect.appendChild(option);
                    });
                } else {
                    const option = document.createElement('option');
                    option.value = '';
                    option.textContent = '-- No slots active --';
                    simDeleteSelect.appendChild(option);
                }
            });
    }

    // --- Status and Logs Polling ---
    function pollStatus() {
        fetch('/api/status')
            .then(res => res.json())
            .then(state => {
                // Update Pulse
                agentPulse.className = `pulse-dot ${state.status}`;
                agentStatusText.textContent = state.status.replace('_', ' ').toUpperCase();
                
                // Toggle Button State
                if (state.is_running) {
                    toggleMonitorBtn.setAttribute('data-running', 'true');
                    toggleMonitorBtn.className = 'btn btn-danger btn-sm btn-block';
                    toggleMonitorBtn.innerHTML = '<i class="fa-solid fa-stop"></i> Stop Monitor';
                    statEngineStatus.textContent = 'Active Monitoring';
                    statEngineStatus.className = 'stat-value text-success';
                } else {
                    toggleMonitorBtn.setAttribute('data-running', 'false');
                    toggleMonitorBtn.className = 'btn btn-primary btn-sm btn-block';
                    toggleMonitorBtn.innerHTML = '<i class="fa-solid fa-play"></i> Start Monitor';
                    statEngineStatus.textContent = 'Inactive (Idle)';
                    statEngineStatus.className = 'stat-value text-muted';
                }
                
                // Check if engine state changed to alert you
                if (state.is_running !== previousState.is_running) {
                    const action = state.is_running ? 'started' : 'stopped';
                    addTimelineEvent('monitor', `Agent monitoring daemon was ${action}.`);
                }
                
                // Check if slots count changed
                const currentSlotsCount = state.slots_found.length;
                if (state.is_running && currentSlotsCount > previousState.slots_count) {
                    // New slots detected!
                    showToast(`Alert: ${currentSlotsCount - previousState.slots_count} new slot(s) found!`, 'success');
                    addTimelineEvent('added', `Detected ${currentSlotsCount - previousState.slots_count} new slot openings.`);
                } else if (state.is_running && currentSlotsCount < previousState.slots_count) {
                    addTimelineEvent('removed', `Slot booked or canceled by system.`);
                }
                
                // Track slots array
                activeSlots = state.slots_found;
                
                // Update Counts
                statSlotsCount.textContent = currentSlotsCount;
                slotsCountBadge.textContent = `${currentSlotsCount} Found`;
                
                // Update Timestamps
                statLastChecked.textContent = state.last_checked || 'Never';
                
                // Countdown representation
                if (state.is_running) {
                    statCountdown.textContent = `${state.next_check_in_seconds} s`;
                    // Assume normal interval is around 60 seconds
                    const normInterval = parseInt(schedInterval.value) || 60;
                    const pct = Math.max(0, Math.min(100, (state.next_check_in_seconds / normInterval) * 100));
                    statCountdownBar.style.width = `${pct}%`;
                } else {
                    statCountdown.textContent = '--';
                    statCountdownBar.style.width = '0%';
                }
                
                // Draw Slots List
                renderSlotsList(state.slots_found);
                
                // Keep history trackers
                previousState.is_running = state.is_running;
                previousState.slots_count = currentSlotsCount;
            })
            .catch(err => {
                console.error('API polling error:', err);
                agentPulse.className = 'pulse-dot not_available';
                agentStatusText.textContent = 'API ERROR';
                statEngineStatus.textContent = 'Server Offline';
            });
    }

    function renderSlotsList(slots) {
        slotsListContainer.innerHTML = '';
        if (slots.length > 0) {
            slots.forEach(slot => {
                const item = document.createElement('div');
                item.className = 'slot-item';
                item.innerHTML = `
                    <div class="slot-meta">
                        <span class="slot-date"><i class="fa-solid fa-calendar-check"></i> ${slot.date}</span>
                        <span class="slot-details">${slot.country} visa center at VFS ${slot.city} (${slot.type.toUpperCase()})</span>
                    </div>
                    <button class="btn btn-primary btn-xs" onclick="document.querySelector('[data-tab=booking]').click();">
                        <i class="fa-solid fa-paper-plane"></i> Book
                    </button>
                `;
                slotsListContainer.appendChild(item);
            });
        } else {
            slotsListContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fa-solid fa-calendar-xmark"></i>
                    <p>No active slots detected. Make sure the Monitor Engine is running and check the Mock Visa Center to add slots.</p>
                </div>
            `;
        }
    }

    function pollLogs() {
        fetch('/api/logs')
            .then(res => res.json())
            .then(data => {
                const terminal = logsTerminal;
                const isScrolledToBottom = terminal.scrollHeight - terminal.clientHeight <= terminal.scrollTop + 40;
                
                terminal.textContent = data.logs || 'Console output empty.';
                
                if (isScrolledToBottom) {
                    terminal.scrollTop = terminal.scrollHeight;
                }
            })
            .catch(err => {
                logsTerminal.textContent = 'Error fetching active agent activity logs.';
            });
    }

    clearLogsBtn.addEventListener('click', () => {
        logsTerminal.textContent = 'Clear view. Waiting for next polling update...';
    });

    refreshDataBtn.addEventListener('click', () => {
        showToast('Refreshing dashboard metrics...', 'info');
        pollStatus();
        pollLogs();
    });

    // Timeline event tracker
    function addTimelineEvent(type, message) {
        const timeStr = new Date().toLocaleTimeString();
        timelineEvents.unshift({ type, message, time: timeStr });
        if(timelineEvents.length > 5) timelineEvents.pop(); // Keep last 5
        
        renderTimeline();
    }

    function renderTimeline() {
        slotsTimeline.innerHTML = '';
        if (timelineEvents.length > 0) {
            timelineEvents.forEach(evt => {
                const li = document.createElement('li');
                li.className = `timeline-item ${evt.type}`;
                li.innerHTML = `
                    <span class="timeline-content">${evt.message}</span>
                    <span class="timeline-time">${evt.time}</span>
                `;
                slotsTimeline.appendChild(li);
            });
        } else {
            slotsTimeline.innerHTML = '<li class="timeline-empty">No activity events recorded yet.</li>';
        }
    }

    // --- Bootstrapping Operations ---
    loadProfileData();
    pollStatus();
    pollLogs();
    loadMockSlotsDropdown();
    
    // Setup recurring intervals
    setInterval(pollStatus, 2000); // Poll status every 2s
    setInterval(pollLogs, 4000);   // Poll logs every 4s
});
