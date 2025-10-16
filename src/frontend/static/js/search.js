/**
 * Module de recherche sémantique OPSEMIA
 */

// État de la recherche
const searchState = {
    collections: [],  // Maintenant un tableau de collections
    dernierResultats: [],
    filtresActifs: {}
};

/**
 * Initialise la page de recherche
 */
function initRecherche() {
    // Charger les collections disponibles
    chargerCollections();
    
    // Restaurer l'état de recherche si disponible
    restaurerEtatRecherche();
    
    // Événements
    document.getElementById('search-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        await effectuerRecherche();
    });
    
    document.getElementById('toggle-filters')?.addEventListener('click', toggleFiltres);
    
    // Initialiser les filtres
    document.getElementById('apply-filters')?.addEventListener('click', appliquerFiltres);
    document.getElementById('reset-filters')?.addEventListener('click', reinitialiserFiltres);
}

/**
 * Charge la liste des collections disponibles (checkboxes)
 */
async function chargerCollections() {
    try {
        const data = await api.listerCollections();
        const container = document.getElementById('collections-checkboxes');
        
        if (container && data.collections) {
            // Séparer les collections en 3 catégories
            const collectionsMessages = [];
            const collectionsChunks = [];
            const collectionsImages = [];
            
            data.collections.forEach(col => {
                if (!col.nom || col.nom === 'undefined' || col.nom.trim() === '') {
                    return; // Ignorer les collections invalides
                }
                
                if (col.nom.includes('chunk')) {
                    collectionsChunks.push(col);
                } else if (col.nom.includes('image')) {
                    collectionsImages.push(col);
                } else {
                    collectionsMessages.push(col);
                }
            });
            
            // Trier chaque catégorie
            collectionsMessages.sort((a, b) => a.nom.localeCompare(b.nom));
            collectionsChunks.sort((a, b) => a.nom.localeCompare(b.nom));
            collectionsImages.sort((a, b) => a.nom.localeCompare(b.nom));
            
            // Créer le HTML avec 3 colonnes horizontales
            let html = '<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.4rem;">';
            
            // Section Messages
            if (collectionsMessages.length > 0) {
                html += creerSectionCollection(
                    '💬 MESSAGES',
                    'var(--accent-primary)',
                    collectionsMessages.map(col => creerCheckboxCollection(col, true)).join('')
                );
            } else {
                html += '<div></div>'; // Colonne vide
            }
            
            // Section Extraits de conversations (chunks)
            if (collectionsChunks.length > 0) {
                html += creerSectionCollection(
                    '💭 EXTRAITS DE CONVERSATIONS',
                    'var(--accent-secondary)',
                    collectionsChunks.map(col => creerCheckboxCollection(col, false)).join('')
                );
            } else {
                html += '<div></div>'; // Colonne vide
            }
            
            // Section Images
            if (collectionsImages.length > 0) {
                html += creerSectionCollection(
                    '🖼️ IMAGES',
                    'var(--text-secondary)',
                    collectionsImages.map(col => creerCheckboxCollection(col, false)).join('')
                );
            } else {
                html += '<div></div>'; // Colonne vide
            }
            
            html += '</div>';
            
            if (collectionsMessages.length === 0 && collectionsChunks.length === 0 && collectionsImages.length === 0) {
                container.innerHTML = '<span style="color: var(--text-secondary);">Aucune collection disponible</span>';
                console.warn('Aucune collection trouvée');
                return;
            }
            
            container.innerHTML = html;
            
            // Initialiser l'état avec la première collection de messages cochée
            searchState.collections = collectionsMessages.length > 0 ? [collectionsMessages[0].nom] : [];
            
            // Ajouter les événements de changement
            const checkboxes = container.querySelectorAll('.collection-checkbox');
            checkboxes.forEach(cb => {
                cb.addEventListener('change', (e) => {
                    if (e.target.checked) {
                        if (!searchState.collections.includes(e.target.value)) {
                            searchState.collections.push(e.target.value);
                        }
                    } else {
                        searchState.collections = searchState.collections.filter(c => c !== e.target.value);
                    }
                    console.log('Collections sélectionnées:', searchState.collections);
                });
                
                // Effet visuel au survol
                cb.parentElement.addEventListener('mouseenter', function() {
                    this.style.background = 'rgba(255, 255, 255, 0.05)';
                });
                cb.parentElement.addEventListener('mouseleave', function() {
                    this.style.background = 'transparent';
                });
            });
            
            console.log('Collections chargées:');
            console.log('  - Messages:', collectionsMessages.map(c => c.nom));
            console.log('  - Chunks:', collectionsChunks.map(c => c.nom));
            console.log('  - Images:', collectionsImages.map(c => c.nom));
            console.log('Collections sélectionnées par défaut:', searchState.collections);
        }
    } catch (error) {
        afficherErreur('Erreur lors du chargement des collections: ' + error.message);
    }
}

