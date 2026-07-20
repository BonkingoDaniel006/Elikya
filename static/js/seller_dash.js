document.addEventListener('DOMContentLoaded', function () {
  // --- GESTION DE LA SIDEBAR MOBILE (MENU HAMBURGER) ---
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('overlay');
  // On sélectionne tous les boutons qui peuvent ouvrir/fermer la sidebar
  const toggleButtons = document.querySelectorAll('[data-action="toggle-sidebar"]');

  if (sidebar && overlay && toggleButtons.length) {
    toggleButtons.forEach(button => {
      button.addEventListener('click', (e) => {
        e.stopPropagation(); // Empêche le clic de se propager
        sidebar.classList.toggle('open');
        overlay.classList.toggle('hidden');
      });
    });
  }

  // --- GESTION DES ONGLETS (TABS) ---
  const navButtons = document.querySelectorAll('.nav-btn');
  const tabPanels = document.querySelectorAll('.tab-panel');
  const pageTitle = document.getElementById('page-title');

  navButtons.forEach(button => {
    button.addEventListener('click', () => {
      const tabName = button.dataset.tab;
      if (!tabName) return; // Ignore les boutons sans l'attribut data-tab

      // Met à jour les boutons de navigation
      navButtons.forEach(btn => {
        if (btn.dataset.tab) {
          btn.classList.toggle('active', btn.dataset.tab === tabName);
        }
      });

      // Affiche le bon panneau de contenu
      tabPanels.forEach(panel => {
        panel.classList.toggle('active', panel.id === `tab-${tabName}`);
      });

      // Met à jour le titre de la page
      if (pageTitle) {
        const activeNavBtn = document.querySelector(`.nav-btn[data-tab="${tabName}"]`);
        if (activeNavBtn) pageTitle.textContent = activeNavBtn.textContent.trim();
      }

      // Ferme la sidebar en mobile après avoir cliqué sur un onglet
      if (window.innerWidth < 1024 && sidebar.classList.contains('open')) {
        sidebar.classList.remove('open');
        overlay.classList.add('hidden');
      }
    });
  });

  // --- MISE À JOUR DE LA DATE ---
  const todayDateEl = document.getElementById('today-date');
  if (todayDateEl) {
    todayDateEl.textContent = new Date().toLocaleDateString('fr-FR', {
      weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
    });
  }
});