"""Script pour nettoyer le cache des modèles PyTorch."""

import shutil
from pathlib import Path

def nettoyer_cache():
    """Supprime les caches PyTorch et transformers."""
    
    # Cache transformers
    cache_transformers = Path.home() / ".cache" / "huggingface"
    
    # Cache torch
    cache_torch = Path.home() / ".cache" / "torch"
    
    print("🧹 Nettoyage des caches de modèles...")
    
    caches_nettoyes = []
    
    # Nettoyer seulement les fichiers temporaires, pas les modèles téléchargés
    for cache_dir in [cache_transformers, cache_torch]:
        if cache_dir.exists():
            temp_dirs = ["tmp", "temp", ".locks"]
            for temp_name in temp_dirs:
                temp_path = cache_dir / temp_name
                if temp_path.exists():
                    try:
                        if temp_path.is_dir():
                            shutil.rmtree(temp_path)
                        else:
                            temp_path.unlink()
                        caches_nettoyes.append(str(temp_path))
                        print(f"  ✓ Supprimé: {temp_path}")
                    except Exception as e:
                        print(f"  ⚠️  Erreur lors de la suppression de {temp_path}: {e}")
    
    if caches_nettoyes:
        print(f"\n✅ {len(caches_nettoyes)} cache(s) nettoyé(s)")
    else:
        print("\n✅ Aucun cache temporaire à nettoyer")
    
    print("\n💡 Conseil: Redémarrez le serveur après ce nettoyage")

if __name__ == "__main__":
    nettoyer_cache()

