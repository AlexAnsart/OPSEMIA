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
    
    document.getElementById('load-images-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        await chargerImages();
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

    // Images
    const imgMinLength = document.getElementById('config-img-min-length');
    if (imgMinLength && config.images) {
        imgMinLength.value = config.images.longueur_min_description || 30;
    }

    const imgMaxLength = document.getElementById('config-img-max-length');
    if (imgMaxLength && config.images) {
        imgMaxLength.value = config.images.longueur_max_description || 150;
    }

    const imgNumBeams = document.getElementById('config-img-num-beams');
    if (imgNumBeams && config.images) {
        imgNumBeams.value = config.images.num_beams || 15;
    }

    const imgTemperature = document.getElementById('config-img-temperature');
    if (imgTemperature && config.images) {
        imgTemperature.value = config.images.temperature || 0.3;
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
    
    // Collections avec bouton de suppression
    if (stats.collections && stats.collections.length > 0) {
        // Filtrer les collections "undefined" ou vides
        const collectionsValides = stats.collections.filter(col => col.nom && col.nom !== 'undefined' && col.nom.trim() !== '');
        
        html += `
            <div>
                <h4 style="color: var(--text-white); margin-bottom: var(--spacing-md);">Détails des collections</h4>
                <table class="table">
                    <thead>
                        <tr>
                            <th>Nom de la collection</th>
                            <th>Documents</th>
                            <th style="width: 100px;">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${collectionsValides.map(col => `
                            <tr>
                                <td><code>${col.nom}</code></td>
                                <td><span class="badge badge-success">${col.nombre_documents}</span></td>
                                <td>
                                    <button 
                                        onclick="supprimerCollectionConfirm('${col.nom.replace(/'/g, "\\'")}')"
                                        class="btn btn-sm btn-danger"
                                        title="Supprimer cette collection"
                                    >
                                        🗑️
                                    </button>
                                </td>
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
 * Confirmation avant suppression d'une collection
 */
async function supprimerCollectionConfirm(nomCollection) {
    const confirmation = confirm(`⚠️ Êtes-vous sûr de vouloir supprimer la collection "${nomCollection}" ?\n\nCette action est irréversible et supprimera tous les documents de cette collection.`);
    
    if (!confirmation) return;
    
    try {
        const response = await api.supprimerCollection(nomCollection);
        
        if (response.succes) {
            afficherAlerte(`✅ Collection "${nomCollection}" supprimée avec succès`, 'success');
            chargerStatistiques();  // Recharger les stats
        } else {
            throw new Error(response.erreur || 'Erreur inconnue');
        }
    } catch (error) {
        console.error('Erreur suppression collection:', error);
        afficherAlerte(`❌ Erreur lors de la suppression: ${error.message}`, 'danger');
    }
}

/**
 * Charge et indexe un fichier CSV avec suivi de progression SSE
 */
async function chargerCSV() {
    const cheminCSV = document.getElementById('csv-path')?.value.trim();
    const nomCas = null; // Nom du cas toujours null (non configurable)
    const reinitialiser = document.getElementById('csv-reset')?.checked;
    
    if (!cheminCSV) {
        afficherAlerte('Veuillez saisir le chemin du fichier CSV', 'warning');
        return;
    }
    
    // Désactiver le bouton pendant le traitement
    const submitBtn = document.querySelector('#load-csv-form button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = '⏳ Chargement du modèle...';
    }
    
    try {
        // Afficher un message de chargement du modèle
        afficherAlerte('⏳ Chargement du modèle d\'embedding en mémoire... Cela peut prendre 15-30 secondes pour les gros modèles comme Qwen3 (8GB). Veuillez patienter.', 'info');
        
        // 1. Démarrer l'indexation (peut prendre du temps si le modèle n'est pas encore chargé)
        const response = await api.chargerCSV(cheminCSV, nomCas, reinitialiser);
        
        if (!response.succes || !response.task_id) {
            throw new Error(response.erreur || 'Impossible de démarrer l\'indexation');
        }
        
        const taskId = response.task_id;
        console.log(`📡 Tâche d'indexation démarrée: ${taskId}`);
        
        // Mettre à jour le bouton
        if (submitBtn) {
            submitBtn.textContent = '📊 Indexation en cours...';
        }
        
        // 2. Afficher la barre de progression
        afficherBarreProgression();
        
        // 3. Se connecter au stream SSE pour suivre la progression
        await suivreProgressionSSE(taskId);
        
    } catch (error) {
        console.error('Erreur lors de l\'indexation:', error);
        masquerBarreProgression();
        afficherAlerte('Erreur lors de l\'indexation: ' + error.message, 'danger');
    } finally {
        // Réactiver le bouton
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = '📤 Charger et indexer les messages';
        }
    }
}

/**
 * Charge et indexe un fichier CSV d'images avec suivi de progression SSE
 */
async function chargerImages() {
    const cheminCSV = document.getElementById('images-csv-path')?.value.trim();
    const nomCas = null; // Nom du cas toujours null (non configurable)
    const reinitialiser = document.getElementById('images-reset')?.checked;
    
    if (!cheminCSV) {
        afficherAlerte('Veuillez saisir le chemin du fichier CSV d\'images', 'warning');
        return;
    }
    
    // Désactiver le bouton pendant le traitement
    const submitBtn = document.querySelector('#load-images-form button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Indexation d\'images en cours...';
    }
    
    try {
        // 1. Démarrer l'indexation (retourne immédiatement avec task_id)
        const response = await api.chargerImages(cheminCSV, nomCas, reinitialiser);
        
        if (!response.succes || !response.task_id) {
            throw new Error(response.erreur || 'Impossible de démarrer l\'indexation d\'images');
        }
        
        const taskId = response.task_id;
        console.log(`📡 Tâche d'indexation d'images démarrée: ${taskId}`);
        
        // 2. Afficher la barre de progression
        afficherBarreProgression();
        
        // 3. Se connecter au stream SSE pour suivre la progression
        await suivreProgressionImagesSSE(taskId);
        
    } catch (error) {
        console.error('Erreur lors de l\'indexation d\'images:', error);
        masquerBarreProgression();
        afficherAlerte('Erreur lors de l\'indexation d\'images: ' + error.message, 'danger');
    } finally {
        // Réactiver le bouton
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = '📤 Charger et indexer les images';
        }
    }
}

