@app.route("/produit/<int:product_id>")
@jwt_required(optional=True)
def vendeur_details(product_id):
    user_id = get_jwt_identity()
    user = get_jwt() if user_id else None

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.*, b.nom_boutique AS seller_name
        FROM products p
        JOIN buyers b ON p.seller_id = b.id
        WHERE p.id = %s
    """, (product_id,))
    produit = cursor.fetchone()
    added = request.args.get("added")
    error = request.args.get("error")
    cursor.close()
    conn.close()

    if not produit:
        return "Produit introuvable", 404

    return render_template(
        "detail_produit.html",
        produit=produit,
        panier="Produit ajouté au panier !" if added else None,
        error_msg="Veuillez vous connecter pour ajouter au panier." if error else None,
        user=user
    )

@app.route("/add_product/<int:product_id>", methods=["POST"])
@jwt_required(optional=True)
def add_product(product_id):
    buyer_id = get_jwt_identity()
    
    # Si l'utilisateur n'est pas connecté, le ramener sur la page produit avec une erreur
    if not buyer_id:
        return redirect(url_for("vendeur_details", product_id=product_id, error=1))
        
    claims = get_jwt()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.*, b.nom_boutique AS seller_name
        FROM products p
        JOIN buyers b ON p.seller_id = b.id
        WHERE p.id = %s
    """, (product_id,))
    produit = cursor.fetchone()

    if not produit:
        cursor.close()
        conn.close()
        return "Produit introuvable", 404

    try:
        quantite = int(request.form.get("quantite", 1))
    except ValueError:
        quantite = 1

    if quantite <= 0:
        cursor.close()
        conn.close()
        return "Quantité invalide", 400

    prix_total = quantite * float(produit["price"])

    cursor.execute("""
        INSERT INTO panier2 (
            buyer_id, buyer_first_name, buyer_last_name,
            product_id, product_name, product_price, product_description, product_image_url,
            seller_id, seller_name, quantite, prix_total
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        buyer_id, claims.get("first_name"), claims.get("last_name"),
        produit["id"], produit["name"], produit["price"], produit["description"], produit["image_url"],
        produit["seller_id"], produit["seller_name"], quantite, prix_total
    ))
    

    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for("vendeur_details", product_id=product_id, added=1))





<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Profil Acheteur - e-MiniShopRDC</title>
<link rel="stylesheet" href="{{ url_for('static', filename='profil_vendeur.css') }}">
<link rel="stylesheet" href="{{ url_for('static', filename='fil_actu.css') }}">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body>

<header>
  <div class="header-top">
    <div class="logo-container {{ 'active-home' if request.endpoint == 'auth.index' }}">
      <img src="{{ url_for('static', filename='profils/logo.png') }}" alt="Logo" style="height: 50px;">
    </div>
    <div class="search-bar">
      <input type="text" placeholder="Rechercher un produit..." style="width:100%; padding:8px; border-radius:20px; border:none; box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);">
    </div>

    <label for="menu-toggle" class="hamburger">☰</label>
  </div>

  <input type="checkbox" id="menu-toggle" class="menu-cb">

  <nav class="nav-menu">
    <ul class="nav-list">
      <li><a href="{{ url_for('auth.index') }}" class="nav-item">
        <i class="fa-solid fa-house nav-icon"></i> Accueil
      </a></li>
      <li><a href="{{ url_for('notification.notifications') }}" class="nav-item">
        <i class="fa-solid fa-bell nav-icon"></i> Notifications
      </a></li>
      <li><a href="{{ url_for('panier.panier') }}" class="nav-item">
        <i class="fa-solid fa-cart-shopping nav-icon"></i> Panier
      </a></li>
      <li><a href="{{ url_for('buyer.profil_acheteur') }}" class="nav-item {{ 'active' if request.endpoint == 'buyer.profil_acheteur' }}">
        <div class="profile">
          {% if user and user.get('profil') %}
            <img src="{{ user['profil'] }}" class="profil-img">
          {% else %}
            <img src="{{ url_for('static', filename='profils/default_profile.png') }}" class="profil-img">
          {% endif %}
        </div> Profil
      </a></li>
    </ul>
  </nav>
</header>

<nav class="profile-tabs">
  <a href="{{ url_for('buyer.profil_acheteur') }}" class="tab-item {{ 'active' if request.endpoint == 'buyer.profil_acheteur' }}">
    <i class="fa-solid fa-circle-user"></i> Profil Acheteur
  </a>
  <a href="{{ url_for('seller.seller_dashboard') }}" class="tab-item {{ 'active' if request.endpoint == 'seller.seller_dashboard' }}">
    <i class="fa-solid fa-shop"></i> Profil Vendeur
  </a>
</nav>

<main>

  {% with messages = get_flashed_messages(with_categories=true) %}
  {% if messages %}
    <div style="max-width: 1000px; margin: 20px auto; padding: 0 20px;">
      {% for category, message in messages %}
        <div style="padding: 15px; border-radius: 10px; margin-bottom: 10px; font-weight: bold; text-align: center;
                    background-color: {{ '#ff4081' if category == 'danger' else '#c8b6ff' }}; color: white;">
          {{ message }}
        </div>
      {% endfor %}
    </div>
  {% endif %}
  {% endwith %}

  <div class="shop-header">
    <img src="{{ user.get('profil') or url_for('static', filename='profils/default_profile.png') }}" alt="Profil Acheteur">
    <div class="shop-info">
      <h2 class="username"> {{ user.get('prenom', '') }} {{ user.get('nom', '') }} {{ user.get('postnom', '') or '' }}</h2>
      <p>Email : {{ user.get('email', '') }}</p>
      {% if user.get('adresse') %}
        <p style="font-size: 0.9rem; color: #666; margin-top: 5px;"><i class="fa-solid fa-location-dot"></i> {{ user.get('adresse') }}</p>
      {% endif %}
      <br>
      <button onclick="showVerifyPasswordModal()" class="subscribe-btn" style="cursor: pointer; border: none;">Modifier le profil</button>
    </div>
  </div>
  
  <div class="section">
    <h2>Boutiques Abonnées</h2>
    <div class="subscriptions-grid">
      <div class="card">
        <h3>KasaTech</h3>
        <p>Spécialiste en consoles gaming.</p>
      </div>
      <div class="card">
        <h3>TechWorld</h3>
        <p>Accessoires et gadgets tech.</p>
      </div>
    </div>
  </div>

  <div class="section" onclick="window.location.href='/avis_commande'">
    <h2>Laisser un avis sur une commande</h2>
    <div class="comments-grid">
      <div class="card">
        <p>“Intéressé par la PS5 Pro, super boutique !”</p>
        <p><strong>KasaTech</strong></p>
      </div>
      <div class="card">
        <p>“Le casque gaming est excellent, livraison rapide.”</p>
        <p><strong>KasaTech</strong></p>
      </div>
    </div>
  </div>

  <!-- MODALE 1 : Vérification initiale du mot de passe -->
  <div id="verifyPasswordModal" class="modal-overlay" style="display: none;">
      <div class="modal-box">
          <h3 style="color: #4b0082; margin-top: 0;"><i class="fa-solid fa-lock"></i> Vérification de sécurité</h3>
          <p style="color: #666; font-size: 0.9rem; margin-bottom: 20px;">Veuillez saisir votre mot de passe actuel pour accéder à la modification de votre profil.</p>
          
          <div id="verifyStep">
              <input type="password" id="currentPasswordVerify" placeholder="Mot de passe actuel" class="modal-input" required>
          </div>

          <div class="modal-actions">
              <button type="button" onclick="closeVerifyModal()" class="btn-modal btn-modal-cancel">Annuler</button>
              <button type="button" onclick="handleVerifyPassword()" class="btn-modal btn-modal-confirm">
                  Confirmer
              </button>
          </div>
      </div>
  </div>

  <!-- MODALE 2 : Formulaire effectif de modification du Profil -->
  <div id="editProfileModal" class="modal-overlay" style="display: none;">
      <div class="modal-box">
          <h3 style="color: #4b0082; margin-top: 0;">Modifier mes informations</h3>
          <form id="profileForm" method="POST" action="{{ url_for('buyer.profil_acheteur') }}" enctype="multipart/form-data" style="margin-top:20px;">
              <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
              
              <!-- On renvoie de manière cachée le mot de passe vérifié pour validation finale back-end -->
              <input type="hidden" name="current_password" id="hiddenCurrentPassword">
              
              <div id="infoStep">
                  <input type="text" name="prenom" id="editPrenom" value="{{ user.prenom }}" placeholder="Prénom" class="modal-input" required>
                  <input type="text" name="nom" id="editNom" value="{{ user.nom }}" placeholder="Nom" class="modal-input" required>
                  <input type="text" name="postnom" id="editPostnom" value="{{ user.postnom or '' }}" placeholder="Postnom (Optionnel)" class="modal-input">
                  <input type="text" name="adresse" id="editAdresse" value="{{ user.adresse or '' }}" placeholder="Adresse (ex: 24 rue des bajeux)" class="modal-input">
                  
                  <!-- NOUVEAU CHAMP : Changement de mot de passe facultatif -->
                  <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                  <label style="display: block; text-align: left; margin-left: 10px; font-size: 0.8rem; color: #4b0082; font-weight: bold; margin-bottom: 5px;">
                     <i class="fa-solid fa-key"></i> Changer de mot de passe (Optionnel) :
                  </label>
                  <input type="password" name="new_password" id="editNewPassword" placeholder="Nouveau mot de passe" class="modal-input">
                  
                  <label style="display: block; text-align: left; margin-left: 10px; font-size: 0.8rem; color: #666; margin-top: 15px;">Changer la photo de profil :</label>
                  <input type="file" name="profil" id="editProfilImg" class="modal-input" accept="image/*">
              </div>

              <div class="modal-actions">
                  <button type="button" onclick="closeEditProfileModal()" class="btn-modal btn-modal-cancel">Annuler</button>
                  <button type="submit" class="btn-modal btn-modal-confirm">
                      Enregistrer les modifications
                  </button>
              </div>
          </form>
      </div>
  </div>

</main>

<script>
// --- LOGIQUE MODALE 1 : VERIFICATION DE SECURITE ---
function showVerifyPasswordModal() {
    document.getElementById('verifyPasswordModal').style.display = 'block';
    setTimeout(() => document.getElementById('currentPasswordVerify').focus(), 100);
}

function handleVerifyPassword() {
    const passwordInput = document.getElementById('currentPasswordVerify').value;
    
    if (passwordInput.trim() === "") {
        alert("Veuillez entrer votre mot de passe.");
        return;
    }
    
    // Transférer le mot de passe tapé vers le formulaire caché de la Modale 2
    document.getElementById('hiddenCurrentPassword').value = passwordInput;
    
    // Fermer la modale de sécurité et ouvrir directement le formulaire
    document.getElementById('verifyPasswordModal').style.display = 'none';
    showEditProfileModal();
}

function closeVerifyModal() {
    document.getElementById('verifyPasswordModal').style.display = 'none';
    document.getElementById('currentPasswordVerify').value = '';
}


// --- LOGIQUE MODALE 2 : FORMULAIRE DE MODIFICATION ---
function showEditProfileModal() {
    document.getElementById('editProfileModal').style.display = 'block';
}

function closeEditProfileModal() {
    document.getElementById('editProfileModal').style.display = 'none';
    // Clean des champs sensibles
    document.getElementById('currentPasswordVerify').value = '';
    document.getElementById('hiddenCurrentPassword').value = '';
    document.getElementById('editNewPassword').value = '';
}
</script>

<footer><a href="{{ url_for('auth.deconnexion') }}" class="secondary">Se déconnecter</a></footer>

</body>
</html>