import os
IS_UNIT = os.getenv("UNIT_TEST") == "1"

from flask import Flask, jsonify, request, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import (
    JWTManager, create_access_token, get_jwt, jwt_required, get_jwt_identity
)
from flask_cors import CORS
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import timedelta, datetime, date
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey,CheckConstraint, UniqueConstraint, Index
import requests
import ast
from metrics import metrics_bp
app = Flask(__name__)

app.register_blueprint(metrics_bp)

CORS(app, resources={r"/*": {
    "origins": ["http://localhost:4200", "http://localhost:8100","http://localhost:29902"],
    "allow_headers": ["Content-Type", "Authorization"],
    "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
}})
# DB config (choose one of the two blocks)
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "postgresql+psycopg2://postgres:postgres123@localhost:5432/gestiondonsdb?client_encoding=utf8"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = '473f7e8c82ad4f2aae3704006097205f'
app.config["JWT_ACCESS_TOKEN_EXPIRES"]  = timedelta(minutes=20)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=14)
app.config["JWT_HEADER_TYPE"] = "Bearer"
# Files & mail (don’t commit real secrets)
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'donbyuib@gmail.com'
app.config['MAIL_PASSWORD'] = 'sewi joqt yjhw fqqu'   
app.config['MAIL_DEFAULT_SENDER'] = 'DonByUIB <admin@donbyuib.tn>'

mail = Mail(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)
revoked_tokens = set()


# ------------------- MODELS -------------------

# User Model (Admin or Donator or Association)
class User(db.Model):
    """ General User model for Admin, Donator, and Associations """
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'donator'
    
    # Donator-specific attributes
    nom_complet = db.Column(db.String(80), nullable=True)  # Only for donators
    telephone = db.Column(db.String(15), nullable=True)    # Only for donators
    token = db.Column(db.String(255), nullable=True)       # JWT token storage if needed
    cin = db.Column(db.String(8), unique=True, nullable=True)
    cin_recto = db.Column(db.String(255), nullable=True)   
    cin_verso = db.Column(db.String(255), nullable=True) 
    date_naissance = db.Column(db.Date, nullable=True)
    adresse = db.Column(db.String(255), nullable=True)
    profession = db.Column(db.String(100), nullable=True)

 
    is_verified = db.Column(db.Boolean, default=False)

# OTP
    otp_code = db.Column(db.String(6), nullable=True)
    otp_expires_at = db.Column(db.DateTime, nullable=True)
    otp_attempts = db.Column(db.Integer, default=0)     # sécurité (limiter tentatives)
    otp_last_sent = db.Column(db.DateTime, nullable=True)  # anti-spam resend

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# class enum de type association
import enum
from sqlalchemy import Enum as SqlEnum

class TypeAssociationEnum(enum.Enum):
    HUMANITAIRE = "humanitaire"
    EDUCATION = "éducation"
    SANTE = "santé"
    ENVIRONNEMENT = "environnement"
    AUTRE = "autre"

class Gouvernorat(db.Model):
    __tablename__ = 'gouvernorat'
    id = db.Column(db.Integer, primary_key=True)
    nomGouvernorat = db.Column(db.String(100), nullable=False, unique=True)

    associations = db.relationship("Association", backref="gouvernorat", lazy=True)


class Association(db.Model):
    __tablename__ = 'associations'  

    id_association = db.Column(db.Integer, primary_key=True)
    nom_complet = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(40), unique=True, nullable=False)
    description_association = db.Column(db.String(255), nullable=True)
    telephone = db.Column(db.String(15), nullable=False)  
    adresse = db.Column(db.String(100), nullable=True)  
    rne = db.Column(db.String(20), unique=True, nullable=True)
    type_association = db.Column(
    SqlEnum(TypeAssociationEnum, name="type_association_enum"),
    nullable=False,
    default=TypeAssociationEnum.AUTRE
)

    photo = db.Column(db.String(255), nullable=True)  # pour stocker le chemin de la photo
    matricule_fiscal = db.Column(db.String(50), nullable=True)
    cin_fiscale = db.Column(db.String(255), nullable=True)  # upload: path to file
    releve_rib = db.Column(db.String(50), nullable=True)

    gouvernorat_id = db.Column(db.Integer, db.ForeignKey('gouvernorat.id'), nullable=True)

    
    
    # association créé par Admin
    id_admin = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False) 

    def __repr__(self):
        return f"<Association {self.nom_complet}>"







    



class Don(db.Model):
    __tablename__ = "dons"

    id_don = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(600), nullable=True)
    objectif = db.Column(db.Float, nullable=False)
    montant_collecte = db.Column(db.Float, default=0.0)
    date_fin_collecte = db.Column(db.Date, nullable=False)
    recu_don = db.Column(db.String(255), nullable=True)
    photo_don = db.Column(db.String(255), nullable=True)
    statut = db.Column(db.String(20), default="en_attente")  # "en_attente", "valide", "refuse"

     #  Attributs utiles pour les statistiques :
    nb_donateurs = db.Column(db.Integer, default=0)
    is_reussi = db.Column(db.Boolean, default=False)
    

    # clé etrangere avec cascade
    id_association = db.Column(
        db.Integer,
        db.ForeignKey("associations.id_association", ondelete="CASCADE"),
        nullable=False
    )
    association = db.relationship("Association", backref=db.backref("dons", cascade="all, delete-orphan"))

    id_utilisateur = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
class Participation(db.Model):
    __tablename__ = "participations"

    id_participation = db.Column(db.Integer, primary_key=True)
    montant = db.Column(db.Float, nullable=False)
    date_participation = db.Column(db.DateTime, default=datetime.utcnow)

    # Clé étrangère vers le don
    id_don = db.Column(db.Integer, db.ForeignKey("dons.id_don", ondelete="CASCADE"), nullable=False)
    don = db.relationship("Don", backref=db.backref("participations", cascade="all, delete-orphan"))

    # Clé étrangère vers l’utilisateur (donateur)
    id_user = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = db.relationship("User", backref=db.backref("participations", cascade="all, delete-orphan"))


class Publication(db.Model):
    __tablename__ = "publications"

    id_publication = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(100), nullable=False)
    contenu = db.Column(db.Text, nullable=False)
    date_publication = db.Column(db.Date, nullable=False)
    nb_likes = db.Column(db.Integer, default=0)
    nb_commentaires = db.Column(db.Integer, default=0)
    nb_partages = db.Column(db.Integer, default=0)
    statut = db.Column(db.String(20), default="en_attente")  # "en_attente", "valide", "refuse"

    # clé etrangére avec CASCADE (si une association a été supprimée, ses publications seront supprimées)
    id_association = db.Column(
        db.Integer,
        db.ForeignKey("associations.id_association", ondelete="CASCADE"),
        nullable=False
    )

    # la liaison d'une publication avec les commentaires
    commentaires = db.relationship("Commentaire", backref="publication", cascade="all, delete-orphan")
    association = db.relationship("Association", backref="publications")

class Commentaire(db.Model):
    __tablename__ = "commentaires"

    id_commentaire = db.Column(db.Integer, primary_key=True)
    contenu = db.Column(db.Text, nullable=False)
    date_commentaire = db.Column(db.Date, nullable=False)
    sentiment = db.Column(db.String(20), nullable=True)  # "positif", "neutre", "négatif"
    parent_comment_id = db.Column(
        db.Integer,
        db.ForeignKey("commentaires.id_commentaire", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    replies = db.relationship(
        "Commentaire",
        backref=db.backref("parent", remote_side=[id_commentaire]),
        cascade="all, delete-orphan",
        lazy=True
    )

    # clé etrangére avec CASCADE (si une publication a été supprimée, ses commentaires seront supprimées)
    id_publication = db.Column(
        db.Integer,
        db.ForeignKey("publications.id_publication", ondelete="CASCADE"),
        nullable=False
    )
    id_user = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)



class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    contenu = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)

    id_association = db.Column(db.Integer, db.ForeignKey("associations.id_association", ondelete="CASCADE"), nullable=False, index=True)
    id_publication = db.Column(db.Integer, db.ForeignKey("publications.id_publication", ondelete="CASCADE"), nullable=True, index=True)
    id_don = db.Column(db.Integer, db.ForeignKey("dons.id_don", ondelete="CASCADE"), nullable=True, index=True)  

    association = db.relationship("Association", backref=db.backref("notifications", lazy=True, cascade="all, delete-orphan"))
    publication = db.relationship("Publication", backref=db.backref("notifications", lazy=True, cascade="all, delete-orphan"))
    don = db.relationship("Don", backref=db.backref("notifications", lazy=True, cascade="all, delete-orphan"))  # ✅ AJOUTÉ ICI

    id_user = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    user = db.relationship("User", backref="notifications")
    
    __table_args__ = (
        # Exactly one source must be set (XOR)
        CheckConstraint(
            "(id_publication IS NOT NULL AND id_don IS NULL) OR "
            "(id_publication IS NULL AND id_don IS NOT NULL)",
            name="ck_notifications_exactly_one_source"
        ),

        # Avoid duplicates for publication-sourced notifs
        UniqueConstraint(
            "id_association", "id_publication", "contenu",
            name="uq_notifications_pub_once"
        ),

        # Avoid duplicates for don-sourced notifs
        UniqueConstraint(
            "id_association", "id_don", "contenu",
            name="uq_notifications_don_once"
        ),

        # Helpful composite index for listing latest
        Index("ix_notifications_assoc_date", "id_association", "date")
    )
# ---------- Methods ---------
@app.before_request

def handle_options_request():
    if request.method == "OPTIONS":
        response = jsonify({"message": "CORS preflight request successful"})
        origin = request.headers.get("Origin", "*")
        response.headers.add("Access-Control-Allow-Origin", origin)
        response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
        response.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        return response, 200

import re

# Fonction de validation
def is_valid_nom_complet(nom):
     return bool(re.fullmatch(r"[A-Za-zÀ-ÿ\s\-]{1,40}", nom))
def is_valid_email(email):
    # Format basique d’un email
    return bool(re.fullmatch(r"[^@]+@[^@]+\.[^@]+", email))

def is_valid_telephone(tel):
    return bool(re.fullmatch(r"\d{8}", tel))

def is_strong_password(password):
    return bool(re.fullmatch(r"^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{6,}$", password))


