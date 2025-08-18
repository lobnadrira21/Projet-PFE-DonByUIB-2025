import pandas as pd
from app import app, db
from app import Gouvernorat  

with app.app_context():
    try:
        df = pd.read_excel("D:/codes_tunisie.xlsx")  
        unique_names = df['nomGouvernorat'].dropna().unique()

        inserted = 0
        for nom in unique_names:
            if not Gouvernorat.query.filter_by(nomGouvernorat=nom).first():
                db.session.add(Gouvernorat(nomGouvernorat=nom))
                inserted += 1

        db.session.commit()
        print(f"✅ {inserted} gouvernorats insérés avec succès.")
    except Exception as e:
        print(f"❌ Une erreur est survenue : {e}")
