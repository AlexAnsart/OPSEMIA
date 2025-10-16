/**
 * Module de gestion de la galerie d'images OPSEMIA
 */

// État de la galerie
const galerieState = {
    collection: 'images',
    images: [],
    imageSelectionnee: null,
};

/**
 * Initialise la page de galerie
 */
function initGalerie() {
    // Charger les collections disponibles
    chargerCollectionsGalerie();
    
    // Charger la galerie
    chargerGalerie();
    
    // Événements
    document.getElementById('collection-select')?.addEventListener('change', (e) => {
        galerieState.collection = e.target.value;
        chargerGalerie();
    });
    
    document.getElementById('tri-select')?.addEventListener('change', () => {
        chargerGalerie();
    });
    
    document.getElementById('limite-select')?.addEventListener('change', () => {
        chargerGalerie();
    });
    
    document.getElementById('btn-refresh')?.addEventListener('click', () => {
        chargerGalerie();
    });
    
    // Modale
    document.getElementById('modal-close')?.addEventListener('click', fermerModaleImage);
    document.getElementById('image-modal')?.addEventListener('click', (e) => {
        if (e.target.id === 'image-modal') {
            fermerModaleImage();
        }
    });
    
    // Fermer avec Échap
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            fermerModaleImage();
        }
    });
    
    // Navigation depuis la recherche
    const navImageId = sessionStorage.getItem('nav_imageId');
    const navCollection = sessionStorage.getItem('nav_collection_images');
    
    if (navImageId && navCollection) {
        galerieState.collection = navCollection;
        sessionStorage.removeItem('nav_imageId');
        sessionStorage.removeItem('nav_collection_images');
        
        // Charger la galerie puis ouvrir l'image
        chargerGalerie().then(() => {
            const image = galerieState.images.find(img => img.id === navImageId);
            if (image) {
                ouvrirModaleImage(image);
            }
        });
    }
}

/**
 * Charge les collections disponibles (filtrer les collections d'images)
 */
async function chargerCollectionsGalerie() {
    try {
        const data = await api.listerCollections();
        
        if (data.succes && data.collections) {
            const select = document.getElementById('collection-select');
            if (!select) return;
            
            // Filtrer pour ne garder que les collections d'images
            const collectionsImages = data.collections.filter(c => 
                c.nom.includes('image') || c.nom.includes('photo')
            );
            
            if (collectionsImages.length === 0) {
                select.innerHTML = '<option value="">Aucune collection d\'images</option>';
                return;
            }
            
            select.innerHTML = collectionsImages.map(c => 
                `<option value="${c.nom}" ${c.nom === galerieState.collection ? 'selected' : ''}>${c.nom} (${c.nombre_documents} images)</option>`
            ).join('');
            
            if (collectionsImages.length > 0 && !collectionsImages.find(c => c.nom === galerieState.collection)) {
                galerieState.collection = collectionsImages[0].nom;
                select.value = galerieState.collection;
            }
        }
    } catch (error) {
        console.error('Erreur chargement collections:', error);
    }
}

/**
 * Charge la galerie d'images
 */
async function chargerGalerie() {
    const container = document.getElementById('galerie-container');
    const countElement = document.getElementById('galerie-count');
    
    if (!container) return;
    
    try {
        afficherChargement('Chargement de la galerie...');
        
        // Récupérer les paramètres
        const tri = document.getElementById('tri-select')?.value || 'chronologique';
        const limite = parseInt(document.getElementById('limite-select')?.value || '500');
        
        // Appeler l'API
        const response = await fetch(
            `${api.baseURL}/api/images/galerie?collection=${galerieState.collection}&tri=${tri}&limite=${limite}`
        );
        
        const data = await response.json();
        
        if (!data.succes) {
            throw new Error(data.erreur || 'Erreur lors du chargement de la galerie');
        }
        
        galerieState.images = data.images || [];
        
        // Afficher le nombre d'images
        if (countElement) {
            countElement.textContent = `${galerieState.images.length} image(s)`;
        }
        
        // Afficher la galerie
        afficherGalerie(galerieState.images);
        
        masquerChargement();
        
    } catch (error) {
        console.error('Erreur chargement galerie:', error);
        masquerChargement();
        container.innerHTML = `
            <div class="alert alert-danger">
                ⚠️ Erreur lors du chargement de la galerie: ${error.message}
            </div>
        `;
    }
}

/**
 * Affiche la galerie d'images
 */