/**
 * Crée le HTML pour une section de collections (colonne)
 */
function creerSectionCollection(titre, couleur, contenuCheckboxes) {
    return `
        <div style="
            display: flex; 
            flex-direction: column; 
            gap: 0.3rem;
        ">
            <div style="
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 0.3rem 0.4rem;
                background: ${couleur};
                background: linear-gradient(135deg, ${couleur}15 0%, ${couleur}08 100%);
            ">
                <strong style="
                    color: ${couleur};
                    font-size: 0.68rem;
                    font-weight: 600;
                    letter-spacing: 0.5px;
                    text-transform: uppercase;
                    text-align: center;
                ">${titre}</strong>
            </div>
            <div style="
                display: flex;
                flex-direction: column;
                gap: 0.2rem;
            ">
                ${contenuCheckboxes}
            </div>
        </div>
    `;
}

/**
 * Crée le HTML pour une checkbox de collection
 */
function creerCheckboxCollection(collection, checked = false) {
    const checkedAttr = checked ? 'checked' : '';
    return `
        <label style="
            display: flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.25rem 0.4rem;
            background: transparent;
            border-radius: var(--border-radius);
            cursor: pointer;
            transition: background 0.15s ease;
        ">
            <input 
                type="checkbox" 
                value="${collection.nom}" 
                class="collection-checkbox" 
                ${checkedAttr}
                style="cursor: pointer; flex-shrink: 0;"
            >
            <div style="
                display: flex;
                flex-direction: column;
                gap: 0.05rem;
                flex: 1;
                overflow: hidden;
            ">
                <span style="
                    font-size: 0.78rem;
                    color: var(--text-primary);
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                ">
                    ${collection.nom}
                </span>
                <span style="
                    font-size: 0.68rem;
                    color: var(--text-secondary);
                    font-weight: 500;
                ">${collection.nombre_documents} doc${collection.nombre_documents > 1 ? 's' : ''}</span>
            </div>
        </label>
    `;
}

/**
 * Effectue une recherche sémantique (multi-collections)
 */
async function effectuerRecherche() {
    const requete = document.getElementById('search-input')?.value.trim();
    
    if (!requete) {
        afficherErreur('Veuillez saisir une requête de recherche');
        return;
    }
    
    if (searchState.collections.length === 0) {
        afficherErreur('Veuillez sélectionner au moins une collection');
        return;
    }
    
    // Afficher le chargement
    afficherChargement('Recherche en cours...');
    
    try {
        // Options de recherche
        const options = {
            nombreResultats: parseInt(document.getElementById('nb-results')?.value || '10'),
            excludeBruit: document.getElementById('exclude-noise')?.checked !== false,
            filtres: searchState.filtresActifs,
            inclure_chunks: false  // Désactiver l'inclusion automatique des chunks
        };
        
        console.log('=== DÉBUT RECHERCHE MULTI-COLLECTIONS ===');
        console.log('Requête:', requete);
        console.log('Collections:', searchState.collections);
        console.log('Options:', options);
        
        // Rechercher dans toutes les collections sélectionnées
        const promesses = searchState.collections.map(collection => 
            api.rechercher(requete, collection, options)
                .then(data => ({
                    collection,
                    resultats: data.resultats || [],
                    succes: true
                }))
                .catch(error => ({
                    collection,
                    resultats: [],
                    succes: false,
                    erreur: error.message
                }))
        );
        
        const reponses = await Promise.all(promesses);
        
        // Combiner tous les résultats
        let tousResultats = [];
        for (const reponse of reponses) {
            if (reponse.succes) {
                console.log(`✓ Collection ${reponse.collection}: ${reponse.resultats.length} résultats`);
                // Ajouter le nom de la collection à chaque résultat
                const resultatsAvecCollection = reponse.resultats.map(r => ({
                    ...r,
                    collection_source: reponse.collection
                }));
                tousResultats = tousResultats.concat(resultatsAvecCollection);
            } else {
                console.warn(`⚠ Collection ${reponse.collection}: erreur - ${reponse.erreur}`);
            }
        }
        
        // Trier par score décroissant
        tousResultats.sort((a, b) => b.score - a.score);
        
        // Limiter au nombre de résultats demandés
        const resultatsFinaux = tousResultats.slice(0, options.nombreResultats);
        
        console.log(`✓ Total: ${resultatsFinaux.length} résultats combinés (sur ${tousResultats.length})`);
        console.log('================================');
        
        // Masquer le chargement
        masquerChargement();
        
        // Afficher les résultats
        searchState.dernierResultats = resultatsFinaux;
        afficherResultats(resultatsFinaux, requete);
        
        // Sauvegarder l'état pour le retour depuis les conversations
        sauvegarderEtatRecherche();
        
    } catch (error) {
        masquerChargement();
        afficherErreur('Erreur lors de la recherche: ' + error.message);
    }
}

