/**
 * Module de gestion et configuration OPSEMIA
 */

// État de la configuration
const gestionState = {
    configActuelle: null,
    statsActuelles: null,
    modelesDisponibles: []
};

/**
 * Initialise la page de gestion
 */
function initGestion() {
    // Charger la configuration
    chargerConfiguration();
    
    // Événements
    document.getElementById('load-csv-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        await chargerCSV();
    });
    
    document.getElementById('config-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        await sauvegarderConfiguration();
    });
    
    document.getElementById('refresh-stats')?.addEventListener('click', (e) => {
        e.stopPropagation();
        chargerStatistiques();
    });

    // Événement changement de modèle pour afficher la description
    document.getElementById('config-modele-embedding')?.addEventListener('change', function() {
        afficherDescriptionModele(this.value);
    });
}

/**
 * Charge la configuration actuelle
 */
async function chargerConfiguration() {
    try {
        const data = await api.obtenirConfig();
        
        if (data.succes && data.configuration) {
            gestionState.configActuelle = data.configuration;
            gestionState.modelesDisponibles = data.configuration.encodage.modeles_disponibles || [];
            afficherConfiguration(data.configuration);
        }
    } catch (error) {
        afficherAlerte('Erreur lors du chargement de la configuration: ' + error.message, 'danger');
    }
}

/**
 * Affiche la configuration dans le formulaire
 */
function afficherConfiguration(config) {
    // Encodage - Modèles disponibles
    const selectModele = document.getElementById('config-modele-embedding');
    if (selectModele && gestionState.modelesDisponibles.length > 0) {
        selectModele.innerHTML = '';
        gestionState.modelesDisponibles.forEach(modele => {
            const option = document.createElement('option');
            option.value = modele.id;
            option.textContent = `${modele.nom} - ${modele.description}`;
            if (modele.id === config.encodage.modele) {
                option.selected = true;
            }
            selectModele.appendChild(option);
        });
        afficherDescriptionModele(config.encodage.modele);
    }

    // Périphérique
    const peripheriqueSelect = document.getElementById('config-peripherique');
    if (peripheriqueSelect) {
        peripheriqueSelect.value = config.encodage.peripherique || 'auto';
    }
    
    // Chunking
    const tailleFenetre = document.getElementById('config-taille-fenetre');
    if (tailleFenetre) {
        tailleFenetre.value = config.chunking.taille_fenetre || 1;
    }
    
    const overlap = document.getElementById('config-overlap');
    if (overlap) {
        overlap.value = config.chunking.overlap || 1;
    }
    
    // Recherche
    const methode = document.getElementById('config-methode');
    if (methode) {
        methode.value = config.recherche.methode || 'ANN';
    }
    
    const nbResults = document.getElementById('config-nb-results');
    if (nbResults) {
        nbResults.value = config.recherche.nombre_resultats || 10;
    }
    
    const exclureBruit = document.getElementById('config-exclure-bruit');
    if (exclureBruit) {
        exclureBruit.checked = config.recherche.exclure_bruit_par_defaut !== false;
    }
    
    const seuilDistance = document.getElementById('config-seuil-distance');
    if (seuilDistance && config.recherche.seuil_distance_max !== null && config.recherche.seuil_distance_max !== undefined) {
        seuilDistance.value = config.recherche.seuil_distance_max;
    }
}

/**
 * Affiche la description du modèle sélectionné
 */
function afficherDescriptionModele(modeleId) {
    const modele = gestionState.modelesDisponibles.find(m => m.id === modeleId);
    const descElement = document.getElementById('modele-description');
    
    if (descElement && modele) {
        descElement.innerHTML = `
            <strong>${modele.nom}</strong>: ${modele.description}<br>
            Dimensions: ${modele.dimensions}
        `;
    }
}

/**
 * Charge les statistiques d'indexation
 */
async function chargerStatistiques() {
    const statsContainer = document.getElementById('stats-container');
    if (!statsContainer) return;
    
    try {
        statsContainer.innerHTML = '<div class="flex-center" style="padding: 2rem;"><div class="spinner"></div></div>';
        
        const data = await api.obtenirStats();
        
        if (data.succes && data.statistiques) {
            gestionState.statsActuelles = data.statistiques;
            afficherStatistiques(data.statistiques);
        }
    } catch (error) {
        statsContainer.innerHTML = `
            <div class="alert alert-danger">
                Erreur lors du chargement des statistiques: ${error.message}
            </div>
        `;
    }
}

/**
 * Affiche les statistiques
 */
function afficherStatistiques(stats) {
    const statsContainer = document.getElementById('stats-container');
    if (!statsContainer) return;
    
    let html = `
        <div style="margin-bottom: var(--spacing-lg);">
            <h4 style="color: var(--text-white); margin-bottom: var(--spacing-md);">Vue d'ensemble</h4>
            <table class="table">
                <tbody>
                    <tr>
                        <td><strong>Collections indexées</strong></td>
                        <td>${stats.nombre_collections || 0}</td>
                    </tr>
                    <tr>
                        <td><strong>Total de documents</strong></td>
                        <td>${stats.total_documents || 0}</td>
                    </tr>
                    <tr>
                        <td><strong>Modèle d'embedding</strong></td>
                        <td><code>${stats.modele_embedding || 'N/A'}</code></td>
                    </tr>
                    <tr>
                        <td><strong>Méthode de recherche</strong></td>
                        <td><span class="badge badge-info">${stats.methode_recherche || 'N/A'}</span></td>
                    </tr>
                </tbody>
            </table>
        </div>
    `;
    
    // Collections
    if (stats.collections && stats.collections.length > 0) {
        html += `
            <div>
                <h4 style="color: var(--text-white); margin-bottom: var(--spacing-md);">Détails des collections</h4>
                <table class="table">
                    <thead>
                        <tr>
                            <th>Nom de la collection</th>
                            <th>Documents</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${stats.collections.map(col => `
                            <tr>
                                <td><code>${col.nom}</code></td>
                                <td><span class="badge badge-success">${col.nombre_documents}</span></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
    } else {
        html += `
            <div class="alert alert-info">
                Aucune collection indexée. Chargez des données pour commencer.
            </div>
        `;
    }
    
    statsContainer.innerHTML = html;
}

