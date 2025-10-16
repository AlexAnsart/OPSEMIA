import os
import csv
from PIL import Image, ExifTags

# === CONFIGURATION ===
DOSSIER_IMAGES = "CLIC"  # ton dossier d'images
FICHIER_CSV = "infos_images.csv"

# === EXTENSIONS ACCEPTÉES ===
EXTENSIONS_AUTORISEES = (".jpg", ".jpeg", ".png", ".tiff", ".bmp", ".webp")

# --- EXTRACTION EXIF ---
def lire_exif(image_path):
    """Lit les données EXIF d'une image (si elles existent)."""
    try:
        image = Image.open(image_path)
        exif_data = getattr(image, "_getexif", lambda: None)()
        if not exif_data:
            return {}
        return {ExifTags.TAGS.get(tag, tag): val for tag, val in exif_data.items()}
    except Exception:
        return {}

def convertir_coord(coord):
    """Convertit les coordonnées EXIF en degrés décimaux."""
    try:
        d, m, s = coord
        return d[0] / d[1] + m[0] / m[1] / 60 + s[0] / s[1] / 3600
    except Exception:
        return None

def lire_gps(exif):
    """Retourne (latitude, longitude) si GPSInfo existe."""
    gps_info = exif.get("GPSInfo")
    if not gps_info:
        return None, None
    gps_data = {ExifTags.GPSTAGS.get(t, t): gps_info[t] for t in gps_info}
    try:
        lat = convertir_coord(gps_data["GPSLatitude"])
        lon = convertir_coord(gps_data["GPSLongitude"])
        if gps_data.get("GPSLatitudeRef") == "S":
            lat = -lat
        if gps_data.get("GPSLongitudeRef") == "W":
            lon = -lon
        return lat, lon
    except Exception:
        return None, None

def lire_date_heure(exif):
    """Retourne (date, heure) si EXIF contient DateTimeOriginal."""
    dt = exif.get("DateTimeOriginal", "")
    if dt:
        try:
            date, heure = dt.split(" ")
            return date.replace(":", "-"), heure
        except Exception:
            return dt, ""
    return "", ""

# --- TRAITEMENT DES IMAGES ---
if not os.path.exists(DOSSIER_IMAGES):
    print(f"❌ Le dossier '{DOSSIER_IMAGES}' n'existe pas.")
    exit()

fichiers = [f for f in os.listdir(DOSSIER_IMAGES) if f.lower().endswith(EXTENSIONS_AUTORISEES)]

if not fichiers:
    print(f"❌ Aucune image trouvée dans '{DOSSIER_IMAGES}'.")
    exit()

# --- CRÉATION DU CSV ---
with open(FICHIER_CSV, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["nom_image", "chemin", "date_prise", "heure_prise", "latitude", "longitude"])

    for fichier in fichiers:
        chemin = os.path.join(DOSSIER_IMAGES, fichier)
        exif = lire_exif(chemin)
        date, heure = lire_date_heure(exif)
        lat, lon = lire_gps(exif)

        # Messages console utiles
        if not exif:
            print(f"⚠️  {fichier}: aucune donnée EXIF (souvent PNG/WEBP ou modifiée).")
        else:
            print(f"📸 {fichier} → date={date or 'N/A'}, heure={heure or 'N/A'}, lat={lat or 'N/A'}, lon={lon or 'N/A'}")

        writer.writerow([fichier, chemin, date, heure, lat, lon])

print(f"\n✅ Fichier CSV créé avec succès : {FICHIER_CSV}")