/**
 * Affiche les résultats de recherche
 */
function afficherResultats(resultats, requete) {
    // DEBUG: Logger les paramètres
    console.log('=== AFFICHAGE RÉSULTATS ===');
    console.log('Nombre de résultats:', resultats.length);
    console.log('Requête:', requete);
    console.log('Premier résultat:', resultats[0]);
    console.log('===========================');
    
    const container = document.getElementById('results-container');
    const header = document.getElementById('results-header');
    
    if (!container) {
        console.error('Container results-container non trouvé!');
        return;
    }
    
    // Afficher le header avec le nombre de résultats
    if (header) {
        header.classList.remove('hidden');
        document.getElementById('results-count').textContent = 
            `${resultats.length} résultat(s) pour "${requete}"`;
    }
    
    // Afficher les résultats
    if (resultats.length === 0) {
        console.warn('Aucun résultat à afficher');
        container.innerHTML = `
            <div class="alert alert-info">
                Aucun résultat trouvé pour cette requête. Essayez avec d'autres mots-clés ou ajustez les filtres.
            </div>
        `;
        return;
    }
    
    container.innerHTML = resultats.map((res, index) => creerResultatHTML(res, index)).join('');
    
    // Ajouter les événements de clic
    resultats.forEach((res, index) => {
        const element = document.getElementById(`result-${index}`);
        if (element) {
            element.addEventListener('click', () => afficherContexte(res));
        }
    });
}

/**
 * Crée le HTML pour un résultat
 */