function afficherGalerie(images) {
    const container = document.getElementById('galerie-container');
    if (!container) return;
    
    if (images.length === 0) {
        container.innerHTML = `
            <div class="empty-galerie">
                <div class="empty-galerie-icon">🖼️</div>
                <h3>Aucune image dans cette collection</h3>
                <p class="text-secondary">Indexez des images via la page Configuration pour les voir ici.</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = `
        <div class="galerie-grid">
            ${images.map((img, index) => creerCarteImage(img, index)).join('')}
        </div>
    `;
    
    // Ajouter les événements de clic
    images.forEach((img, index) => {
        const element = document.getElementById(`galerie-item-${index}`);
        if (element) {
            element.addEventListener('click', () => ouvrirModaleImage(img));
        }
    });
}

/**
 * Crée une carte d'image pour la galerie
 */
function creerCarteImage(image, index) {
    const meta = image.metadata || {};
    const nomImage = meta.nom_image || 'Image';
    const timestamp = meta.timestamp || meta.date_prise || '';
    const description = image.description || '';
    
    // Construire l'URL de l'image
    const cheminImage = meta.chemin || meta.nom_image || '';
    const urlImage = `/api/images/servir/${encodeURIComponent(cheminImage)}`;
    
    return `
        <div class="galerie-item" id="galerie-item-${index}">
            <img 
                class="galerie-item-image" 
                src="${urlImage}" 
                alt="${echapperHTML(nomImage)}"
                onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 200 200%22%3E%3Crect fill=%22%23333%22 width=%22200%22 height=%22200%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 fill=%22%23666%22 text-anchor=%22middle%22 dy=%22.3em%22 font-size=%2220%22%3EImage non trouvée%3C/text%3E%3C/svg%3E'"
            >
            <div class="galerie-item-info">
                <div class="galerie-item-nom" title="${echapperHTML(nomImage)}">
                    ${echapperHTML(nomImage)}
                </div>
                <div class="galerie-item-meta">
                    ${timestamp ? `<span>📅 ${formatTimestampCourt(timestamp)}</span>` : ''}
                    ${meta.gps_lat && meta.gps_lon ? `<span>📍 GPS</span>` : ''}
                    ${description ? `<span title="${echapperHTML(description)}">💬 ${echapperHTML(description.substring(0, 40))}${description.length > 40 ? '...' : ''}</span>` : ''}
                </div>
            </div>
        </div>
    `;
}

/**
 * Ouvre la modale avec l'image en plein écran
 */
function ouvrirModaleImage(image) {
    galerieState.imageSelectionnee = image;
    
    const modal = document.getElementById('image-modal');
    const modalImage = document.getElementById('modal-image');
    const modalTitre = document.getElementById('modal-titre');
    const modalMetadata = document.getElementById('modal-metadata');
    const modalDescription = document.getElementById('modal-description');
    
    if (!modal || !modalImage) return;
    
    const meta = image.metadata || {};
    const nomImage = meta.nom_image || 'Image';
    const cheminImage = meta.chemin || meta.nom_image || '';
    const urlImage = `/api/images/servir/${encodeURIComponent(cheminImage)}`;
    
    // Afficher l'image
    modalImage.src = urlImage;
    modalImage.alt = nomImage;
    
    // Titre
    if (modalTitre) {
        modalTitre.textContent = nomImage;
    }
    
    // Métadonnées
    if (modalMetadata) {
        const metadataHTML = [];
        
        if (meta.timestamp || meta.date_prise) {
            const dateStr = meta.timestamp ? formatTimestamp(meta.timestamp) : `${meta.date_prise} ${meta.heure_prise || ''}`;
            metadataHTML.push(`<div><strong>📅 Date:</strong><br>${dateStr}</div>`);
        }
        
        if (meta.gps_lat && meta.gps_lon) {
            metadataHTML.push(`<div><strong>📍 Localisation:</strong><br>Lat: ${meta.gps_lat.toFixed(6)}<br>Lon: ${meta.gps_lon.toFixed(6)}</div>`);
        }
        
        if (meta.chemin) {
            metadataHTML.push(`<div><strong>📁 Chemin:</strong><br><code>${echapperHTML(meta.chemin)}</code></div>`);
        }
        
        modalMetadata.innerHTML = metadataHTML.join('');
    }
    
    // Description
    if (modalDescription) {
        const description = image.description || '';
        if (description) {
            modalDescription.innerHTML = `
                <strong>🤖 Description générée:</strong><br>
                <p style="margin-top: var(--spacing-sm); color: var(--text-primary);">${echapperHTML(description)}</p>
            `;
        } else {
            modalDescription.innerHTML = '';
        }
    }
    
    // Afficher la modale
    modal.classList.add('visible');
}

/**
 * Ferme la modale d'image
 */
function fermerModaleImage() {
    const modal = document.getElementById('image-modal');
    if (modal) {
        modal.classList.remove('visible');
    }
    galerieState.imageSelectionnee = null;
}

/**
 * Affiche le chargement
 */
function afficherChargement(message = 'Chargement...') {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.classList.remove('hidden');
        document.getElementById('loading-message').textContent = message;
    }
}

/**
 * Masque le chargement
 */
function masquerChargement() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.classList.add('hidden');
    }
}

/**
 * Formate un timestamp complet
 */
function formatTimestamp(timestamp) {
    if (!timestamp) return '';
    
    const date = new Date(timestamp);
    const options = { 
        year: 'numeric', 
        month: '2-digit', 
        day: '2-digit', 
        hour: '2-digit', 
        minute: '2-digit' 
    };
    return date.toLocaleString('fr-FR', options);
}

/**
 * Formate un timestamp court
 */
function formatTimestampCourt(timestamp) {
    if (!timestamp) return '';
    
    const date = new Date(timestamp);
    return date.toLocaleDateString('fr-FR', { 
        year: 'numeric', 
        month: '2-digit', 
        day: '2-digit' 
    });
}

/**
 * Échappe le HTML pour éviter les injections
 */
function echapperHTML(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialiser au chargement de la page
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initGalerie);
} else {
    initGalerie();
}

// Exposer pour navigation externe
window.galerieModule = {
    ouvrirModaleImage
};


