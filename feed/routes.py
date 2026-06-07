from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from feed.models import Produits

feed_bp = Blueprint('feed', __name__)

@feed_bp.route("/produit/<int:product_id>")
def vendeur_details(product_id):
    conn = Produits.get_db_connection()
    cursor = conn.cursor(dictionary=True)
    # Utilisation des noms de tables cohérents avec ton schéma (produits et users)
    cursor.execute("""
        SELECT p.*, u.nom_boutique AS seller_name
        FROM produits p
        JOIN users u ON p.seller_id = u.id
        WHERE p.id = %s
    """, (product_id,))
    produit = cursor.fetchone()
    cursor.close()
    conn.close()

    if not produit:
        return "Produit introuvable", 404

    return render_template("detail_produit.html", produit=produit)
