document.addEventListener('DOMContentLoaded', function() {
    // Cible tous les champs de recherche ayant la classe 'global-search-input'
    const searchInputs = document.querySelectorAll('.global-search-input');

    searchInputs.forEach(input => {
        input.addEventListener('keydown', function(event) {
            // Vérifie si la touche pressée est "Entrée"
            if (event.key === 'Enter') {
                event.preventDefault(); // Empêche le comportement par défaut (ex: soumission de formulaire)

                const query = input.value.trim();

                // Ne redirige que si la recherche n'est pas vide
                if (query) {
                    // Construit l'URL de recherche et redirige l'utilisateur
                    window.location.href = `/search?q=${encodeURIComponent(query)}`;
                }
            }
        });
    });
});