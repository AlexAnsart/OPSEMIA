/**
 * Module de recherche sémantique OPSEMIA
 */

// État de la recherche
const searchState = {
    collection: 'messages_cas1',
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
 * Charge la liste des collections disponibles
 */
async function chargerCollections() {
    try {
        const data = await api.listerCollections();
        const select = document.getElementById('collection-select');
        
        if (select && data.collections) {
            // Filtrer et trier les collections : prioriser "messages" sur "chunks"
            const collections = data.collections
                .filter(col => !col.nom.includes('chunk'))  // Exclure les chunks
                .sort((a, b) => {
                    // Trier alphabétiquement
                    return a.nom.localeCompare(b.nom);
                });
            
            if (collections.length === 0) {
                select.innerHTML = '<option value="">Aucune collection disponible</option>';
                console.warn('Aucune collection de messages trouvée');
                return;
            }
            
            select.innerHTML = collections.map(col => 
                `<option value="${col.nom}">${col.nom} (${col.nombre_documents} docs)</option>`
            ).join('');
            
            // Sélectionner la première collection
            searchState.collection = collections[0].nom;
            
            console.log('Collections chargées:', collections.map(c => c.nom));
            console.log('Collection sélectionnée:', searchState.collection);
            
            // Écouter les changements de sélection
            select.addEventListener('change', (e) => {
                searchState.collection = e.target.value;
                console.log('Collection changée vers:', searchState.collection);
            });
        }
    } catch (error) {
        afficherErreur('Erreur lors du chargement des collections: ' + error.message);
    }
}

/**
 * Effectue une recherche sémantique
 */
async function effectuerRecherche() {
    const requete = document.getElementById('search-input')?.value.trim();
    
    if (!requete) {
        afficherErreur('Veuillez saisir une requête de recherche');
        return;
    }
    
    // Afficher le chargement
    afficherChargement('Recherche en cours...');
    
    try {
        // Options de recherche
        const options = {
            nombreResultats: parseInt(document.getElementById('nb-results')?.value || '10'),
            excludeBruit: document.getElementById('exclude-noise')?.checked !== false,
            filtres: searchState.filtresActifs
        };
        
        // Effectuer la recherche
        const data = await api.rechercher(
            requete, 
            searchState.collection,
            options
        );
        
        // DEBUG: Logger la réponse complète
        console.log('=== RÉPONSE API RECHERCHE ===');
        console.log('Requête:', requete);
        console.log('Collection:', searchState.collection);
        console.log('Options:', options);
        console.log('Réponse complète:', data);
        console.log('Nombre de résultats:', data.nombre_resultats);
        console.log('Résultats (array):', data.resultats);
        console.log('Type resultats:', typeof data.resultats, Array.isArray(data.resultats));
        console.log('================================');
        
        // Masquer le chargement
        masquerChargement();
        
        // Afficher les résultats
        searchState.dernierResultats = data.resultats || [];
        afficherResultats(data.resultats || [], requete);
        
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
    
    // Déterminer le contact pour la navigation
    const contact = meta.direction === 'incoming' ? meta.from : meta.to;
    
    return `
        <div class="result-item" id="result-${index}">
            <div class="result-header">
                <div class="result-metadata">
                    ${meta.timestamp ? `<span>📅 ${formatTimestamp(meta.timestamp)}</span>` : ''}
                    ${meta.contact_name ? `<span>👤 ${meta.contact_name}</span>` : ''}
                    ${meta.direction ? `<span>${meta.direction === 'incoming' ? '⬅️ Reçu' : '➡️ Envoyé'}</span>` : ''}
                    ${meta.app ? `<span>📱 ${meta.app}</span>` : ''}
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
                    <button class="btn-sm btn-primary" onclick="naviguerVersConversation('${contact}', '${resultat.id}'); event.stopPropagation();">
                        💬 Voir dans les conversations
                    </button>
                ` : ''}
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
        await ouvrirContexte(resultat, searchState.collection);
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
        collection: searchState.collection,
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
        
        // Restaurer la collection
        searchState.collection = etat.collection;
        const collectionSelect = document.getElementById('collection-select');
        if (collectionSelect) {
            collectionSelect.value = etat.collection;
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
    
    // Stocker les infos dans sessionStorage pour la navigation
    sessionStorage.setItem('nav_contact', contact);
    sessionStorage.setItem('nav_messageId', messageId);
    sessionStorage.setItem('nav_collection', searchState.collection);
    
    // Rediriger vers la page des conversations
    window.location.href = '/conversations';
}

// Initialiser au chargement de la page
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initRecherche);
} else {
    initRecherche();
}