/**
 * Charge et indexe un fichier CSV
 */
async function chargerCSV() {
    const cheminCSV = document.getElementById('csv-path')?.value.trim();
    const reinitialiser = document.getElementById('csv-reset')?.checked;
    
    if (!cheminCSV) {
        afficherAlerte('Veuillez saisir le chemin du fichier CSV', 'warning');
        return;
    }
    
    afficherAlerte('Indexation en cours... Veuillez patienter.', 'info');
    
    // Désactiver le bouton pendant le traitement
    const submitBtn = document.querySelector('#load-csv-form button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Indexation en cours...';
    }
    
    try {
        const data = await api.chargerCSV(cheminCSV, null, reinitialiser);
        
        if (data.succes) {
            let message = data.message || 'Indexation terminée avec succès!';
            
            // Afficher les statistiques si disponibles
            if (data.statistiques) {
                message += `<br><br>Détails:<br>
                    ${data.statistiques.messages_indexe || 0} messages indexés<br>
                    ${data.statistiques.chunks_indexes || 0} chunks créés<br>
                    Durée: ${data.statistiques.duree_totale_sec?.toFixed(2) || 0}s`;
            }
            
            afficherAlerte(message, 'success');
            
            // Recharger les statistiques
            setTimeout(() => {
                const collapsible = document.getElementById('stats-collapsible');
                if (collapsible && collapsible.classList.contains('collapsed')) {
                    collapsible.classList.remove('collapsed');
                }
                chargerStatistiques();
            }, 1000);
            
            // Réinitialiser le formulaire
            document.getElementById('csv-path').value = '';
            document.getElementById('csv-reset').checked = false;
        }
    } catch (error) {
        afficherAlerte('Erreur lors de l\'indexation: ' + error.message, 'danger');
    } finally {
        // Réactiver le bouton
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = '📤 Charger et indexer';
        }
    }
}

/**
 * Sauvegarde la configuration modifiée
 */
async function sauvegarderConfiguration() {
    const seuilDistanceInput = document.getElementById('config-seuil-distance')?.value.trim();
    const seuilDistance = seuilDistanceInput ? parseFloat(seuilDistanceInput) : null;
    
    const parametres = {
        // Encodage
        id_modele_embedding: document.getElementById('config-modele-embedding')?.value,
        peripherique_embedding: document.getElementById('config-peripherique')?.value,
        
        // Chunking
        taille_fenetre_chunk: parseInt(document.getElementById('config-taille-fenetre')?.value || '1'),
        overlap_fenetre_chunk: parseInt(document.getElementById('config-overlap')?.value || '1'),
        
        // Recherche
        methode_recherche: document.getElementById('config-methode')?.value,
        nombre_resultats_recherche: parseInt(document.getElementById('config-nb-results')?.value || gestionState.configActuelle?.recherche?.nombre_resultats || '10'),
        exclure_bruit_par_defaut: document.getElementById('config-exclure-bruit')?.checked,
        seuil_distance_max: seuilDistance
    };
    
    try {
        const data = await api.modifierConfig(parametres);
        
        if (data.succes) {
            afficherAlerte('Configuration sauvegardée avec succès!', 'success');
            
            if (data.avertissement) {
                afficherAlerte(data.avertissement, 'warning');
            }
            
            // Recharger la configuration
            setTimeout(chargerConfiguration, 500);
        }
    } catch (error) {
        afficherAlerte('Erreur lors de la sauvegarde de la configuration: ' + error.message, 'danger');
    }
}

/**
 * Affiche un message d'alerte
 */
function afficherAlerte(message, type = 'info') {
    const container = document.getElementById('alerts-container');
    if (!container) return;
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.innerHTML = `
        <div style="flex: 1;">${message}</div>
        <button onclick="this.parentElement.remove()" 
                style="background: none; border: none; cursor: pointer; font-size: 1.5rem; color: inherit; padding: 0; margin-left: var(--spacing-md);">
            &times;
        </button>
    `;
    alertDiv.style.display = 'flex';
    alertDiv.style.alignItems = 'flex-start';
    alertDiv.style.justifyContent = 'space-between';
    
    container.appendChild(alertDiv);
    
    // Scroll vers l'alerte
    alertDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    
    // Auto-remove après 10 secondes pour les succès et infos
    if (type === 'success' || type === 'info') {
        setTimeout(() => {
            alertDiv.style.opacity = '0';
            alertDiv.style.transform = 'translateX(-20px)';
            setTimeout(() => alertDiv.remove(), 300);
        }, 10000);
    }
}

// Initialiser au chargement de la page
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initGestion);
} else {
    initGestion();
}