from flask_jwt_extended import create_access_token, create_refresh_token

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    nom_complet = data.get("nom_complet")
    telephone = data.get("telephone")
    role = data.get("role", "donator")

    # 🔐 Vérifications
    if not email or not password or not nom_complet or not telephone:
        return jsonify({"error": "Tous les champs sont requis."}), 400

    if not is_valid_email(email):
        return jsonify({"error": "L'email n'est pas valide."}), 400

    if not is_valid_nom_complet(nom_complet):
        return jsonify({"error": "Le nom complet ne doit contenir que des lettres, espaces ou tirets (max 40 caractères)."}), 400

    if not is_valid_telephone(telephone):
        return jsonify({"error": "Le numéro de téléphone doit contenir exactement 8 chiffres."}), 400

    if not is_strong_password(password):
        return jsonify({"error": "Le mot de passe doit contenir au moins une lettre majuscule, un chiffre, et un caractère spécial."}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Cet email est déjà utilisé."}), 409

    if role not in ["admin", "donator"]:
        return jsonify({"error": "Rôle invalide."}), 400

    #  Création de l'utilisateur
    user = User(email=email, role=role, nom_complet=nom_complet, telephone=telephone, is_verified=False)
    user.set_password(password)

    code = generate_otp_code()
    user.otp_code = code
    user.otp_expires_at = datetime.utcnow() + timedelta(minutes=10)
    user.otp_attempts = 0
    user.otp_last_sent = datetime.utcnow()

    db.session.add(user)
    db.session.commit()
    send_otp_email(user, code)

    #  Réponse complète
    return jsonify({
        "message": "Compte créé. Un code OTP vous a été envoyé par email. Veuillez vérifier votre compte.",
        "need_verification": True
    }), 201
# helpers otp 
import secrets
from datetime import datetime, timedelta

def generate_otp_code(n=6):
    # 6 chiffres aléatoires, sans zéros en tête “coupés”
    return f"{secrets.randbelow(10**n):0{n}d}"

def send_otp_email(user, code):
    try:
        msg = Message(
            subject="Votre code de vérification DonByUIB",
            recipients=[user.email],
            sender=app.config['MAIL_USERNAME']
        )
        msg.body = (
            f"Bonjour {user.nom_complet or ''},\n\n"
            f"Votre code de vérification est : {code}\n"
            f"Il expire dans 10 minutes.\n\n"
            "— L’équipe DonByUIB"
        )
        mail.send(msg)
    except Exception:
        app.logger.exception("Échec envoi OTP")

#vérifier otp
@app.route("/verify-otp", methods=["POST"])
def verify_otp():
    data = request.get_json()
    email = data.get("email")
    code = data.get("code")

    if not email or not code:
        return jsonify({"error": "Email et code sont requis."}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "Utilisateur introuvable."}), 404

    if user.is_verified:
        return jsonify({"message": "Compte déjà vérifié."}), 200

    # sécurité de base : limiter à 5 tentatives
    if user.otp_attempts is not None and user.otp_attempts >= 5:
        return jsonify({"error": "Trop de tentatives. Demandez un nouveau code."}), 429

    if not user.otp_code or not user.otp_expires_at or datetime.utcnow() > user.otp_expires_at:
        return jsonify({"error": "Code expiré. Demandez un nouveau code."}), 410

    if code.strip() != user.otp_code:
        user.otp_attempts = (user.otp_attempts or 0) + 1
        db.session.commit()
        return jsonify({"error": "Code invalide."}), 401

    # Succès : marquer vérifié et nettoyer les champs OTP
    user.is_verified = True
    user.otp_code = None
    user.otp_expires_at = None
    user.otp_attempts = 0
    db.session.commit()

    # On peut maintenant créer un access token classique
    additional_claims = {"email": user.email, "role": user.role}
    access_token = create_access_token(identity=str(user.id), additional_claims=additional_claims)

    return jsonify({"message": "Compte vérifié avec succès.", "access_token": access_token}), 200
# renvoyer otp 
@app.route("/resend-otp", methods=["POST"])
def resend_otp():
    data = request.get_json()
    email = data.get("email")
    if not email:
        return jsonify({"error": "Email requis."}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "Utilisateur introuvable."}), 404

    if user.is_verified:
        return jsonify({"message": "Compte déjà vérifié."}), 200

    # Anti-spam : 60s de cooldown + max 5 envois par heure (simple)
    now = datetime.utcnow()
    if user.otp_last_sent and (now - user.otp_last_sent) < timedelta(seconds=60):
        return jsonify({"error": "Veuillez patienter avant de renvoyer un code."}), 429

    code = generate_otp_code()
    user.otp_code = code
    user.otp_expires_at = now + timedelta(minutes=10)
    user.otp_attempts = 0
    user.otp_last_sent = now

    db.session.commit()
    send_otp_email(user, code)

    return jsonify({"message": "Nouveau code envoyé."}), 200

# captcha register
from captcha.image import ImageCaptcha
import random
import string
import base64
from io import BytesIO

@app.route("/get-captcha-image", methods=["GET"])
def get_captcha_image():
    captcha_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    image = ImageCaptcha()
    image_data = image.generate(captcha_text).read()
    encoded_image = base64.b64encode(image_data).decode("utf-8")

    return jsonify({
        "captcha_image": f"data:image/png;base64,{encoded_image}",
        "captcha_text": captcha_text  # En prod, ne jamais envoyer le texte en clair !
    })



# afficher infos donateur 
@app.route('/get-info-donateur', methods=['GET']) 
@jwt_required()
def get_info_donator():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    return jsonify({
        "nom_complet": user.nom_complet,
        "email": user.email
    })
# refresh token pour regénérer un access token 
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt, create_access_token

@app.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    # tu peux aussi vérifier le blocklist via ton loader existant
    identity = get_jwt_identity()
    claims   = get_jwt()  # contient aussi email/role si tu les as mis dans refresh
    new_access = create_access_token(
        identity=identity,
        additional_claims={"email": claims.get("email"), "role": claims.get("role")}
    )
    return jsonify({"access_token": new_access}), 200

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    # 🔍 Recherche utilisateur
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Identifiants invalides"}), 401

    # ✅ OTP uniquement pour les donateurs
    if user.role == "donator" and not user.is_verified:
        # Ici tu déclenches l’envoi du code OTP par email ou SMS
        # par exemple: send_otp(user.email)
        return jsonify({
            "error": "Vérification OTP requise.",
            "need_verification": True,
            "role": user.role
        }), 403

    # 🧠 Récupération du nom selon le rôle
    username = None
    if user.role == "association":
        association = Association.query.filter_by(email=email).first()
        if association:
            username = association.nom_complet
    else:
        username = user.nom_complet

    # 🎫 Génération des tokens JWT
    additional_claims = {"email": user.email, "role": user.role}
    access_token  = create_access_token(identity=str(user.id), additional_claims=additional_claims)
    refresh_token = create_refresh_token(identity=str(user.id), additional_claims=additional_claims)

    print("✅ Connexion réussie pour :", user.email)
    print("🔐 JWT généré avec rôle :", user.role)

    # ✅ Réponse finale
    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "role": user.role,
        "username": username
    }), 200




@app.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]  # Get token identifier (JTI)
    revoked_tokens.add(jti)  # Add token to revoked list
    return jsonify({"message": "Successfully logged out"}), 200

@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    return jwt_payload["jti"] in revoked_tokens

#reset password 

@app.route("/reset-password", methods=["POST"])
@jwt_required()
def reset_password():
    data = request.get_json()
    new_password = data.get("new_password")

    if not new_password:
        return jsonify({"error": "Mot de passe requis."}), 400

    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"error": "Utilisateur non trouvé."}), 404

    user.set_password(new_password)
    db.session.commit()

    return jsonify({"message": "Mot de passe réinitialisé avec succès."}), 200


# reset + verification with email
@app.route("/request-password-reset", methods=["POST"])
def request_password_reset():
    data = request.get_json()
    email = data.get("email")

    FRONTEND_WEB = os.getenv("FRONTEND_WEB", "http://localhost:4200")
    FRONTEND_IONIC = os.getenv("FRONTEND_IONIC", "http://localhost:8100")
    USE_HASH = os.getenv("USE_HASH_ROUTING", "true").lower() == "true"
    RESET_PATH = "/#/reset-password" if USE_HASH else "/reset-password"

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "Aucun compte avec cet email."}), 404

    # Générer token temporaire (valide 30 min)
    token = create_access_token(identity=str(user.id), expires_delta=timedelta(minutes=30))

    link_web = f"{FRONTEND_WEB}{RESET_PATH}/{token}"
    link_ionic = f"{FRONTEND_IONIC}{RESET_PATH}/{token}"

    # Envoyer l'email
    msg = Message(
        "Réinitialisation du mot de passe",
        sender=app.config['MAIL_USERNAME'],
        recipients=[email]
    )

    msg.body = (
        "Bonjour,\n\n"
        "Réinitialisez votre mot de passe avec l’un de ces liens :\n"
        f"- Web  : {link_web}\n"
        f"- Ionic : {link_ionic}\n\n"
        "Le lien expire dans 30 minutes."
    )

    mail.send(msg)
    return jsonify({"message": "Un lien de réinitialisation a été envoyé à votre email."}), 200


@app.route("/create-association", methods=["POST"])
@jwt_required()
def create_association():
    try:
        current_user_id = get_jwt_identity()
        claims = get_jwt()

        if claims.get("role") != "admin":
            return jsonify({"error": "Access denied, admin only!"}), 403

        data = request.get_json()
        print("📥 Data received:", data)

        # Champs obligatoires
        required_fields = ["nom_complet", "email", "telephone", "adresse", "type_association", "password", "gouvernorat_id"]
        for field in required_fields:
            if field not in data or (isinstance(data[field], str) and not data[field].strip()):
                return jsonify({"error": f"'{field}' must be a non-empty string"}), 400

        # Validation du type_association
        type_str = data["type_association"].strip().lower()
        type_map = {
            "humanitaire": TypeAssociationEnum.HUMANITAIRE,
            "education": TypeAssociationEnum.EDUCATION,
            "éducation": TypeAssociationEnum.EDUCATION,
            "sante": TypeAssociationEnum.SANTE,
            "santé": TypeAssociationEnum.SANTE,
            "environnement": TypeAssociationEnum.ENVIRONNEMENT,
            "autre": TypeAssociationEnum.AUTRE
        }
        type_enum = type_map.get(type_str)
        if not type_enum:
            valid_types = [t.value for t in TypeAssociationEnum]
            return jsonify({
                "error": f"Type d'association invalide. Valeurs valides : {valid_types}"
            }), 400

        # Validation du gouvernorat_id
        try:
            gouvernorat_id = int(data["gouvernorat_id"])
            if not Gouvernorat.query.get(gouvernorat_id):
                return jsonify({"error": "Gouvernorat non trouvé."}), 404
        except Exception:
            return jsonify({"error": "ID de gouvernorat invalide."}), 400

        # Vérification de l'unicité de l'email
        if User.query.filter_by(email=data["email"]).first():
            return jsonify({"error": "Email already exists"}), 409

        # Création du user
        new_user = User(
            email=data["email"].strip(),
            role="association"
        )
        new_user.set_password(data["password"])
        db.session.add(new_user)
        db.session.flush()  # Récupérer new_user.id

        # Création de l'association
        new_association = Association(
            nom_complet=data["nom_complet"].strip(),
            email=data["email"].strip(),
            description_association=data.get("description_association", "").strip(),
            telephone=data["telephone"].strip(),
            adresse=data["adresse"].strip(),
            type_association=type_enum,
            gouvernorat_id=gouvernorat_id,
            id_admin=current_user_id,
            rne=None,
            matricule_fiscal=None,
            cin_fiscale=None,
            releve_rib=None
        )
        db.session.add(new_association)
        db.session.commit()

        return jsonify({"message": "✅ Association created successfully", "user_id": new_user.id}), 201

    except Exception as e:
        db.session.rollback()
        print("🔥 Server Error in /create-association:", str(e))
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500









