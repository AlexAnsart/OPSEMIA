/**
 * Module de vue contextuelle pour afficher les conversations
 */

/**
 * Ouvre la vue contextuelle pour un message
 */
async function ouvrirContexte(resultat, collection) {
    const contextView = document.getElementById('context-view');
    if (!contextView) {
        console.error('context-view element not found');
        return;
    }
    
    const contextContent = document.getElementById('context-content');
    if (!contextContent) {
        console.error('context-content element not found');
        return;
    }
    
    // Afficher le chargement
    contextContent.innerHTML = `
        <div class="flex-center" style="padding: 2rem;">
            <div class="spinner"></div>
            <p style="margin-top: 1rem; color: var(--text-secondary);">Chargement du contexte...</p>
        </div>
    `;
    
    // Ouvrir le panneau
    contextView.classList.add('open');
    
    console.log('Chargement contexte pour message:', resultat.id, 'collection:', collection);
    
    try {
        // Récupérer le contexte du message avec timeout
        const messageId = resultat.id;
        
        // Créer une promesse avec timeout de 10 secondes
        const timeoutPromise = new Promise((_, reject) => 
            setTimeout(() => reject(new Error('Timeout: La requête a pris trop de temps')), 10000)
        );
        
        const dataPromise = api.obtenirContexte(messageId, collection, 10, 10);
        
        // Race entre la requête et le timeout
        const data = await Promise.race([dataPromise, timeoutPromise]);
        
        console.log('Contexte reçu:', data);
        
        if (data.succes && data.contexte) {
            afficherConversation(data.contexte);
        } else {
            console.error('Erreur dans la réponse:', data);
            afficherErreurContexte(data.erreur || 'Impossible de charger le contexte du message');
        }
    } catch (error) {
        console.error('Erreur lors du chargement du contexte:', error);
        afficherErreurContexte('Erreur lors du chargement du contexte: ' + error.message);
    }
}

/**
 * Ferme la vue contextuelle
 */
function fermerContexte() {
    const contextView = document.getElementById('context-view');
    if (contextView) {
        contextView.classList.remove('open');
    }
}

/**
 * Affiche la conversation complète
 */
function afficherConversation(contexte) {
    const contextContent = document.getElementById('context-content');
    if (!contextContent) return;
    
    const messagesAvant = contexte.messages_avant || [];
    const messageCentral = contexte.message_central;
    const messagesApres = contexte.messages_apres || [];
    
    // Construire le HTML de la conversation
    let html = '';
    
    // Messages avant (contexte précédent)
    if (messagesAvant.length > 0) {
        html += '<div class="context-section">';
        html += '<div class="text-small text-muted mb-2">Messages précédents</div>';
        messagesAvant.forEach(msg => {
            html += creerMessageBubble(msg, false);
        });
        html += '</div>';
    }
    
    // Message central (celui cliqué)
    if (messageCentral) {
        html += '<div class="context-section">';
        html += '<div class="text-small text-muted mb-2">✨ Message recherché</div>';
        html += creerMessageBubble(messageCentral, true);
        html += '</div>';
    }
    
    // Messages après (contexte suivant)
    if (messagesApres.length > 0) {
        html += '<div class="context-section">';
        html += '<div class="text-small text-muted mb-2">Messages suivants</div>';
        messagesApres.forEach(msg => {
            html += creerMessageBubble(msg, false);
        });
        html += '</div>';
    }
    
    contextContent.innerHTML = html;
    
    // Scroll vers le message cible
    setTimeout(() => {
        const targetMessage = contextContent.querySelector('.message-bubble.target');
        if (targetMessage) {
            targetMessage.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }, 100);
}

/**
 * Crée une bulle de message
 */
function creerMessageBubble(message, estCible = false) {
    const meta = message.metadata || {};
    const direction = meta.direction || 'incoming';
    const targetClass = estCible || message.est_cible ? 'target' : '';
    
    return `
        <div class="message-bubble ${direction} ${targetClass}">
            <div class="message-meta">
                <strong>${meta.contact_name || meta.from || 'Inconnu'}</strong>
                ${meta.timestamp ? ` · ${formatTimestamp(meta.timestamp)}` : ''}
                ${meta.direction ? ` · ${direction === 'incoming' ? '⬅️ Reçu' : '➡️ Envoyé'}` : ''}
            </div>
            <div class="message-text">
                ${echapperHTML(message.document || message.message || '')}
            </div>
            ${meta.app ? `<div class="text-small text-muted mt-1">via ${meta.app}</div>` : ''}
            ${meta.gps_lat && meta.gps_lon ? `
                <div class="text-small text-muted">
                    📍 ${meta.gps_lat.toFixed(4)}, ${meta.gps_lon.toFixed(4)}
                </div>
            ` : ''}
        </div>
    `;
}

/**
 * Affiche une erreur dans la vue contextuelle
 */
function afficherErreurContexte(message) {
    const contextContent = document.getElementById('context-content');
    if (contextContent) {
        contextContent.innerHTML = `
            <div class="alert alert-danger">
                ⚠️ ${echapperHTML(message)}
            </div>
        `;
    }
}

/**
 * Formate un timestamp (copie de search.js pour éviter la dépendance)
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
 * Échappe le HTML (copie de search.js)
 */
function echapperHTML(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialiser l'événement de fermeture
document.addEventListener('DOMContentLoaded', () => {
    const closeBtn = document.getElementById('context-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', fermerContexte);
    }
    
    // Fermer avec la touche Échap
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            fermerContexte();
        }
    });
});