function creerResultatHTML(resultat, index) {
    const meta = resultat.metadata || {};
    const score = (resultat.score * 100).toFixed(1);
    const scoreClass = score >= 80 ? 'badge-success' : score >= 60 ? 'badge-warning' : 'badge-info';
    
    // Vérifier le type de résultat
    const typeResultat = meta.type || 'message';
    
    if (typeResultat === 'image') {
        // Rendu spécial pour les images
        return creerResultatImageHTML(resultat, index, score, scoreClass);
    } else if (typeResultat === 'chunk') {
        // Rendu spécial pour les chunks de contexte
        return creerResultatChunkHTML(resultat, index, score, scoreClass);
    }
    
    // Rendu pour les messages individuels (code existant)
    // Déterminer le contact pour la navigation
    const contact = meta.contact || (meta.direction === 'incoming' ? meta.from : meta.to);
    const collectionSource = resultat.collection_source || 'inconnue';
    
    // Échapper les valeurs pour éviter les injections
    const contactEscaped = (contact || '').replace(/'/g, "\\'");
    const messageIdEscaped = (resultat.id || '').replace(/'/g, "\\'");
    
    return `
        <div class="result-item" id="result-${index}">
            <div class="result-header">
                <div class="result-metadata">
                    <span style="color: var(--accent-primary); font-weight: 600;">💬 Message</span>
                    ${meta.timestamp ? `<span>📅 ${formatTimestamp(meta.timestamp)}</span>` : ''}
                    ${meta.contact_name ? `<span>👤 ${meta.contact_name}</span>` : ''}
                    ${meta.direction ? `<span>${meta.direction === 'incoming' ? '⬅️ Reçu' : '➡️ Envoyé'}</span>` : ''}
                    ${meta.app ? `<span>📱 ${meta.app}</span>` : ''}
                    <span style="color: var(--text-secondary); font-size: 0.85rem;">📁 ${collectionSource}</span>
                </div>
                <div class="badge ${scoreClass}">${score}%</div>
            </div>
            <div class="result-message">${echapperHTML(resultat.document)}</div>
            ${meta.gps_lat && meta.gps_lon ? `
                <div class="text-small text-muted mt-1">
                    📍 GPS: ${meta.gps_lat.toFixed(4)}, ${meta.gps_lon.toFixed(4)}
                </div>
            ` : ''}
            <div class="result-actions">
                <button class="btn-sm btn-secondary" onclick="afficherContexte(searchState.dernierResultats[${index}]); event.stopPropagation();">
                    📱 Voir le contexte
                </button>
                ${contact ? `
                    <button class="btn-sm btn-primary" onclick="naviguerVersConversation('${contactEscaped}', '${messageIdEscaped}'); event.stopPropagation();">
                        💬 Voir dans les conversations
                    </button>
                ` : ''}
            </div>
        </div>
    `;
}

/**
 * Crée le HTML pour un résultat de type chunk (contexte)
 */
function creerResultatChunkHTML(resultat, index, score, scoreClass) {
    const meta = resultat.metadata || {};
    const contact = meta.contact || meta.contact_name || 'Inconnu';
    const collectionSource = resultat.collection_source || 'inconnue';
    const nombreMessages = meta.nombre_messages || 1;
    const premierMessageId = meta.premier_message_id;
    
    // Échapper les valeurs pour éviter les injections
    const contactEscaped = (contact || '').replace(/'/g, "\\'");
    const premierMessageIdEscaped = (premierMessageId || '').replace(/'/g, "\\'");
    
    // Extraire un aperçu du texte (première ligne ou 150 premiers caractères)
    const texteComplet = resultat.document || '';
    const lignes = texteComplet.split('\n');
    const apercu = lignes.length > 0 ? lignes[0] : texteComplet.substring(0, 150);
    
    return `
        <div class="result-item" id="result-${index}" style="border-left: 3px solid var(--accent-secondary);">
            <div class="result-header">
                <div class="result-metadata">
                    <span style="color: var(--accent-secondary); font-weight: 600;">💭 Contexte (${nombreMessages} message${nombreMessages > 1 ? 's' : ''})</span>
                    ${meta.timestamp_debut ? `<span>📅 ${formatTimestamp(meta.timestamp_debut)}</span>` : ''}
                    ${meta.contact_name ? `<span>👤 ${meta.contact_name}</span>` : ''}
                    ${meta.app ? `<span>📱 ${meta.app}</span>` : ''}
                    <span style="color: var(--text-secondary); font-size: 0.85rem;">📁 ${collectionSource}</span>
                </div>
                <div class="badge ${scoreClass}">${score}%</div>
            </div>
            <div class="result-message">
                <div style="font-style: italic; color: var(--text-secondary); margin-bottom: 0.5rem;">
                    Extrait de conversation (${nombreMessages} messages)
                </div>
                <div style="white-space: pre-wrap; font-family: monospace; font-size: 0.9rem; background: var(--bg-darker); padding: 0.75rem; border-radius: var(--border-radius); max-height: 200px; overflow-y: auto;">
${echapperHTML(texteComplet)}
                </div>
            </div>
            ${meta.gps_lat && meta.gps_lon ? `
                <div class="text-small text-muted mt-1">
                    📍 GPS: ${meta.gps_lat.toFixed(4)}, ${meta.gps_lon.toFixed(4)}
                </div>
            ` : ''}
            <div class="result-actions">
                ${contact && premierMessageId ? `
                    <button class="btn-sm btn-primary" onclick="naviguerVersConversation('${contactEscaped}', '${premierMessageIdEscaped}'); event.stopPropagation();">
                        💬 Voir dans les conversations
                    </button>
                ` : ''}
            </div>
        </div>
    `;
}

/**
 * Crée le HTML pour un résultat d'image
 */
function creerResultatImageHTML(resultat, index, score, scoreClass) {
    const meta = resultat.metadata || {};
    const nomImage = meta.nom_image || 'Image';
    const description = resultat.document || '';
    const cheminImage = meta.chemin || meta.nom_image || '';
    const urlImage = `/api/images/servir/${encodeURIComponent(cheminImage)}`;
    const collectionSource = resultat.collection_source || 'inconnue';
    
    // Échapper pour éviter les injections
    const imageIdEscaped = (resultat.id || '').replace(/'/g, "\\'");
    
    return `
        <div class="result-item" id="result-${index}" style="display: flex; gap: var(--spacing-md);">
            <div style="flex-shrink: 0;">
                <img 
                    src="${urlImage}" 
                    alt="${echapperHTML(nomImage)}"
                    style="width: 150px; height: 150px; object-fit: cover; border-radius: var(--border-radius); background: var(--bg-darker);"
                    onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 150 150%22%3E%3Crect fill=%22%23333%22 width=%22150%22 height=%22150%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 fill=%22%23666%22 text-anchor=%22middle%22 dy=%22.3em%22 font-size=%2212%22%3EImage%3C/text%3E%3C/svg%3E'"
                >
            </div>
            <div style="flex: 1; display: flex; flex-direction: column;">
                <div class="result-header">
                    <div class="result-metadata">
                        <span>🖼️ Image</span>
                        ${meta.timestamp ? `<span>📅 ${formatTimestamp(meta.timestamp)}</span>` : ''}
                        ${meta.nom_image ? `<span>📄 ${echapperHTML(nomImage)}</span>` : ''}
                        <span style="color: var(--text-secondary); font-size: 0.85rem;">📁 ${collectionSource}</span>
                    </div>
                    <div class="badge ${scoreClass}">${score}%</div>
                </div>
                <div class="result-message" style="flex: 1;">
                    <strong>Description:</strong> ${echapperHTML(description)}
                </div>
                ${meta.gps_lat && meta.gps_lon ? `
                    <div class="text-small text-muted mt-1">
                        📍 GPS: ${meta.gps_lat.toFixed(4)}, ${meta.gps_lon.toFixed(4)}
                    </div>
                ` : ''}
                <div class="result-actions">
                    <button class="btn-sm btn-primary" onclick="naviguerVersGalerie('${imageIdEscaped}'); event.stopPropagation();">
                        🖼️ Voir dans la galerie
                    </button>
                </div>
            </div>
        </div>
    `;
}

/**
 * Affiche le contexte d'un message
 */
async function afficherContexte(resultat) {
    // Déléguer à context.js
    if (typeof ouvrirContexte === 'function') {
        // Utiliser la collection source du résultat, ou la première collection sélectionnée en fallback
        const collection = resultat.collection_source || (searchState.collections && searchState.collections[0]) || '';
        
        if (!collection) {
            console.error('Aucune collection disponible pour le contexte');
            alert('⚠️ Impossible d\'afficher le contexte: aucune collection sélectionnée');
            return;
        }
        
        await ouvrirContexte(resultat, collection);
    }
}

/**
 * Toggle les filtres
 */
function toggleFiltres() {
    const container = document.getElementById('filters-container');
    container?.classList.toggle('filters-collapsed');
    
    const icon = document.getElementById('filters-toggle-icon');
    if (icon) {
        icon.textContent = container?.classList.contains('filters-collapsed') ? '▼' : '▲';
    }
}

/**
 * Applique les filtres sélectionnés
 */
function appliquerFiltres() {
    const filtres = {};
    
    // Filtre temporel
    const dateDebut = document.getElementById('filter-date-start')?.value;
    const dateFin = document.getElementById('filter-date-end')?.value;
    
    if (dateDebut) {
        filtres.timestamp_debut = dateDebut;
    }
    if (dateFin) {
        filtres.timestamp_fin = dateFin;
    }
    
    // Filtre direction
    const direction = document.getElementById('filter-direction')?.value;
    if (direction && direction !== 'all') {
        filtres.direction = direction;
    }
    
    searchState.filtresActifs = filtres;
    
    // Relancer la recherche si une requête existe
    const requete = document.getElementById('search-input')?.value.trim();
    if (requete) {
        effectuerRecherche();
    }
}

/**
 * Réinitialise les filtres
 */
function reinitialiserFiltres() {
    document.getElementById('filter-date-start').value = '';
    document.getElementById('filter-date-end').value = '';
    document.getElementById('filter-direction').value = 'all';
    
    searchState.filtresActifs = {};
    
    // Relancer la recherche si une requête existe
    const requete = document.getElementById('search-input')?.value.trim();
    if (requete) {
        effectuerRecherche();
    }
}

/**
 * Affiche un message d'erreur
 */
function afficherErreur(message) {
    const container = document.getElementById('results-container');
    if (container) {
        container.innerHTML = `
            <div class="alert alert-danger">
                ⚠️ ${echapperHTML(message)}
            </div>
        `;
    }
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
 * Formate un timestamp
 */
function formatTimestamp(timestamp) {
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
 * Échappe le HTML pour éviter les injections XSS
 */
function echapperHTML(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Sauvegarde l'état actuel de la recherche
 */
function sauvegarderEtatRecherche() {
    const etat = {
        requete: document.getElementById('search-input')?.value || '',
        collections: searchState.collections,  // Tableau au lieu d'une seule
        nombreResultats: parseInt(document.getElementById('nb-results')?.value || '10'),
        excludeBruit: document.getElementById('exclude-noise')?.checked !== false,
        filtres: searchState.filtresActifs,
        resultats: searchState.dernierResultats
    };
    
    sessionStorage.setItem('search_state', JSON.stringify(etat));
    console.log('État de recherche sauvegardé:', etat);
}

/**
 * Restaure l'état de la recherche
 */
function restaurerEtatRecherche() {
    const etatJson = sessionStorage.getItem('search_state');
    if (!etatJson) return;
    
    try {
        const etat = JSON.parse(etatJson);
        console.log('Restauration de l\'état de recherche:', etat);
        
        // Restaurer les champs du formulaire
        const searchInput = document.getElementById('search-input');
        if (searchInput && etat.requete) {
            searchInput.value = etat.requete;
        }
        
        const nbResults = document.getElementById('nb-results');
        if (nbResults) {
            nbResults.value = etat.nombreResultats;
        }
        
        const excludeNoise = document.getElementById('exclude-noise');
        if (excludeNoise) {
            excludeNoise.checked = etat.excludeBruit;
        }
        
        // Restaurer les collections (compatible avec ancien format)
        if (etat.collections && Array.isArray(etat.collections)) {
            searchState.collections = etat.collections;
            // Cocher les bonnes checkboxes
            const checkboxes = document.querySelectorAll('.collection-checkbox');
            checkboxes.forEach(cb => {
                cb.checked = etat.collections.includes(cb.value);
            });
        } else if (etat.collection) {
            // Ancien format avec une seule collection
            searchState.collections = [etat.collection];
        }
        
        // Restaurer les filtres
        searchState.filtresActifs = etat.filtres || {};
        
        // Restaurer les résultats
        if (etat.resultats && etat.resultats.length > 0) {
            searchState.dernierResultats = etat.resultats;
            afficherResultats(etat.resultats, etat.requete);
        }
        
        // Ne pas effacer l'état immédiatement, le garder pour permettre le retour en arrière
        // Il sera effacé lors de la prochaine recherche
        
    } catch (error) {
        console.error('Erreur lors de la restauration de l\'état:', error);
        sessionStorage.removeItem('search_state');
    }
}

/**
 * Navigue vers la page des conversations et ouvre la conversation avec le message mis en surbrillance
 */
function naviguerVersConversation(contact, messageId) {
    // Sauvegarder l'état de la recherche actuelle
    sauvegarderEtatRecherche();
    
    // Trouver la collection du message (depuis le résultat)
    const resultat = searchState.dernierResultats.find(r => r.id === messageId);
    const collection = resultat?.collection_source || (searchState.collections[0] || '');
    
    // Stocker les infos dans sessionStorage pour la navigation
    sessionStorage.setItem('nav_contact', contact);
    sessionStorage.setItem('nav_messageId', messageId);
    sessionStorage.setItem('nav_collection', collection);
    
    // Rediriger vers la page des conversations
    window.location.href = '/conversations';
}

/**
 * Navigue vers la page de la galerie et ouvre l'image en modale
 */
function naviguerVersGalerie(imageId) {
    // Sauvegarder l'état de la recherche actuelle
    sauvegarderEtatRecherche();
    
    // Trouver la collection de l'image (depuis le résultat)
    const resultat = searchState.dernierResultats.find(r => r.id === imageId);
    const collection = resultat?.collection_source || (searchState.collections[0] || '');
    
    // Stocker les infos dans sessionStorage pour la navigation
    sessionStorage.setItem('nav_imageId', imageId);
    sessionStorage.setItem('nav_collection_images', collection);
    
    // Rediriger vers la page de la galerie
    window.location.href = '/galerie';
}

// Initialiser au chargement de la page
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initRecherche);
} else {
    initRecherche();
}