@app.route("/associations", methods=["GET"])
@jwt_required()
def get_associations():
    current_user_id = get_jwt_identity()
    claims = get_jwt()  # Retrieve claims including role

    if claims.get("role") not in ["admin", "donator"]:
        return jsonify({"error": "Access denied!"}), 403

    try:
        associations = Association.query.all()
        result = [
            {
                "id_association": assoc.id_association,  
                "nom_complet": assoc.nom_complet, 
                "email": assoc.email,  
                "description_association": assoc.description_association,  
                "telephone": assoc.telephone,  
                "adresse": assoc.adresse,  
                "type_association": assoc.type_association.value, 
                "gouvernorat_id": assoc.gouvernorat_id,
                "nomGouvernorat": assoc.gouvernorat.nomGouvernorat if assoc.gouvernorat else None
                
            }
            for assoc in associations
        ]
        return jsonify(result), 200  # ✅ Correct JSON format

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# modifier association par admin 
@app.route("/modify-compte-association/<int:id>", methods=["PUT"])
@jwt_required()
def modify_compte_association(id):
    try:
        claims = get_jwt()
        if claims.get("role") != "admin":
            return jsonify({"error": "Access denied!"}), 403

        data = request.form

        # ✅ D'abord vérifier que l'association existe
        association = Association.query.get(id)
        if not association:
            return jsonify({"error": "Association not found!"}), 404

        # ✅ Puis récupérer l'user correspondant, et vérifier
        user = User.query.filter_by(email=association.email).first()
        if not user:
            return jsonify({"error": "User not found for this association!"}), 404

        # --- mises à jour ---
        if "nom_complet" in data:
            association.nom_complet = data["nom_complet"].strip()

        if "email" in data:
            new_email = data["email"].strip()
            existing_user = User.query.filter(User.email == new_email, User.id != user.id).first()
            if existing_user:
                return jsonify({"error": "Email already exists!"}), 409
            association.email = new_email
            user.email = new_email

        if "description_association" in data:
            association.description_association = data["description_association"].strip()
        if "telephone" in data:
            association.telephone = data["telephone"].strip()
        if "adresse" in data:
            association.adresse = data["adresse"].strip()
        if "type_association" in data:
            try:
                type_enum = TypeAssociationEnum(data["type_association"].strip().lower())
                association.type_association = type_enum
            except ValueError:
                valid_types = [t.value for t in TypeAssociationEnum]
                return jsonify({
                    "error": f"Type d'association invalide. Valeurs valides : {valid_types}"
                }), 400

        db.session.commit()
        return jsonify({"message": "Association updated successfully!"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# supprimer association par l'admin
@app.route("/delete-compte-association/<int:id_association>", methods=["DELETE"])
@jwt_required()
def delete_compte_association(id_association):
    try:
        claims = get_jwt()
        if claims.get("role") != "admin":
            return jsonify({"error": "Access denied! Only admin can delete an association."}), 403

        association = Association.query.get(id_association)
        if not association:
            return jsonify({"error": "Association not found."}), 404

        user = User.query.filter_by(email=association.email).first()

        # Supprimer d'abord l'utilisateur lié (optionnel selon ton modèle)
        if user:
            db.session.delete(user)

        db.session.delete(association)
        db.session.commit()

        return jsonify({"message": "Association deleted successfully!"}), 200

    except Exception as e:
        db.session.rollback()
        print("Error:", str(e))
        return jsonify({"error": str(e)}), 500
@app.route("/gouvernorats", methods=["GET"])
def get_gouvernorats():
    gouvernorats = Gouvernorat.query.all()
    result = [{"id": g.id, "nomGouvernorat": g.nomGouvernorat} for g in gouvernorats]
    return jsonify(result), 200

@app.route("/modify-profile-association", methods=["PUT"])
@jwt_required()
def modify_association():
    try:
        claims = get_jwt()
        if claims.get("role") != "association":
            return jsonify({"error": "Access denied! Only associations can modify their profile."}), 403

        data = request.form
        file_photo = request.files.get("photo_file")
        file_cin = request.files.get("cin_fiscale_file")

        association = Association.query.filter_by(email=claims.get("email")).first()
        user = User.query.filter_by(email=claims.get("email")).first()

        if not association or not user:
            return jsonify({"error": "Association not found!"}), 404

        # Champs simples
        association.nom_complet = data.get("nom_complet", association.nom_complet)
        association.description_association = data.get("description_association", association.description_association)
        association.telephone = data.get("telephone", association.telephone)
        association.adresse = data.get("adresse", association.adresse)
        association.matricule_fiscal = data.get("matricule_fiscal", association.matricule_fiscal)
        association.releve_rib = data.get("releve_rib", association.releve_rib)

        # Gouvernorat (select)
        if "gouvernorat_id" in data:
            try:
                association.gouvernorat_id = int(data["gouvernorat_id"])
            except ValueError:
                return jsonify({"error": "ID gouvernorat invalide"}), 400

        # Type Association (enum)
        if "type_association" in data:
            try:
                type_enum = TypeAssociationEnum(data["type_association"].strip().lower())
                association.type_association = type_enum
            except Exception:
                valid_types = [t.name for t in TypeAssociationEnum]
                return jsonify({
                    "error": f"Type d'association invalide. Valeurs valides : {valid_types}"
                }), 400

        # Email (modifie aussi l'utilisateur)
        if "email" in data:
            new_email = data["email"].strip()
            existing_user = User.query.filter(User.email == new_email, User.id != user.id).first()
            if existing_user:
                return jsonify({"error": "Email already exists!"}), 409
            association.email = new_email
            user.email = new_email

        # Fichier photo
        if file_photo:
            filename = secure_filename(file_photo.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file_photo.save(file_path)
            association.photo = f"/static/uploads/{filename}"

        # Fichier CIN fiscale
        if file_cin:
            filename_cin = secure_filename(file_cin.filename)
            path_cin = os.path.join(app.config['UPLOAD_FOLDER'], filename_cin)
            file_cin.save(path_cin)
            association.cin_fiscale = f"/static/uploads/{filename_cin}"

        # Changement mot de passe
        if "old_password" in data and "new_password" in data:
            if not user.check_password(data["old_password"]):
                return jsonify({"error": "Old password is incorrect!"}), 401
            user.password_hash = generate_password_hash(data["new_password"])

        db.session.commit()
        return jsonify({"message": "Association profile updated successfully!"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/modify-profile-donateur", methods=["PUT"])
@jwt_required()
def modify_donator():
    try:
        current_user_id = get_jwt_identity()
        claims = get_jwt()

        if claims.get("role") != "donator":
            return jsonify({"error": "Access denied! Only donators can modify their profile."}), 403

        # ✅ Accepter FormData (cas Angular avec <form>)
        data = request.form
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({"error": "Donator not found!"}), 404

        # ✅ Mise à jour des champs facultatifs
        if "nom_complet" in data and data["nom_complet"].strip():
            user.nom_complet = data["nom_complet"].strip()

        if "email" in data and data["email"].strip():
            existing_user = User.query.filter(User.email == data["email"].strip(), User.id != user.id).first()
            if existing_user:
                return jsonify({"error": "Email already exists!"}), 409
            user.email = data["email"].strip()

        if "telephone" in data and data["telephone"].strip():
            user.telephone = data["telephone"].strip()

        # ✅ Mot de passe
        if "old_password" in data and "new_password" in data:
            if not user.check_password(data["old_password"]):
                return jsonify({"error": "Ancien mot de passe incorrect."}), 401
            user.set_password(data["new_password"])

        db.session.commit()

        return jsonify({"message": "✅ Profil mis à jour avec succès."}), 200

    except Exception as e:
        db.session.rollback()
        print("❌ Erreur dans modify_donator:", str(e))
        return jsonify({"error": "Erreur serveur", "details": str(e)}), 500


@app.route("/get-profile-donator", methods=["GET"])
@jwt_required()
def get_profile_donator():
    try:
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        if claims.get("role") != "donator":
            return jsonify({"error": "Access denied!"}), 403

        user = User.query.get(current_user_id)
        if not user:
            return jsonify({"error": "Donator profile not found"}), 404

        return jsonify({
            "nom_complet": user.nom_complet,
            "email": user.email,
            "telephone": user.telephone
        }), 200

    except Exception as e:
        print("Error fetching donator profile:", str(e))
        return jsonify({"error": str(e)}), 500

 # get by id the association infos
@app.route("/association/<int:id>", methods=["GET"])
@jwt_required()
def get_association_detail(id):
    try:
        claims = get_jwt()
        if claims.get("role") != "admin":
            return jsonify({"error": "Access denied!"}), 403

        association = Association.query.get(id)

        if not association:
            return jsonify({"error": "Association non trouvée."}), 404

      

        result = {
            "nom_complet": association.nom_complet,
            "email": association.email,
            "description_association": association.description_association,
            "telephone": association.telephone,
            "adresse": association.adresse,
            "type_association": association.type_association.value,
        }

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
# get profile of an association
@app.route("/get-profile-association", methods=["GET"])
@jwt_required()
def get_profile_association():
    try:
        current_user_id = get_jwt_identity()
        claims = get_jwt()

        if claims.get("role") != "association":
            return jsonify({"error": "Access denied!"}), 403

        # Fetch the user's association profile
        association = Association.query.filter_by(email=claims.get("email")).first()

        if not association:
            return jsonify({"error": "Association profile not found"}), 404

        # Return profile data
        return jsonify({
        "nom_complet": association.nom_complet,
        "email": association.email,
        "description_association": association.description_association,
        "telephone": association.telephone,
        "adresse": association.adresse,
        "type_association": association.type_association.value,
        "photo": association.photo,
        "matricule_fiscal": association.matricule_fiscal,
        "releve_rib": association.releve_rib,
        "cin_fiscale": association.cin_fiscale,
        "gouvernorat_id": association.gouvernorat_id,
        # Ce champ provoque l'erreur :
        "nomGouvernorat": association.gouvernorat.nomGouvernorat if association.gouvernorat else None
    }), 200

    except Exception as e:
        print("Error fetching profile:", str(e))
        return jsonify({"error": str(e)}), 500

# ajouter don
@app.route("/create-don", methods=["POST"])
@jwt_required()
def create_don():
    try:
        claims = get_jwt()
        if claims.get("role") != "association":
            return jsonify({"error": "Access denied: only associations can create dons."}), 403

        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        association = Association.query.filter_by(email=user.email).first()
        if not association:
            return jsonify({"error": "Aucune association liée à ce compte."}), 404

        data = request.form
        file = request.files.get("photo_file")

        # Champs requis
        titre = data.get("titre")
        objectif_str = data.get("objectif")
        date_fin_collecte_str = data.get("date_fin_collecte")

        if not titre or not objectif_str or not date_fin_collecte_str:
            return jsonify({"error": "Titre, objectif et date_fin_collecte sont obligatoires."}), 400

        # Conversion float
        try:
            objectif = float(objectif_str)
        except Exception:
            return jsonify({"error": "L'objectif doit être un nombre"}), 400

        # Conversion date
        try:
            date_fin_collecte = datetime.strptime(date_fin_collecte_str, "%Y-%m-%d").date()
        except Exception:
            return jsonify({"error": "La date doit être au format AAAA-MM-JJ"}), 400

        # Image
        photo_path = None
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            photo_path = f"/static/uploads/{filename}"

        # Créer Don
        new_don = Don(
            titre=titre.strip(),
            description=data.get("description", "").strip(),
            objectif=objectif,
            montant_collecte=0.0,
            date_fin_collecte=date_fin_collecte,
            photo_don=photo_path,
            id_association=association.id_association,
            id_utilisateur=current_user_id,
            statut="en_attente",
        )

        db.session.add(new_don)
        db.session.commit()

        return jsonify({"message": "✅ Don créé avec succès !"}), 201

    except Exception as e:
        db.session.rollback()
        print("Erreur lors de la création du don:", str(e))
        return jsonify({"error": str(e)}), 500
    
# modifier don par l'association
@app.route("/update-don/<int:id_don>", methods=["PUT"])

@jwt_required()
def update_don(id_don):
    try:
        claims = get_jwt()
        if claims.get("role") != "association":
            return jsonify({"error": "Accès refusé : seules les associations peuvent modifier un don."}), 403

        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        association = Association.query.filter_by(email=user.email).first()

        if not association:
            return jsonify({"error": "Association non trouvée."}), 404

        don = Don.query.filter_by(id_don=id_don, id_association=association.id_association).first()
        if not don:
            return jsonify({"error": "Don introuvable ou non autorisé."}), 404

        # Récupérer les données
        data = request.form
        file = request.files.get("photo_file")

        if "titre" in data:
            don.titre = data["titre"].strip()

        if "description" in data:
            don.description = data["description"].strip()

        if "objectif" in data:
            try:
                don.objectif = float(data["objectif"])
            except ValueError:
                return jsonify({"error": "L'objectif doit être un nombre"}), 400

        if "date_fin_collecte" in data:
            try:
                don.date_fin_collecte = datetime.strptime(data["date_fin_collecte"], "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"error": "Date invalide. Format attendu : AAAA-MM-JJ"}), 400

        # 📷 Gestion du changement de photo
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            don.photo_don = f"/static/uploads/{filename}"

        db.session.commit()
        return jsonify({"message": "✅ Don mis à jour avec succès."}), 200

    except Exception as e:
        db.session.rollback()
        print("Erreur modification don :", str(e))
        return jsonify({"error": str(e)}), 500

# supprimer don par l'association
@app.route("/delete-don/<int:id_don>", methods=["DELETE"])
@jwt_required()
def delete_don(id_don):
    try:
        claims = get_jwt()
        if claims.get("role") != "association":
            return jsonify({"error": "Access denied! Only associations can delete their donations."}), 403

        # ✅ Assoc liée au user connecté
        assoc = Association.query.filter_by(email=claims.get("email")).first()
        if not assoc:
            return jsonify({"error": "Association introuvable pour cet utilisateur."}), 404

        # ✅ Chercher le don appartenant à cette association
        don = Don.query.filter_by(id_don=id_don, id_association=assoc.id_association).first()
        if not don:
            return jsonify({"error": "Don not found."}), 404

        db.session.delete(don)
        db.session.commit()
        return jsonify({"message": "Don deleted successfully!"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# valider don
@app.route("/don/<int:id_don>/valider", methods=["PUT"])
@jwt_required()
def valider_don(id_don):
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Accès refusé"}), 403

    don = Don.query.get(id_don)
    if not don:
        return jsonify({"error": "Don introuvable"}), 404

    don.statut = "valide"
    id_assoc = don.id_association
    # ✅ Notification
    notif_assoc = Notification(
    contenu=f"Le don '{don.titre}' a été validé par l’administrateur.",
    id_association=id_assoc,
    is_read=False,
    id_don=don.id_don,
    date=datetime.utcnow()
)

    db.session.add(notif_assoc)
    # 🔔 Notifier tous les donateurs
    utilisateurs = User.query.filter_by(role='donator').all()
    for user in utilisateurs:
        notif = Notification(
            contenu=f"Nouveau don : {don.titre}",
            date=datetime.utcnow(),
            is_read=False,
            id_association=id_assoc,  
            id_user=user.id,
            id_don=don.id_don 
        )
        db.session.add(notif)

  

    db.session.commit()
    return jsonify({"message": "Don validé avec succès"}), 200
# supprimer les notifications qui dépassent 24h
@app.route('/notifications/cleanup', methods=['DELETE'])
@jwt_required()
def supprimer_anciennes_notifications():
    if get_jwt().get("role") != "association":
        return jsonify({"error": "Accès refusé"}), 403

    limite = datetime.utcnow() - timedelta(days=1)
    anciennes = Notification.query.filter(Notification.date < limite).all()

    for notif in anciennes:
        db.session.delete(notif)

    db.session.commit()
    return jsonify({"message": f"{len(anciennes)} notifications supprimées"}), 200


# Refuser don

@app.route("/don/<int:id_don>/refuser", methods=["PUT"])
@jwt_required()
def refuser_don(id_don):
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Accès refusé"}), 403

    don = Don.query.get(id_don)
    if not don:
        return jsonify({"error": "Don introuvable"}), 404

    don.statut = "refuse"

    # ✅ Notification
    notif = Notification(
        contenu=f"Le don '{don.titre}' a été refusé par l’administrateur.",
        id_association=don.id_association,
        date=datetime.utcnow()
    )
    db.session.add(notif)

    # ✅ Email (optionnel)
    try:
        assoc = don.association
        if assoc and assoc.email:
            msg = Message(
                subject="Refus de votre don",
                sender=app.config.get("MAIL_DEFAULT_SENDER", "admin@donbyuib.tn"),
                recipients=[assoc.email],
                body=f"Bonjour {assoc.nom_complet},\n\nVotre don intitulé '{don.titre}' a été refusé par l'administrateur.\n\nMerci."
            )
            mail.send(msg)
    except Exception as e:
        print("Erreur lors de l’envoi de l’email :", e)

    db.session.commit()
    return jsonify({"message": "Don refusé avec succès"}), 200


# get dons pour l'admin 

@app.route("/admin/dons", methods=["GET"])
@jwt_required()
def get_all_dons_admin():
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Accès refusé"}), 403

    dons = Don.query.all()
    result = []
    for don in dons:
        result.append({
            "id_don": don.id_don,
            "titre": don.titre,
            "description": don.description,
            "objectif": don.objectif,
            "montant_collecte": don.montant_collecte,
            "date_fin_collecte": don.date_fin_collecte.isoformat(),
            "photo_don": don.photo_don,
            "statut": don.statut,
            "association": don.association.nom_complet if don.association else "Inconnue"
        })

    return jsonify(result), 200

# valider publication

@app.route("/publication/<int:id_publication>/valider", methods=["PUT"])
@jwt_required()
def valider_publication(id_publication):
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Accès refusé"}), 403

    publication = Publication.query.get(id_publication)
    if not publication:
        return jsonify({"error": "publication introuvable"}), 404

    publication.statut = "valide"
    id_assoc = publication.id_association
    # ✅ Notification
    notif_assoc = Notification(
        contenu=f"La publication '{publication.titre}' a été validée par l’administrateur.",
        date=datetime.utcnow(),
        is_read=False,
        id_association=id_assoc,
        id_publication=publication.id_publication
    )
    db.session.add(notif_assoc)
    # 🔔 Notifier tous les donateurs
    utilisateurs = User.query.filter_by(role='donator').all()
    for user in utilisateurs:
        notif = Notification(
            contenu=f"Nouvelle publication : {publication.titre}",
            date=datetime.utcnow(),
            is_read=False,
            id_association=id_assoc,  # ✅ On met ici la bonne valeur
            id_user=user.id,
            id_publication=publication.id_publication # (facultatif si tu veux rattacher la notif à la publication)
        )
        db.session.add(notif)
    

    db.session.commit()
    return jsonify({"message": "Publication validé avec succès"}), 200


@app.route("/publication/<int:id_publication>/refuser", methods=["PUT"])
@jwt_required()
def refuser_publication(id_publication):
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Accès refusé"}), 403

    publication = Publication.query.get(id_publication)
    if not publication:
        return jsonify({"error": "Publication introuvable"}), 404

    publication.statut = "refuse"

    notif = Notification(
        contenu=f"La publication '{publication.titre}' a été refusée par l’administrateur.",
        id_publication=publication.id_publication,
        id_association=publication.id_association,  # ✅ ceci est nécessaire
        date=datetime.utcnow(),
        is_read=False  # si ce champ existe
    )
    db.session.add(notif)
    db.session.commit()

    return jsonify({"message": "Publication refusée avec succès"}), 200

# afficher les publications par l'admin 

@app.route("/admin/publications", methods=["GET"])
@jwt_required()
def get_all_publication_admin():
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Accès refusé"}), 403

    publications = Publication.query.all()
    result = []
    for publication in publications:
        result.append({
            "id_publication": publication.id_publication,
            "titre": publication.titre,
            "contenu": publication.contenu,
            "date_publication": publication.date_publication.isoformat(),
            "statut": publication.statut
        })

    return jsonify(result), 200


# get dons by associations

@app.route("/dons", methods=["GET"])
@jwt_required()
def get_dons():
    try:
        claims = get_jwt()
        if claims.get("role") != "association":
            return jsonify({"error": "Access denied: only associations can view their dons."}), 403

        current_user_id = get_jwt_identity()

        dons = Don.query.filter_by(id_utilisateur=current_user_id).all()

        result = []
        for don in dons:
            result.append({
                "id_don": don.id_don,
                "titre": don.titre,
                "description": don.description,
                "montant_collecte": don.montant_collecte,
                "objectif":don.objectif,
                "date_fin_collecte": don.date_fin_collecte.isoformat(),
                "recu_don": don.recu_don,
                "photo_don": don.photo_don,
                "id_association": don.id_association
            })

        return jsonify(result), 200

    except Exception as e:
        print("Erreur lors de la récupération des dons:", str(e))
        return jsonify({"error": str(e)}), 500
#get all dons (to pagefront)
@app.route("/public-dons", methods=["GET"])
def get_all_dons_public():
    try:
        # ❗ Exclure les dons refusés et en attente
        dons = Don.query.filter(Don.statut == "valide").all()
        today = date.today()
        result = []
        

        for don in dons:
              pourcentage = round((don.montant_collecte / don.objectif) * 100) if don.objectif > 0 else 0
              result.append({
                "id_don": don.id_don,
                "titre": don.titre,
                "description": don.description,
                "montant_collecte": don.montant_collecte,
                "objectif": don.objectif,
                "date_fin_collecte": don.date_fin_collecte.isoformat(),
                "photo_don": don.photo_don,
                "nom_organisateur": don.association.nom_complet if don.association else "Inconnu",
                "id_association": don.id_association,
                "pourcentage": pourcentage,
                "is_expire": don.date_fin_collecte < today

            })

        return jsonify(result), 200

    except Exception as e:
        print("Erreur lors de la récupération des dons:", str(e))
        return jsonify({"error": str(e)}), 500
# voir les détails de l'association en public
@app.route("/public-association/<int:id>", methods=["GET"])
def get_public_association_detail(id):
    try:
        association = Association.query.get(id)

        if not association:
            return jsonify({"error": "Association non trouvée."}), 404

        result = {
            "nom_complet": association.nom_complet,
            "photo": association.photo,
            "description_association": association.description_association,
            "telephone": association.telephone,
            "adresse": association.adresse
        }

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    
#récupérer les détails des dons
@app.route("/don/<int:id>", methods=["GET"])
def get_don_by_id(id):
    don = Don.query.get(id)
    if not don:
        return jsonify({"error": "Don non trouvé"}), 404

    return jsonify({
        "id_don": don.id_don,
        "titre": don.titre,
        "description": don.description,
        "objectif": don.objectif,
        "montant_collecte": don.montant_collecte,
        "date_fin_collecte": don.date_fin_collecte.isoformat(),
        "photo_don": don.photo_don,
        "nom_organisateur": don.association.nom_complet if don.association else "Inconnu"
    }), 200



# participer aux dons

@app.route("/participate/<int:id_don>", methods=["POST"])
@jwt_required()
def participate(id_don):
    try:
        claims = get_jwt()
        if claims.get("role") != "donator":
            return jsonify({"error": "Seuls les donateurs peuvent participer."}), 403

        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user:
            return jsonify({"error": "Utilisateur introuvable."}), 404

        don = Don.query.get(id_don)
        if not don:
            return jsonify({"error": "Don non trouvé."}), 404

        data = request.get_json()
        montant = data.get("montant")

        if not montant or float(montant) <= 0:
            return jsonify({"error": "Montant invalide."}), 400

        # Enregistrer la participation
        participation = Participation(
            montant=montant,
            id_don=id_don,
            id_user=current_user_id
        )

        db.session.add(participation)
        don.montant_collecte += float(montant)
        nb_unique_users = db.session.query(Participation.id_user).filter_by(id_don=id_don).distinct().count()
        don.nb_donateurs = nb_unique_users

# Vérifier si l’objectif est atteint
        if don.montant_collecte >= don.objectif:
            don.is_reussi = True
        # ✅ Notification à l’association lors d’une participation
        notif = Notification(
         contenu=f"{user.nom_complet} a participé avec {montant} TND au don « {don.titre} ». 🙏",
        id_association=don.id_association,
        id_don=don.id_don,
        is_read=False,
        date=datetime.utcnow()
        )
        db.session.add(notif)

        db.session.commit()
        send_congrats_email(user, don, montant)
        return jsonify({
            "message": "✅ Participation enregistrée avec succès.",
            "nom_complet": user.nom_complet,
            "email": user.email
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
    # mail de félicitation après la participation

def send_congrats_email(user, don, montant):
    try:
        msg = Message(
            subject="Merci pour votre contribution ❤️",
            recipients=[user.email],
            sender=app.config['MAIL_USERNAME']  # => donbyuib@gmail.com
        )
        # Texte brut
        msg.body = (
            f"Bonjour {user.nom_complet},\n\n"
            f"Merci pour votre don de {float(montant):.2f} TND pour « {don.titre} ».\n"
            f"Montant collecté : {float(don.montant_collecte):.2f} / {float(don.objectif):.2f} TND\n"
            f"Association : {getattr(don.association, 'nom_complet', '—')}\n\n"
            "Votre geste compte énormément. Merci !\n\n"
            "— L’équipe DonByUIB"
        )
        # Version HTML (facultatif mais recommandé)
        msg.html = f"""
        <p>Bonjour <strong>{user.nom_complet}</strong>,</p>
        <p>Merci pour votre don de <strong>{float(montant):.2f} TND</strong> pour « <strong>{don.titre}</strong> ».</p>
        <p>Montant collecté : <strong>{float(don.montant_collecte):.2f} / {float(don.objectif):.2f} TND</strong><br/>
        Association : <strong>{getattr(don.association, 'nom_complet', '—')}</strong></p>
        <p>Votre geste compte énormément. Merci 🙏</p>
        <p>— L’équipe DonByUIB</p>
        """
        mail.send(msg)
    except Exception as e:
        app.logger.exception("Échec d’envoi de l’email de félicitations")

# conter le nombre de participations 
@app.route("/don-participants", methods=["GET"])
def get_don_participants():
    try:
        results = db.session.query(
            Don.id_don,
            Don.titre,
            db.func.count(db.func.distinct(Participation.id_user)).label("nb_participants")

        ).outerjoin(Participation).group_by(Don.id_don).all()

        data = []
        for don_id, titre, nb in results:
            data.append({
                "id_don": don_id,
                "titre": titre,
                "nb_participants": nb
            })

        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/static/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)






# ajouter publication

from datetime import datetime

@app.route("/add-publications", methods=["POST"])
@jwt_required()
def create_publication():
    try:
        claims = get_jwt()
        if claims.get("role") != "association":
            return jsonify({"error": "Access denied: only associations can create publications."}), 403

        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        association = Association.query.filter_by(email=user.email).first()
        if not association:
            return jsonify({"error": "Aucune association liée à ce compte."}), 404

        data = request.get_json()
        titre = data.get("titre")
        contenu = data.get("contenu")

        if not titre or not contenu:
            return jsonify({"error": "Titre et contenu sont requis."}), 400

        new_pub = Publication(
            titre=titre.strip(),
            contenu=contenu.strip(),
            date_publication=datetime.utcnow().date(),
            id_association=association.id_association,
            statut="en_attente",
        )

        db.session.add(new_pub)
        db.session.commit()

        return jsonify({"message": "✅ Publication créée avec succès."}), 201

    except Exception as e:
        db.session.rollback()
        print("Erreur Publication:", str(e))
        return jsonify({"error": str(e)}), 500


# list publication
from sqlalchemy.orm import joinedload

@app.route("/publications", methods=["GET"])
@jwt_required()
def get_publications():
    try:
        claims = get_jwt()
        role = claims.get("role")

        # Id utilisateur (utile pour marquer is_owner dans la sérialisation)
        try:
            current_user_id = int(get_jwt_identity())
        except Exception:
            current_user_id = None

        base_query = (
            Publication.query
            .options(
                joinedload(Publication.commentaires).joinedload(Commentaire.replies),
                joinedload(Publication.association)
            )
            .order_by(Publication.date_publication.desc())
        )

        if role == "association":
            user = User.query.get(current_user_id)
            association = Association.query.filter_by(email=user.email).first() if user else None
            if not association:
                return jsonify({"error": "Aucune association trouvée."}), 404

            publications = base_query.filter_by(id_association=association.id_association).all()

        elif role == "donator":
            # Donateur : uniquement publications validées
            publications = base_query.filter_by(statut="valide").all()

        elif role == "admin":
            publications = base_query.all()

        else:
            return jsonify({"error": "Access denied!"}), 403

        result = []
        for pub in publications:
            # Racines = commentaires sans parent
            root_comments = [c for c in pub.commentaires if c.parent_comment_id is None]
            root_comments.sort(key=lambda x: x.id_commentaire)

            commentaires_tree = [serialize_comment_tree(c, current_user_id) for c in root_comments]

            result.append({
                "id_publication": pub.id_publication,
                "titre": pub.titre,
                "contenu": pub.contenu,
                "date_publication": (pub.date_publication.isoformat() if pub.date_publication else None),
                "nb_likes": pub.nb_likes,
                "nb_commentaires": pub.nb_commentaires,  # total (incluant réponses si vous incrémentez partout)
                "nb_partages": pub.nb_partages,
                "statut": pub.statut,
                "nom_association": pub.association.nom_complet if pub.association else None,
                "commentaires": commentaires_tree
            })

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# voir détails publication 
from sqlalchemy.orm import joinedload

@app.route("/publication/<int:pub_id>", methods=["GET"])
@jwt_required()
def get_publication_detail(pub_id):
    try:
        claims = get_jwt()
        role = claims.get("role")

        # Précharger commentaires (+ leurs replies) et l'association
        publication = (
            Publication.query
            .options(
                joinedload(Publication.commentaires).joinedload(Commentaire.replies),
                joinedload(Publication.association)
            )
            .filter(Publication.id_publication == pub_id)
            .first()
        )
        if not publication:
            return jsonify({"error": "Publication non trouvée."}), 404

        # Contrôle d'accès selon rôle
        if role == "association":
            assoc = Association.query.filter_by(email=claims.get("email")).first()
            if not assoc or publication.id_association != assoc.id_association:
                return jsonify({"error": "Access denied!"}), 403

        elif role == "donator":
            if publication.statut != "valide":
                return jsonify({"error": "Access denied!"}), 403

        elif role == "admin":
            pass
        else:
            return jsonify({"error": "Access denied!"}), 403

        # Id utilisateur courant pour marquer les commentaires "is_owner"
        try:
            current_user_id = int(get_jwt_identity())
        except Exception:
            current_user_id = None

        # Arbre des commentaires (racines triées)
        root_comments = [c for c in publication.commentaires if c.parent_comment_id is None]
        root_comments.sort(key=lambda x: x.id_commentaire)
        commentaires_tree = [serialize_comment_tree(c, current_user_id) for c in root_comments]

        result = {
            "id_publication": publication.id_publication,
            "titre": publication.titre,
            "contenu": publication.contenu,
            "date_publication": (publication.date_publication.isoformat() if publication.date_publication else None),
            "nb_likes": publication.nb_likes,
            "nb_commentaires": publication.nb_commentaires,  # total
            "nb_partages": publication.nb_partages,
            "statut": publication.statut,
            "nom_association": (publication.association.nom_complet if publication.association else None),
            "commentaires": commentaires_tree
        }
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# modifier commentaire

@app.route("/update-comment/<int:comment_id>", methods=["PUT"])
@jwt_required()
def update_comment(comment_id):
    try:
        claims = get_jwt()
        if claims.get("role") != "donator":
            return jsonify({"error": "Accès refusé : donateur uniquement."}), 403

        current_user_id = int(get_jwt_identity())
        com = Commentaire.query.get(comment_id)
        if not com:
            return jsonify({"error": "Commentaire introuvable."}), 404
        if com.id_user != current_user_id:
            return jsonify({"error": "Vous ne pouvez modifier que vos propres commentaires."}), 403

        data = request.get_json() or {}
        contenu = (data.get("contenu") or "").strip()
        if not contenu:
            return jsonify({"error": "Le contenu est requis."}), 400

        # Recalcule (optionnel) le sentiment
        try:
            com.sentiment = analyze_comment_fr(contenu)["label"]
        except Exception:
            pass

        com.contenu = contenu
        db.session.commit()

        return jsonify({
            "message": "✅ Commentaire mis à jour.",
            "comment": serialize_comment_tree(com, current_user_id)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# helper pour compter la taille du sous-arbre (comment + replies)
def _count_comment_subtree(c: Commentaire) -> int:
    total = 1
    for r in c.replies:
        total += _count_comment_subtree(r)
    return total


# supprimer commentaire
@app.route("/delete-comment/<int:comment_id>", methods=["DELETE"])
@jwt_required()
def delete_comment(comment_id):
    try:
        claims = get_jwt()
        if claims.get("role") != "donator":
            return jsonify({"error": "Accès refusé : donateur uniquement."}), 403

        current_user_id = int(get_jwt_identity())
        com = Commentaire.query.get(comment_id)
        if not com:
            return jsonify({"error": "Commentaire introuvable."}), 404
        if com.id_user != current_user_id:
            return jsonify({"error": "Vous ne pouvez supprimer que vos propres commentaires."}), 403

        pub = Publication.query.get(com.id_publication)
        # décrémenter nb_commentaires du nombre total de noeuds supprimés
        dec = _count_comment_subtree(com)
        db.session.delete(com)
        if pub:
            pub.nb_commentaires = max(0, (pub.nb_commentaires or 0) - dec)

        db.session.commit()
        return jsonify({"message": "🗑️ Commentaire supprimé."}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
def _count_comment_subtree(c: Commentaire) -> int:
    total = 1
    for r in c.replies:
        total += _count_comment_subtree(r)
    return total


# modifier publication

@app.route("/update-publication/<int:id>", methods=["PUT"])
@jwt_required()
def update_publication(id):
    try:
        claims = get_jwt()
        if claims.get("role") != "association":
            return jsonify({"error": "Access denied: only associations can update publications."}), 403

        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        association = Association.query.filter_by(email=user.email).first()

        if not association:
            return jsonify({"error": "Aucune association trouvée."}), 404

        publication = Publication.query.filter_by(id_publication=id, id_association=association.id_association).first()

        if not publication:
            return jsonify({"error": "Publication introuvable ou non autorisée."}), 404

        data = request.get_json()
        titre = data.get("titre")
        contenu = data.get("contenu")

        if titre:
            publication.titre = titre.strip()
        if contenu:
            publication.contenu = contenu.strip()

        db.session.commit()

        return jsonify({"message": "✅ Publication modifiée avec succès."}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# delete publication
@app.route("/delete-publication/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_publication(id):
    try:
        claims = get_jwt()
        if claims.get("role") != "association":
            return jsonify({"error": "Access denied: only associations can delete publications."}), 403

        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        association = Association.query.filter_by(email=user.email).first()
        if not association:
            return jsonify({"error": "Aucune association trouvée."}), 404

        publication = Publication.query.filter_by(id_publication=id, id_association=association.id_association).first()

        if not publication:
            return jsonify({"error": "Publication introuvable ou non autorisée."}), 404

        db.session.delete(publication)
        db.session.commit()

        return jsonify({"message": "✅ Publication supprimée avec succès."}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500





# add commentaire en tant que donateur

@app.route("/add-comment/<int:publication_id>", methods=["POST"])
@jwt_required()
def add_comment(publication_id):
    try:
        claims = get_jwt()
        if claims.get("role") != "donator":
            return jsonify({"error": "Access denied: only donators can comment."}), 403

        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        publication = Publication.query.get(publication_id)
        if not publication:
            return jsonify({"error": "Publication non trouvée."}), 404

        data = request.get_json()
        contenu_commentaire = data.get("contenu")

        if not contenu_commentaire or not contenu_commentaire.strip():
            return jsonify({"error": "Le contenu du commentaire est requis."}), 400

        # Analyse sentiment avec VADER
        # Analyse sentiment
        scores = analyze_comment_fr(contenu_commentaire)
        sentiment_label = scores["label"]



        new_comment = Commentaire(
            contenu=contenu_commentaire.strip(),
            date_commentaire=datetime.utcnow().date(),
            sentiment=sentiment_label,
            id_publication=publication_id,
            id_user=current_user_id
        )

        db.session.add(new_comment)

        notif = Notification(
            contenu=f"Nouveau 💬 à {publication.titre} : {contenu_commentaire.strip()}",
            date=datetime.utcnow(),
            id_association=publication.id_association
        )
        db.session.add(notif)
        publication.nb_commentaires += 1
        db.session.commit()

        return jsonify({"message": "✅ Commentaire ajouté avec succès.", "sentiment": sentiment_label}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
@app.route("/reply-comment/<int:comment_id>", methods=["POST"])
@jwt_required()
def reply_comment(comment_id):
    try:
        claims = get_jwt()
        if claims.get("role") != "association":
            return jsonify({"error": "Accès refusé : seules les associations peuvent répondre."}), 403

        # Récupération "user" (compte de l'association)
        current_user_id = get_jwt_identity()
        assoc_user = User.query.get(current_user_id)
        if not assoc_user:
            return jsonify({"error": "Utilisateur introuvable."}), 404

        parent = Commentaire.query.get(comment_id)
        if not parent:
            return jsonify({"error": "Commentaire parent introuvable."}), 404

        publication = Publication.query.get(parent.id_publication)
        if not publication:
            return jsonify({"error": "Publication introuvable."}), 404

        # Vérifier propriété de la publication par cette association
        assoc = Association.query.filter_by(email=claims.get("email")).first()
        if not assoc or publication.id_association != assoc.id_association:
            return jsonify({"error": "Vous ne pouvez répondre qu'aux commentaires de vos publications."}), 403

        data = request.get_json()
        contenu = (data.get("contenu") or "").strip()
        if not contenu:
            return jsonify({"error": "Le contenu de la réponse est requis."}), 400

        # Optionnel: analyser le sentiment de la réponse
        try:
            scores = analyze_comment_fr(contenu)
            sentiment_label = scores["label"]
        except Exception:
            sentiment_label = None

        # Créer la réponse
        reply = Commentaire(
            contenu=contenu,
            date_commentaire=datetime.utcnow().date(),
            sentiment=sentiment_label,
            id_publication=parent.id_publication,
            id_user=current_user_id,          # l’auteur est le compte "User" de l’association
            parent_comment_id=parent.id_commentaire
        )
        db.session.add(reply)

        # Incrémenter le nombre total de commentaires de la publication
        publication.nb_commentaires = (publication.nb_commentaires or 0) + 1

        # Notifier l’auteur du commentaire parent (souvent un donateur)
        try:
            if parent.id_user:
                contenu_notif = f"L'association {assoc.nom_complet} a répondu à votre commentaire sur « {publication.titre} »."
                notif = Notification(
                    contenu=contenu_notif,
                    date=datetime.utcnow(),
                    is_read=False,
                    id_association=assoc.id_association,
                    id_publication=publication.id_publication,
                    id_user=parent.id_user  # cible = l’auteur du commentaire parent
                )
                db.session.add(notif)
        except Exception:
            pass

        db.session.commit()
        return jsonify({"message": "✅ Réponse publiée avec succès."}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
def serialize_comment_tree(comment: Commentaire, current_user_id: int | None = None):
    user = User.query.get(comment.id_user) if comment.id_user else None
    return {
        "id_commentaire": comment.id_commentaire,
        "id_user": comment.id_user,  # 👈 utile côté front
        "is_owner": (current_user_id is not None and comment.id_user == int(current_user_id)),
        "contenu": comment.contenu,
        "date_commentaire": comment.date_commentaire.isoformat(),
        "sentiment": comment.sentiment,
        "auteur": user.nom_complet if user else "Utilisateur",
        "role_auteur": user.role if user else None,
        "replies": [
            serialize_comment_tree(r, current_user_id)
            for r in sorted(comment.replies, key=lambda x: x.id_commentaire)
        ]
    }

def create_notification_for_publication(association_id: int, publication_id: int, contenu: str, user_id: int | None = None):
    notif = Notification.query.filter_by(
        id_association=association_id,
        id_publication=publication_id,
        id_don=None,
        contenu=contenu
    ).first()
    if notif:
        return notif

    notif = Notification(
        id_association=association_id,
        id_publication=publication_id,
        id_don=None,
        contenu=contenu,
        id_user=user_id
    )
    db.session.add(notif)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        # race-safety: re-fetch if unique constraint hit
        notif = Notification.query.filter_by(
            id_association=association_id,
            id_publication=publication_id,
            id_don=None,
            contenu=contenu
        ).first()
    return notif


def create_notification_for_don(association_id: int, don_id: int, contenu: str, user_id: int | None = None):
    notif = Notification.query.filter_by(
        id_association=association_id,
        id_publication=None,
        id_don=don_id,
        contenu=contenu
    ).first()
    if notif:
        return notif

    notif = Notification(
        id_association=association_id,
        id_publication=None,
        id_don=don_id,
        contenu=contenu,
        id_user=user_id
    )
    db.session.add(notif)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        notif = Notification.query.filter_by(
            id_association=association_id,
            id_publication=None,
            id_don=don_id,
            contenu=contenu
        ).first()
    return notif

#get notification (association)

@app.route("/notifications", methods=["GET"])
@jwt_required()
def get_notifications():
    claims = get_jwt()
    if claims.get("role") != "association":
        return jsonify({"error": "Access denied!"}), 403

    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    # 🟢 Récupère l'association directement par id_admin si user.role == association
    association = Association.query.filter_by(email=user.email).first()

    if not association:
        return jsonify({"error": "Association not found"}), 404

    notifs = Notification.query.filter_by(id_association=association.id_association).order_by(Notification.date.desc()).all()
    return jsonify([
        {
            "id": n.id,
            "contenu": n.contenu,
            "date": n.date.isoformat(),
            "is_read": n.is_read
        }
        for n in notifs
    ])


#notification donateur

@app.route("/notifications-donator", methods=["GET"])
@jwt_required()
def get_notifications_donator():
    claims = get_jwt()
    if claims.get("role") != "donator":
        return jsonify({"error": "Access denied!"}), 403

    current_user_id = get_jwt_identity()

    notifs = Notification.query.filter_by(id_user=current_user_id).order_by(Notification.date.desc()).all()
    return jsonify([
        {
            "id": n.id,
            "contenu": n.contenu,
            "date": n.date.isoformat(),
            "is_read": n.is_read
        }
        for n in notifs
    ])




#paiement avec API flouci
@app.route("/pay-flouci", methods=["POST"])
@jwt_required()
def pay_flouci():
    try:
        data = request.get_json()
        amount = data.get("amount")

        origin = data.get("origin","web")

        if not amount:
            return jsonify({"error": "Montant requis."}), 400

        amount_millimes = int(float(amount) * 1000)

        if origin == "mobile":
            success_link = "http://localhost:8100/#/success"
            fail_link= "http://localhost:8100/#/fail"
        else:
            success_link = "http://localhost:4200/#/success"  
            fail_link = "http://localhost:4200/#/fail"

        payload = {
            "app_token": "b4af24ad-5d18-4eda-9299-c86beb4dd9e4",      
            "app_secret": "4a249c02-181c-4bd5-b350-542a99a4ffc7",    
            "amount": str(amount_millimes),
            "accept_card": "true",
            "session_timeout_secs": 1200,
            "success_link": success_link, 
            "fail_link": fail_link,
            "developer_tracking_id": "donbyuib-20240423"
        }

        headers = {
            "Content-Type": "application/json"
        }

        url = "https://developers.flouci.com/api/generate_payment"

        # 1️⃣ Appel à Flouci
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code in [200, 201]:
            flouci_result = response.json()
            payment_id = flouci_result.get("result", {}).get("payment_id")
            payment_link = flouci_result.get("result", {}).get("link")

            # 2️⃣ On ajoute le payment_id comme paramètre à la fin du lien
            if payment_id and payment_link:
                # Ajoute payment_id à la query string du lien de paiement Flouci (option recommandé)
                # -> Surtout à utiliser dans success_link côté Flouci dashboard, ou passer payment_id à Angular !
                redirect_link = f"{payment_link}?payment_id={payment_id}"
                return jsonify({"result": {"link": redirect_link, "payment_id": payment_id}}), 200
            else:
                return jsonify({"error": "Payment ID ou lien non reçu de Flouci"}), 500
        else:
            return jsonify({"error": response.text}), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    
# pour vérifier le paiement qui a été bien effectué

@app.route("/verify-flouci-payment/<payment_id>", methods=["GET"])
def verify_flouci_payment(payment_id):
    try:
        url = f"https://developers.flouci.com/api/verify_payment/{payment_id}"

        headers = {
            'Content-Type': 'application/json',
            'apppublic': "b4af24ad-5d18-4eda-9299-c86beb4dd9e4",   # Mets ici ton app_token (public)
            'appsecret': "4a249c02-181c-4bd5-b350-542a99a4ffc7"   # Mets ici ton app_secret (privé)
        }

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            # Exemple : {'success': True, 'result': {'status': 'SUCCESS', ...}}
            return jsonify(data), 200
        else:
            return jsonify({"error": response.text}), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500


           

# faire like à une publication
@app.route("/like-publication/<int:publication_id>", methods=["POST"])
@jwt_required()
def like_publication(publication_id):
    try:
        claims = get_jwt()
        if claims.get("role") not in ["donator", "admin","association"]:
            return jsonify({"error": "Seuls les utilisateurs peuvent liker."}), 403

        publication = Publication.query.get(publication_id)
        if not publication:
            return jsonify({"error": "Publication non trouvée."}), 404

        publication.nb_likes += 1
        db.session.commit()

        return jsonify({"message": "👍 Publication likée", "nb_likes": publication.nb_likes}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# analyser sentiment d'un donateur

import re
from functools import lru_cache
from typing import Dict, Any

from deep_translator import GoogleTranslator
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# ---- 1) Instances globales pour éviter les réallocations
ANALYZER = SentimentIntensityAnalyzer()

# ---- 2) Lexiques FR (mots entiers, avec variations accentuées)
POS_FR_PATTERNS = [
    r"\bbravo\b",
    r"\bmerci\b",
    r"\bparfait\b",
    r"\bg[ée]nial[e]?\b",
    r"\bf[ée]licitations?\b",
    r"\bsuper\b",
    r"\bexcellent[e]?\b",
    r"\btop\b",
    r"\bformidable\b",
    r"\bmeilleur[e]?\b",
    r"\bbonne?\b",
    r"\bbon courage\b",
    r"\baider?\b",
]
NEG_FR_PATTERNS = [
    r"\bpas\s+\w+",         # exp: "pas bien", "pas génial"
    r"\bd[ée]çu[e]?\b",
    r"\bmauvais[e]?\b",
    r"\bd[ée]sastreux(se)?\b",
    r"\bcatastrophique\b",
    r"\bannul[ée]?\b",
    r"\bretard[s]?\b",
    r"\bprobl[èe]me[s]?\b",
    r"\bhorrible\b",
    r"\bd[ée]sagr[ée]able\b",
]

POS_RE = [re.compile(p, flags=re.IGNORECASE) for p in POS_FR_PATTERNS]
NEG_RE = [re.compile(p, flags=re.IGNORECASE) for p in NEG_FR_PATTERNS]

# ---- 3) Traduction avec cache (accélère et limite les appels API)
@lru_cache(maxsize=2048)
def _translate_to_en(text: str) -> str:
    # deep_translator détecte automatiquement la langue source
    return GoogleTranslator(source="auto", target="en").translate(text)

def _label_from_vader_compound(c: float) -> str:
    # Seuils classiques de VADER
    if c >= 0.05:
        return "positif"
    if c <= -0.05:
        return "négatif"
    return "neutre"

def analyze_comment_fr(comment_text: str) -> Dict[str, Any]:
    
    original = (comment_text or "").strip()

    # 1) Traduction (avec fallback si l'appel échoue)
    try:
        translated = _translate_to_en(original) if original else ""
    except Exception:
        translated = original  # fallback : mieux vaut analyser le texte brut que planter

    # 2) Scores VADER sur la version anglaise (ou fallback)
    scores = ANALYZER.polarity_scores(translated)

    # 3) Règles FR (prioritaires si signaux forts)
    #    - D'abord signaux négatifs (ex: "pas bon", "déçu") pour éviter faux positifs
    if original:
        if any(r.search(original) for r in NEG_RE):
            label = "négatif"
        elif any(r.search(original) for r in POS_RE):
            label = "positif"
        else:
            label = _label_from_vader_compound(scores["compound"])
    else:
        label = "neutre"

    return {
        **scores,
        "translated": translated,
        "label": label,
    }

# ---- 4) Option: simple étiquette directement
def get_sentiment_label_fr(comment_text: str) -> str:
    res = analyze_comment_fr(comment_text)
    return res["label"]



# get paiements (donateur)
@app.route("/mes-paiements", methods=["GET"])
@jwt_required()
def get_paiements_donator():
    try:
        claims = get_jwt()
        if claims.get("role") != "donator":
            return jsonify({"error": "Accès refusé"}), 403

        current_user_id = get_jwt_identity()

        participations = Participation.query.filter_by(id_user=current_user_id).join(Don).all()
        result = []
        for p in participations:
            result.append({
                "id_participation": p.id_participation,
                "titre_don": p.don.titre,
                "montant": p.montant,
                "date": p.date_participation.isoformat(),
                "photo_don": p.don.photo_don
            })

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# cette fonction permet à l'association de voir le donateur qui a fait les dons
@app.route("/paiements-association", methods=["GET"])
@jwt_required()
def get_paiements_association():
    try:
        claims = get_jwt()
        if claims.get("role") != "association":
            return jsonify({"error": "Accès refusé"}), 403

        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        association = Association.query.filter_by(email=user.email).first()

        if not association:
            return jsonify({"error": "Association introuvable."}), 404

        # Tous les dons de cette association
        dons_ids = [don.id_don for don in association.dons]

        participations = Participation.query.filter(Participation.id_don.in_(dons_ids)).all()

        result = []
        for p in participations:
            result.append({
                "id_participation": p.id_participation,
                "titre_don": p.don.titre,
                "montant": p.montant,
                "date": p.date_participation.isoformat(),
                "donateur": p.user.nom_complet if p.user else "Utilisateur inconnu"
            })

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# participation du donateur
@app.route("/mes-participations", methods=["GET"])
@jwt_required()
def mes_participations():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if user.role != "donator":
        return jsonify({"error": "Accès refusé"}), 403

    participations = Participation.query.filter_by(id_user=current_user_id).all()

    result = []
    for p in participations:
        result.append({
            "id_participation": p.id_participation,
            "montant": p.montant,
            "date_participation": p.date_participation.strftime('%d/%m/%Y'),
            "don": {
                "id_don": p.don.id_don,
                "titre": p.don.titre,
                "photo_don": p.don.photo_don
            }
        })

    return jsonify(result), 200

#recu de paiement (vu par donateur et association)
from flask import make_response, jsonify

from io import BytesIO
import base64, os
from flask_jwt_extended import jwt_required, get_jwt_identity
 

@app.route('/recu-pdf/<int:id_participation>', methods=['GET'])
@jwt_required()
def generate_recu_pdf(id_participation):
    try:
        from xhtml2pdf import pisa   
    except Exception as e:
        return jsonify({"error": "PDF engine not available", "details": str(e)}), 503
    participation = Participation.query.get(id_participation)
    if not participation:
        return jsonify({"error": "Participation introuvable"}), 404

    don = participation.don
    user = participation.user
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)


    # 📷 Logo UIB
    logo_path = os.path.join(app.root_path, 'static', 'uploads', 'uiblogo.png')
    with open(logo_path, "rb") as image_file:
        logo_base64 = base64.b64encode(image_file.read()).decode("utf-8")

    # ✅ Génération du HTML du reçu
    html = f"""
    <html>
      <head>
      <meta charset="utf-8" />
        <style>
          body {{ font-family: Arial, sans-serif; padding: 20px; }}
          .header {{ text-align: center; }}
          .logo {{ width: 100px; }}
          .content {{ margin-top: 30px; }}
          .section {{ margin-bottom: 10px; }}
          .footer {{ text-align: center; margin-top: 50px; font-size: 12px; color: #555; }}
        </style>
      </head>
      <body>
        <div class="header">
          <img class="logo" src="data:image/png;base64,{logo_base64}" />
          <h2 style="color: #e53935;">Reçu de Paiement - DonByUIB</h2>
        </div>

        <div class="content">
          <div class="section"><strong>Nom du Donateur :</strong> {user.nom_complet}</div>
          <div class="section"><strong>Email :</strong> {user.email}</div>
          <div class="section"><strong>Campagne :</strong> {don.titre}</div>
          <div class="section"><strong>Montant :</strong> {participation.montant} TND</div>
          <div class="section"><strong>Date :</strong> {participation.date_participation.strftime('%d/%m/%Y')}</div>
        </div>

        <div class="footer">
          Ce reçu est généré automatiquement par DonByUIB.<br>
          Merci pour votre soutien et votre générosité.
        </div>
      </body>
    </html>
    

      """

    # ✅ Génération du PDF
    buffer = BytesIO()
    pisa_status = pisa.CreatePDF(BytesIO(html.encode('utf-8')), dest=buffer)
    if pisa_status.err:
        return jsonify({"error": "Erreur lors de la génération du PDF"}), 500

    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=recu_{id_participation}.pdf'
    return response


# historique du donateur 

@app.route("/historique-donateur", methods=["GET"])
@jwt_required()
def get_historique_donateur():
    try:
        claims = get_jwt()
        if claims.get("role") != "donator":
            return jsonify({"error": "Accès refusé"}), 403

        current_user_id = get_jwt_identity()

        # Récupérer participations
        participations = Participation.query.filter_by(id_user=current_user_id).join(Don).all()
        dons = [{
            "type": "don",
            "titre_don": p.don.titre,
            "montant": p.montant,
            "date": p.date_participation.isoformat(),
            "photo_don": p.don.photo_don
        } for p in participations]

        # Récupérer commentaires
        commentaires = Commentaire.query.filter_by(id_user=current_user_id).join(Publication).all()
        comments = [{
            "type": "commentaire",
            "publication": c.publication.titre,
            "contenu": c.contenu,
            "date": c.date_commentaire.isoformat(),
            "sentiment": c.sentiment
        } for c in commentaires]

        historique = sorted(dons + comments, key=lambda x: x['date'], reverse=True)

        return jsonify(historique), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    



# stat admin

@app.route("/admin/statistiques", methods=["GET"])
@jwt_required()
def get_admin_stats():
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Accès refusé"}), 403

    try:
        # ✅ Comptage par type d'association
        types = [t.value for t in TypeAssociationEnum]
        association_par_type = {}

        for t in types:
            count = Association.query.filter_by(type_association=TypeAssociationEnum(t)).count()
            association_par_type[t] = count


        # ✅ Nombre total d'associations (somme des types)
        nb_associations = sum(association_par_type.values())

        # ✅ Autres statistiques
        nb_dons = Don.query.count()
        total_montant = db.session.query(db.func.sum(Don.montant_collecte)).scalar() or 0.0
        nb_dons_reussis = Don.query.filter_by(is_reussi=True).count()

        # Répartition des dons par statut
        nb_en_attente = Don.query.filter_by(statut="en_attente").count()
        nb_valides = Don.query.filter_by(statut="valide").count()
        nb_refuses = Don.query.filter_by(statut="refuse").count()

        # Top 5 dons les plus financés
        top_dons = Don.query.order_by(Don.montant_collecte.desc()).limit(5).all()
        top_dons_data = [
            {"titre": d.titre, "montant_collecte": d.montant_collecte, "objectif": d.objectif}
            for d in top_dons
        ]

        # Montant collecté par mois (12 mois)
        montant_par_mois = []
        for m in range(1, 13):
            montant = db.session.query(db.func.sum(Participation.montant))\
                .filter(db.extract('month', Participation.date_participation) == m)\
                .scalar() or 0.0
            montant_par_mois.append(montant)

        # Publications validées et refusées
        nb_pub_valides = Publication.query.filter_by(statut="valide").count()
        nb_pub_refusees = Publication.query.filter_by(statut="refuse").count()

        # Donateurs actifs (distinct)
        nb_donateurs_actifs = db.session.query(Participation.id_user).distinct().count()

        return jsonify({
            "nb_associations": nb_associations,
            "association_par_type": association_par_type,
            "nb_dons": nb_dons,
            "total_montant": total_montant,
            "nb_dons_reussis": nb_dons_reussis,
            "nb_en_attente": nb_en_attente,
            "nb_valides": nb_valides,
            "nb_refuses": nb_refuses,
            "top_dons": top_dons_data,
            "montant_par_mois": montant_par_mois,
            "nb_pub_valides": nb_pub_valides,
            "nb_pub_refusees": nb_pub_refusees,
            "nb_donateurs_actifs": nb_donateurs_actifs
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
# signup verification 
# add these imports
import json
import uuid

# (existing)
from flask import Flask, request, jsonify
from transformers import CLIPProcessor, CLIPModel
import torch
from PIL import Image
import numpy as np
from facenet_pytorch import MTCNN, InceptionResnetV1


# === Configuration & model setup (as before) ===
MODEL_NAME      = "openai/clip-vit-base-patch32"
DOC_CANDIDATES  = [
    "a photo of a Tunisian national identity card",
    "a photo of a driver's license",
    "a photo of a passport",
    "a photo of a fake document"
]
FLAG_CANDIDATES = [
    "a photo of the flag of Tunisia",
    "not a flag"
]
DOC_THRESHOLD   = 0.30
FLAG_THRESHOLD  = 0.30

# NEW: face match threshold (cosine similarity). Tune on your data.
FACE_MATCH_THRESHOLD = 0.65

# In-memory store mapping session_id -> embedding (np.float32, L2-normalized)
SESSIONS = {}

device    = "cuda" if torch.cuda.is_available() else "cpu"
processor = CLIPProcessor.from_pretrained(MODEL_NAME)
model     = CLIPModel.from_pretrained(MODEL_NAME).to(device)

# NEW: face models (MTCNN for detection+alignment, IR-ResNet for embeddings)
mtcnn = MTCNN(keep_all=True, device=device, thresholds=[0.6, 0.7, 0.7])  # tweak if CIN faces are small
face_encoder = InceptionResnetV1(pretrained="vggface2").eval().to(device)

def _get_face_embedding(pil_img: Image.Image):
    """
    Returns (embedding_list, metadata) or (None, reason)
    """
    # 1) detect boxes to pick the largest face (usually the portrait on the ID)
    boxes, probs = mtcnn.detect(pil_img)
    if boxes is None or len(boxes) == 0:
        return None, "no_face_detected"

    # choose largest bounding box by area
    areas = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
    idx = int(np.argmax(areas))

    # 2) get aligned face crops (MTCNN forward returns aligned 160x160 tensors)
    faces = mtcnn(pil_img)  # may be None or tensor
    if faces is None:
        return None, "alignment_failed"

    # normalize shape & select the chosen index
    if faces.ndim == 3:
        faces = faces.unsqueeze(0)  # [1,3,160,160]
    if idx >= faces.shape[0]:
        idx = 0  # fallback

    face = faces[idx].unsqueeze(0).to(device)  # [1,3,160,160]

    # 3) encode as 512-D, L2-normalized
    with torch.no_grad():
        emb = face_encoder(face)                    # [1,512]
        emb = torch.nn.functional.normalize(emb)    # L2 norm
    embedding = emb.squeeze(0).cpu().tolist()

    meta = {
        "bbox": [float(x) for x in boxes[idx].tolist()],
        "prob": float(probs[idx]) if probs is not None else None,
        "dim": 512
    }
    return embedding, meta


@app.route("/verify-cin", methods=["POST"])
def verify_cin():
    # 1. Validate upload under 'cin'
    if "cin" not in request.files:
        return jsonify(False), 400
    file = request.files["cin"]
    if file.filename == "":
        return jsonify(False), 400

    # 2. Load image
    try:
        img = Image.open(file.stream).convert("RGB")
    except Exception:
        return jsonify(False), 400

    # 3. Document classification
    doc_inputs = processor(
        text=DOC_CANDIDATES,
        images=img,
        return_tensors="pt",
        padding=True
    ).to(device)
    with torch.no_grad():
        doc_logits = model(**doc_inputs).logits_per_image
        doc_probs  = doc_logits.softmax(dim=-1)[0].cpu().tolist()
    doc_results = dict(zip(DOC_CANDIDATES, doc_probs))
    best_doc    = max(doc_results, key=doc_results.get)
    is_identity = (
        best_doc == DOC_CANDIDATES[0]
        and doc_results[best_doc] >= DOC_THRESHOLD
    )

    # 4. Flag detection
    flag_inputs = processor(
        text=FLAG_CANDIDATES,
        images=img,
        return_tensors="pt",
        padding=True
    ).to(device)
    with torch.no_grad():
        flag_logits = model(**flag_inputs).logits_per_image
        flag_probs  = flag_logits.softmax(dim=-1)[0].cpu().tolist()
    flag_results = dict(zip(FLAG_CANDIDATES, flag_probs))
    best_flag    = max(flag_results, key=flag_results.get)
    is_flag      = (
        best_flag == FLAG_CANDIDATES[0]
        and flag_results[best_flag] >= FLAG_THRESHOLD
    )

    # 5. Final decision
    final_decision = is_identity and is_flag

    # 6. If valid, extract face embedding from the CIN
    if final_decision:
        embedding, info = _get_face_embedding(img)
        if embedding is None:
            return jsonify({"ok": True, "embedding": None, "reason": info}), 422

        # --- store server-side and return a session_id (recommended) ---
        session_id = str(uuid.uuid4())
        SESSIONS[session_id] = np.asarray(embedding, dtype=np.float32)

        # NOTE: You can choose to NOT return the raw embedding to clients.
        return jsonify({
            "ok": True,
            "session_id": session_id,
            "meta": info,
            "doc_score": doc_results.get(best_doc, None),
            "flag_score": flag_results.get(best_flag, None)
            # "embedding": embedding,  # <— uncomment only if you really want to return it
        }), 200

    # 7. Otherwise, reject as before
    return jsonify(False), 400


# --- NEW: selfie verification route ---
@app.route("/verifyface", methods=["POST"])
@app.route("/verify-face", methods=["POST"])  # alias
def verify_face():
    """
    Form-data:
      - selfie: file (required)
      - session_id: str (optional, preferred) OR
      - embedding: JSON array or comma-separated floats (optional, if not using session)
    Returns match decision + similarity score.
    """
    # 1) Validate selfie upload
    if "selfie" not in request.files:
        return jsonify({"ok": False, "reason": "missing_selfie"}), 400
    selfie_file = request.files["selfie"]
    if selfie_file.filename == "":
        return jsonify({"ok": False, "reason": "empty_selfie_filename"}), 400

    # 2) Load selfie
    try:
        selfie_img = Image.open(selfie_file.stream).convert("RGB")
    except Exception:
        return jsonify({"ok": False, "reason": "bad_selfie_image"}), 400

    # 3) Get reference CIN embedding
    ref_embedding = None
    session_id = request.form.get("session_id")
    emb_str = request.form.get("embedding")  # JSON array or CSV floats

    if session_id:
        ref_embedding = SESSIONS.get(session_id)
        if ref_embedding is None:
            return jsonify({"ok": False, "reason": "unknown_session"}), 404
    elif emb_str:
        try:
            if emb_str.strip().startswith("["):
                ref_list = json.loads(emb_str)
            else:
                ref_list = [float(x) for x in emb_str.split(",")]
            ref_embedding = np.asarray(ref_list, dtype=np.float32)
        except Exception:
            return jsonify({"ok": False, "reason": "bad_embedding_format"}), 400
    else:
        return jsonify({"ok": False, "reason": "missing_reference_embedding"}), 400

    # 4) Create selfie embedding
    selfie_emb, selfie_meta = _get_face_embedding(selfie_img)
    if selfie_emb is None:
        return jsonify({"ok": False, "reason": selfie_meta}), 422
    selfie_emb = np.asarray(selfie_emb, dtype=np.float32)

    # 5) Cosine similarity (safe-normalize even though emb is already L2-normalized)
    ref = ref_embedding / (np.linalg.norm(ref_embedding) + 1e-12)
    qry = selfie_emb / (np.linalg.norm(selfie_emb) + 1e-12)
    score = float(np.dot(ref, qry))  # in [-1, 1], higher is more similar

    is_match = bool(score >= FACE_MATCH_THRESHOLD)

    return jsonify({
        "ok": True,
        "match": is_match,
        "score": score,
        "threshold": FACE_MATCH_THRESHOLD,
        "selfie_meta": selfie_meta,
        "session_id": session_id
    }), 200

# ------------------- ADD ADMIN -------------------
@app.route("/add-admin", methods=["POST"])
def add_admin():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    # check if email already exists
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already in use"}), 409

    # create admin
    admin = User(email=email, role="admin")
    admin.set_password(password)

    db.session.add(admin)
    db.session.commit()

    return jsonify({
        "message": "Admin created successfully",
        "id": admin.id,
        "email": admin.email
    }), 201


# ------------------- DATABASE MIGRATION -------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)   