/**
 * Affiche la barre de progression
 */
function afficherBarreProgression() {
    const existingBar = document.getElementById('progress-bar-container');
    if (existingBar) existingBar.remove();
    
    const alertsContainer = document.getElementById('alerts-container');
    if (!alertsContainer) return;
    
    const progressHTML = `
        <div id="progress-bar-container" class="card" style="margin-bottom: var(--spacing-lg);">
            <div style="padding: var(--spacing-lg);">
                <h4 style="color: var(--text-white); margin-bottom: var(--spacing-md);">
                    📊 Progression de l'indexation
                </h4>
                <div style="margin-bottom: var(--spacing-sm);">
                    <div style="display: flex; justify-content: space-between; margin-bottom: var(--spacing-xs);">
                        <span id="progress-etape" style="color: var(--text-secondary);">Initialisation...</span>
                        <span id="progress-pct" style="color: var(--accent-color); font-weight: 600;">0%</span>
                    </div>
                    <div style="background: var(--bg-darker); border-radius: var(--border-radius); height: 24px; overflow: hidden; position: relative;">
                        <div id="progress-bar" style="background: linear-gradient(90deg, var(--accent-color), var(--accent-hover)); height: 100%; width: 0%; transition: width 0.3s ease; display: flex; align-items: center; justify-content: center;">
                            <span id="progress-bar-text" style="color: white; font-size: 0.75rem; font-weight: 600; position: absolute;"></span>
                        </div>
                    </div>
                </div>
                <p id="progress-message" style="color: var(--text-secondary); font-size: 0.875rem; margin: 0;"></p>
            </div>
        </div>
    `;
    
    alertsContainer.insertAdjacentHTML('afterbegin', progressHTML);
}

