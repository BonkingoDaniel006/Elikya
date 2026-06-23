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




def go_up():
    head.direction = "up"

def go_down():
    head.direction = "down"

def go_left():
    head.direction = "left"

def go_right():
    head.direction = "right"

def move():
    if head.direction == "up":
        y = head.ycor()
        head.sety(y + 20)
    if head.direction == "down":
        y = head.ycor()
        head.sety(y - 20)
    if head.direction == "left":
        x = head.xcor()
        head.setx(x - 20)
    if head.direction == "right":
        x = head.xcor()
        head.setx(x + 20)


fen.listen()
fen.onkey(go_up, "Up")
fen.onkey(go_down, "Down")
fen.onkey(go_left, "Left")
fen.onkey(go_right, "Right")

while not game_over:
    fen.update()

    # Collision avec les murs
    if abs(head.xcor()) > 290 or abs(head.ycor()) > 290:
        game_over = True

    # Collision avec la nourriture
    if head.distance(food) < 20:
        score += 10
        food.goto(random.randint(-14,14) * 20, random.randint(-14,14) * 20)
        seg= turtle.Turtle()
        seg.shape("square")
        seg.color("red")
        seg.penup()
        segments.append(seg)

    # Déplacer les segments du corps en partant de la fin
    for i in range(len(segments)-1, 0, -1):
        segments[i].goto(segments[i-1].xcor(), segments[i-1].ycor())

    # Déplacer le premier segment à la position de la tête
    if len(segments) > 0:
        segments[0].goto(head.xcor(), head.ycor())

    move()

    # Collision avec le corps
    for segment in segments:
        if head.distance(segment) < 20:
            game_over = True
    
    time.sleep(DELAY)

# Affichage du message de fin de partie
if game_over:
    pen.goto(0, 0)
    pen.write(f"Game Over\nScore: {score}", align="center", font=("Courier", 24, "normal"))

# Garde la fenêtre ouverte après la fin du jeu
fen.mainloop()
