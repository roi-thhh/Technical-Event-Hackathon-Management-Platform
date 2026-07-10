import os
import re

files_to_patch = [
    r"d:\project heheh\static\participant.html",
    r"d:\project heheh\static\judge.html",
    r"d:\project heheh\static\admin.html"
]

JS_LOGIC = """
// Tab switching logic
document.addEventListener('DOMContentLoaded', () => {
    const navLinks = document.querySelectorAll('aside nav a, nav.md\\\\:hidden a');
    const mainCanvas = document.querySelector('main');
    
    // Create tab contents if they don't exist
    const tabs = ['teams', 'submissions', 'schedule', 'settings', 'drafts', 'events', 'profile', 'help'];
    
    // Wrap existing content in a dashboard tab
    const existingContent = Array.from(mainCanvas.children).filter(el => el.tagName !== 'SCRIPT');
    const dashboardTab = document.createElement('div');
    dashboardTab.id = 'tab-dashboard';
    dashboardTab.className = 'tab-content';
    existingContent.forEach(el => dashboardTab.appendChild(el));
    mainCanvas.prepend(dashboardTab);

    tabs.forEach(tab => {
        const tabEl = document.createElement('div');
        tabEl.id = `tab-${tab}`;
        tabEl.className = 'tab-content hidden relative z-10 min-h-full flex flex-col items-center justify-center p-8';
        tabEl.innerHTML = `
            <div class="text-center bg-surface-dim/80 backdrop-blur-3xl rounded-[2rem] border-2 border-surface-container-high p-12 max-w-lg w-full shadow-2xl">
                <span class="material-symbols-outlined text-6xl text-primary-fixed mb-4">construction</span>
                <h2 class="font-headline-lg text-on-surface mb-2 capitalize">${tab}</h2>
                <p class="text-on-surface-variant font-body-md">This section is currently under development. Please check back later.</p>
            </div>
        `;
        mainCanvas.appendChild(tabEl);
    });

    const activeClassDesktop = 'bg-primary-fixed text-on-primary-fixed rounded-full font-bold px-4 py-3 mx-2 flex items-center gap-3 translate-x-1 duration-200'.split(' ');
    const inactiveClassDesktop = 'text-on-surface-variant hover:text-secondary-fixed px-4 py-3 mx-2 flex items-center gap-3 hover:bg-surface-variant/50 rounded-full transition-all'.split(' ');
    
    const activeClassMobile = 'flex flex-col items-center justify-center bg-secondary-fixed text-on-secondary-fixed rounded-full p-2 scale-110 transition-all'.split(' ');
    const inactiveClassMobile = 'flex flex-col items-center justify-center text-on-surface-variant p-2 hover:text-primary-fixed'.split(' ');

    function switchTab(tabName) {
        document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
        const target = document.getElementById(`tab-${tabName}`);
        if (target) {
            target.classList.remove('hidden');
        } else {
            document.getElementById('tab-dashboard').classList.remove('hidden');
        }

        navLinks.forEach(link => {
            const linkText = link.textContent.toLowerCase();
            const isMatch = linkText.includes(tabName) || (tabName === 'dashboard' && linkText.includes('home'));
            
            const isDesktop = link.closest('aside') !== null;
            
            if (isDesktop) {
                if (isMatch) {
                    link.classList.remove(...inactiveClassDesktop);
                    link.classList.add(...activeClassDesktop);
                    // fix icon fill
                    const icon = link.querySelector('.material-symbols-outlined');
                    if (icon) icon.style.fontVariationSettings = "'FILL' 1";
                } else {
                    link.classList.remove(...activeClassDesktop);
                    link.classList.add(...inactiveClassDesktop);
                    const icon = link.querySelector('.material-symbols-outlined');
                    if (icon) icon.style.fontVariationSettings = "normal";
                }
            } else {
                if (isMatch) {
                    link.classList.remove(...inactiveClassMobile);
                    link.classList.add(...activeClassMobile);
                    const icon = link.querySelector('.material-symbols-outlined');
                    if (icon) icon.style.fontVariationSettings = "'FILL' 1";
                } else {
                    link.classList.remove(...activeClassMobile);
                    link.classList.add(...inactiveClassMobile);
                    const icon = link.querySelector('.material-symbols-outlined');
                    if (icon) icon.style.fontVariationSettings = "normal";
                }
            }
        });
    }

    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            if (link.id === 'logout-link') return;
            e.preventDefault();
            const linkText = link.textContent.trim().toLowerCase();
            
            let tabName = 'dashboard';
            if (linkText.includes('teams')) tabName = 'teams';
            else if (linkText.includes('submissions')) tabName = 'submissions';
            else if (linkText.includes('schedule') || linkText.includes('events')) tabName = 'schedule';
            else if (linkText.includes('settings')) tabName = 'settings';
            else if (linkText.includes('drafts')) tabName = 'drafts';
            else if (linkText.includes('profile')) tabName = 'profile';
            else if (linkText.includes('help')) tabName = 'help';
            
            switchTab(tabName);
        });
    });

    // Handle new project button
    const newProjectBtn = document.querySelector('button');
    if (newProjectBtn && newProjectBtn.textContent.toLowerCase().includes('new project')) {
        newProjectBtn.addEventListener('click', () => {
            switchTab('drafts'); // or some other tab
        });
    }
});
"""

for filepath in files_to_patch:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if "Tab switching logic" in content:
        continue # already patched
    
    # insert before </body>
    content = content.replace("</body>", f"<script>\n{JS_LOGIC}\n</script>\n</body>")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print("Patch applied to all dashboards!")
