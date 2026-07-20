from flask import Blueprint, redirect, url_for, flash
from flask_login import login_required, current_user
from notifications.models import Notification

notifications_bp = Blueprint('notification', __name__)

@notifications_bp.route("/notifications/mark-read/<int:notification_id>", methods=['POST'])
@login_required
def mark_as_read(notification_id):
    """Marque une notification comme lue."""
    success = Notification.mark_as_read(notification_id, current_user.id)
    if not success:
        flash("Impossible de trouver cette notification.", "danger")
    # Redirige vers le dashboard, l'onglet sera géré par le JS
    return redirect(url_for('seller.seller_dashboard', tab='notifications'))

@notifications_bp.route("/notifications/mark-all-read", methods=['POST'])
@login_required
def mark_all_as_read():
    """Marque toutes les notifications comme lues."""
    Notification.mark_all_as_read(current_user.id)
    flash("Toutes les notifications ont été marquées comme lues.", "success")
    return redirect(url_for('seller.seller_dashboard', tab='notifications'))

@notifications_bp.route("/notifications/delete/<int:notification_id>", methods=['POST'])
@login_required
def delete_notification(notification_id):
    """Supprime une notification."""
    success = Notification.delete(notification_id, current_user.id)
    if success:
        flash("La notification a été supprimée.", "success")
    else:
        flash("Impossible de supprimer cette notification.", "danger")
    return redirect(url_for('seller.seller_dashboard', tab='notifications'))

# Exemple de création de notification (à placer là où un événement se produit)
# Par exemple, dans la route qui valide une commande :
# from notifications.models import Notification
# Notification.create(user_id=vendeur_id, type='order', title='Nouvelle commande !', content='Vous avez reçu une nouvelle commande pour le produit X.')