/**
 * Masque la barre de progression
 */
function masquerBarreProgression() {
    const container = document.getElementById('progress-bar-container');
    if (container) {
        setTimeout(() => container.remove(), 2000);
    }
}

/**
 * Met à jour la barre de progression
 */
function mettreAJourProgression(progression, etape, message) {
    const progressBar = document.getElementById('progress-bar');
    const progressPct = document.getElementById('progress-pct');
    const progressEtape = document.getElementById('progress-etape');
    const progressMessage = document.getElementById('progress-message');
    const progressBarText = document.getElementById('progress-bar-text');
    
    if (progressBar) {
        progressBar.style.width = `${progression}%`;
    }
    if (progressPct) {
        progressPct.textContent = `${Math.round(progression)}%`;
    }
    if (progressBarText) {
        progressBarText.textContent = `${Math.round(progression)}%`;
    }
    if (progressEtape) {
        progressEtape.textContent = etape || 'En cours...';
    }
    if (progressMessage) {
        progressMessage.textContent = message || '';
    }
}

/**
 * Suit la progression via Server-Sent Events (SSE)
 */
function suivreProgressionSSE(taskId) {
    return new Promise((resolve, reject) => {
        const sseURL = `${api.baseURL}/api/load/progress/${taskId}`;
        console.log(`📡 Tentative connexion SSE: ${sseURL}`);
        
        const eventSource = new EventSource(sseURL);
        
        console.log(`📡 Connexion SSE établie pour task ${taskId}`);
        
        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('📊 Progression:', data);
                
                mettreAJourProgression(
                    data.progression || 0,
                    data.etape || 'En cours',
                    data.message || ''
                );
                
            } catch (error) {
                console.error('Erreur parsing SSE:', error);
            }
        };
        
        eventSource.addEventListener('complete', (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('✅ Indexation terminée:', data);
                
                eventSource.close();
                mettreAJourProgression(100, 'Terminé', 'Indexation terminée avec succès!');
                
                // Afficher le résumé
                if (data.statistiques) {
                    const message = `Indexation terminée avec succès!<br><br>Détails:<br>
                        ${data.statistiques.messages_indexe || 0} messages indexés<br>
                        ${data.statistiques.chunks_indexes || 0} chunks créés<br>
                        Durée: ${data.statistiques.duree_totale_sec?.toFixed(2) || 0}s`;
                    afficherAlerte(message, 'success');
                }
                
                // Masquer la barre et recharger les stats
                masquerBarreProgression();
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
                
                resolve(data);
            } catch (error) {
                console.error('Erreur traitement complete:', error);
                eventSource.close();
                reject(error);
            }
        });
        
        eventSource.addEventListener('error', (event) => {
            console.error('❌ Erreur SSE:', event);
            eventSource.close();
            
            try {
                const data = event.data ? JSON.parse(event.data) : {};
                const erreur = data.erreur || 'Erreur de connexion au serveur';
                masquerBarreProgression();
                afficherAlerte('Erreur: ' + erreur, 'danger');
                reject(new Error(erreur));
            } catch (e) {
                masquerBarreProgression();
                afficherAlerte('Erreur de connexion au serveur. Le modèle est peut-être trop lourd pour votre système.', 'danger');
                reject(new Error('Erreur de connexion SSE'));
            }
        });
        
        eventSource.onerror = (error) => {
            console.error('❌ Erreur connexion SSE:', error);
            eventSource.close();
            masquerBarreProgression();
            afficherAlerte('Erreur de connexion au serveur. Si vous utilisez un gros modèle (Qwen3), il peut avoir épuisé la RAM disponible.', 'danger');
            reject(new Error('Erreur de connexion SSE - Ressources insuffisantes'));
        };
    });
}

