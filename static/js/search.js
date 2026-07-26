document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('search-input');
    const productCards = document.querySelectorAll('.product-card');

    if (searchInput) {
        searchInput.addEventListener('input', () => {
            const searchTerm = searchInput.value.toLowerCase().trim();

            productCards.forEach(card => {
                const productNameElement = card.querySelector('.product-info h3');
                const shopNameElement = card.querySelector('.shop-name');

                const productName = productNameElement ? productNameElement.textContent.toLowerCase() : '';
                const shopName = shopNameElement ? shopNameElement.textContent.toLowerCase() : '';

                // La carte est visible si le terme de recherche est trouvé dans le nom du produit OU le nom de la boutique
                if (productName.includes(searchTerm) || shopName.includes(searchTerm)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }
});