/**
 * Suit la progression d'indexation d'images via Server-Sent Events (SSE)
 */
function suivreProgressionImagesSSE(taskId) {
    return new Promise((resolve, reject) => {
        const sseURL = `${api.baseURL}/api/load_images/progress/${taskId}`;
        console.log(`📡 Tentative connexion SSE images: ${sseURL}`);
        
        const eventSource = new EventSource(sseURL);
        
        console.log(`📡 Connexion SSE images établie pour task ${taskId}`);
        
        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('📊 Progression images:', data);
                
                mettreAJourProgression(
                    data.progression || 0,
                    data.etape || 'En cours',
                    data.message || ''
                );
                
            } catch (error) {
                console.error('Erreur parsing SSE images:', error);
            }
        };
        
        eventSource.addEventListener('complete', (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('✅ Indexation d\'images terminée:', data);
                
                eventSource.close();
                mettreAJourProgression(100, 'Terminé', 'Indexation d\'images terminée avec succès!');
                
                // Afficher le résumé
                if (data.statistiques) {
                    const message = `Indexation d'images terminée avec succès!<br><br>Détails:<br>
                        ${data.statistiques.images_indexees || 0} images indexées<br>
                        ${data.statistiques.images_manquantes || 0} images manquantes<br>
                        Durée: ${data.statistiques.duree_totale_sec?.toFixed(2) || 0}s`;
                    afficherAlerte(message, 'success');
                }
                
                // Masquer la barre et recharger les stats
                masquerBarreProgression();
                setTimeout(() => {
                    const collapsible = document.getElementById('stats-collapsible');
                    if (collapsible && collapsible.classList.contains('collapsed')) {
                        collapsible.classList.remove('collapsed');
                    }
                    chargerStatistiques();
                }, 1000);
                
                // Réinitialiser le formulaire
                document.getElementById('images-csv-path').value = '';
                document.getElementById('images-reset').checked = false;
                
                resolve(data);
            } catch (error) {
                console.error('Erreur traitement complete images:', error);
                eventSource.close();
                reject(error);
            }
        });
        
        eventSource.addEventListener('error', (event) => {
            console.error('❌ Erreur SSE images:', event);
            eventSource.close();
            
            try {
                const data = event.data ? JSON.parse(event.data) : {};
                const erreur = data.erreur || 'Erreur de connexion SSE images';
                masquerBarreProgression();
                afficherAlerte('Erreur: ' + erreur, 'danger');
                reject(new Error(erreur));
            } catch (e) {
                masquerBarreProgression();
                afficherAlerte('Erreur de connexion au serveur', 'danger');
                reject(new Error('Erreur de connexion SSE images'));
            }
        });
        
        eventSource.onerror = (error) => {
            console.error('❌ Erreur connexion SSE images:', error);
            eventSource.close();
            masquerBarreProgression();
            afficherAlerte('Erreur de connexion au serveur', 'danger');
            reject(new Error('Erreur de connexion SSE images'));
        };
    });
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
        seuil_distance_max: seuilDistance,
        
        // Images
        longueur_min_description_image: parseInt(document.getElementById('config-img-min-length')?.value || '30'),
        longueur_max_description_image: parseInt(document.getElementById('config-img-max-length')?.value || '150'),
        num_beams_description_image: parseInt(document.getElementById('config-img-num-beams')?.value || '15'),
        temperature_description_image: parseFloat(document.getElementById('config-img-temperature')?.value || '0.3')
    };
    
    try {
        const data = await api.modifierConfig(parametres);
        
        if (data.succes) {
            afficherAlerte('Configuration sauvegardée avec succès!', 'success');
            
            // Afficher le message d'info (rechargement automatique du modèle)
            if (data.info) {
                afficherAlerte(data.info, 'info');
            }
            
            // Afficher l'avertissement (redémarrage requis pour chunking)
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
