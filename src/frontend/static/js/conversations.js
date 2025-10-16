/**
 * Module de gestion des conversations SMS
 */

// État global
let conversationsData = [];
let conversationActive = null;
let collectionActive = 'messages_cas1';

// État de la recherche intra-conversation
let searchState = {
    terme: '',
    occurrences: [],
    indexActuel: -1
};

/**
 * Initialisation au chargement de la page
 */
document.addEventListener('DOMContentLoaded', async () => {
    // Vérifier s'il y a une navigation depuis la recherche AVANT de charger les collections
    const navContact = sessionStorage.getItem('nav_contact');
    const navMessageId = sessionStorage.getItem('nav_messageId');
    const navCollection = sessionStorage.getItem('nav_collection');
    
    // Définir la collection active avant de charger le dropdown
    if (navCollection) {
        collectionActive = navCollection;
        console.log('Collection définie depuis navigation:', navCollection);
    }
    
    // Charger les collections disponibles (le dropdown se remplira avec la bonne collection active)
    await chargerCollections();
    
    // Charger la liste des conversations
    await chargerConversations();
    
    // Si navigation depuis recherche, ouvrir la conversation
    if (navContact && navMessageId) {
        sessionStorage.removeItem('nav_contact');
        sessionStorage.removeItem('nav_messageId');
        sessionStorage.removeItem('nav_collection');
        
        await naviguerVersMessage(navContact, navMessageId);
    }
    
    // Gestionnaires d'événements
    document.getElementById('search-conversations')?.addEventListener('input', filtrerConversations);
    document.getElementById('collection-select')?.addEventListener('change', changerCollection);
    document.getElementById('close-conversation')?.addEventListener('click', fermerConversation);
    
    // Recherche intra-conversation
    const searchInput = document.getElementById('search-messages');
    if (searchInput) {
        searchInput.addEventListener('input', demarrerRechercheMessages);
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                if (e.shiftKey) {
                    allerOccurrencePrecedente();
                } else {
                    allerOccurrenceSuivante();
                }
            } else if (e.key === 'Escape') {
                effacerRecherche();
            }
        });
    }
    document.getElementById('search-next')?.addEventListener('click', allerOccurrenceSuivante);
    document.getElementById('search-prev')?.addEventListener('click', allerOccurrencePrecedente);
    document.getElementById('search-clear')?.addEventListener('click', effacerRecherche);
    
    // Fermer avec Échap
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            fermerConversation();
        }
    });
});

/**
 * Charge les collections disponibles
 */
async function chargerCollections() {
    try {
        const data = await api.listerCollections();
        
        if (data.succes && data.collections) {
            const select = document.getElementById('collection-select');
            if (!select) return;
            
            // Filtrer pour ne garder que les collections de messages (pas les chunks ni les images)
            const collectionsMessages = data.collections.filter(c => 
                !c.nom.includes('chunk') && !c.nom.includes('image')
            );
            
            console.log('Collections messages:', collectionsMessages);
            
            select.innerHTML = collectionsMessages.map(c => 
                `<option value="${c.nom}" ${c.nom === collectionActive ? 'selected' : ''}>${c.nom} (${c.nombre_documents} docs)</option>`
            ).join('');
            
            // Si la collection active n'existe plus, prendre la première
            if (collectionsMessages.length > 0 && !collectionsMessages.find(c => c.nom === collectionActive)) {
                collectionActive = collectionsMessages[0].nom;
                select.value = collectionActive;
            }
        }
    } catch (error) {
        console.error('Erreur chargement collections:', error);
    }
}

/**
 * Change la collection active
 */
async function changerCollection(e) {
    collectionActive = e.target.value;
    await chargerConversations();
    fermerConversation();
}

/**
 * Charge la liste des conversations
 */
async function chargerConversations() {
    try {
        afficherChargement('Chargement des conversations...');
        
        const data = await api.listerConversations(collectionActive);
        
        if (data.succes) {
            conversationsData = data.conversations || [];
            afficherListeConversations(conversationsData);
            
            // Mettre à jour les statistiques
            document.getElementById('total-conversations').textContent = conversationsData.length;
            
            cacherChargement();
        } else {
            afficherErreur('Erreur lors du chargement des conversations');
        }
    } catch (error) {
        console.error('Erreur:', error);
        afficherErreur('Impossible de charger les conversations');
    }
}

/**
 * Affiche la liste des conversations dans le panneau de gauche
 */
function afficherListeConversations(conversations) {
    const container = document.getElementById('conversations-list');
    if (!container) return;
    
    if (conversations.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p>Aucune conversation trouvée</p>
                <p class="text-small text-muted">Indexez des messages pour voir les conversations</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = conversations.map(conv => `
        <div class="conversation-item" data-contact="${conv.contact}">
            <div class="conversation-info">
                <div class="conversation-header">
                    <strong class="conversation-name">${echapperHTML(conv.contact_name)}</strong>
                    <span class="conversation-count">${conv.nombre_messages}</span>
                </div>
                <div class="conversation-preview">${echapperHTML(conv.dernier_message || '')}</div>
                <div class="conversation-date">${formatTimestamp(conv.dernier_timestamp)}</div>
            </div>
        </div>
    `).join('');
    
    // Ajouter les gestionnaires de clic
    container.querySelectorAll('.conversation-item').forEach(item => {
        item.addEventListener('click', () => {
            const contact = item.dataset.contact;
            ouvrirConversation(contact);
        });
    });
}

/**
 * Filtre les conversations par recherche
 */
function filtrerConversations(e) {
    const terme = e.target.value.toLowerCase();
    
    if (!terme) {
        afficherListeConversations(conversationsData);
        return;
    }
    
    const conversationsFiltrees = conversationsData.filter(conv => 
        conv.contact_name.toLowerCase().includes(terme) ||
        conv.contact.toLowerCase().includes(terme) ||
        (conv.dernier_message && conv.dernier_message.toLowerCase().includes(terme))
    );
    
    afficherListeConversations(conversationsFiltrees);
}

/**
 * Ouvre une conversation et charge tous ses messages
 */
async function ouvrirConversation(contact) {
    try {
        afficherChargement('Chargement de la conversation...');
        
        const data = await api.obtenirConversation(contact, collectionActive);
        
        if (data.succes) {
            conversationActive = {
                contact: contact,
                info: data.conversation,
                messages: data.messages
            };
            
            afficherConversation(conversationActive);
            
            // Marquer la conversation comme active dans la liste
            document.querySelectorAll('.conversation-item').forEach(item => {
                item.classList.toggle('active', item.dataset.contact === contact);
            });
            
            cacherChargement();
        } else {
            afficherErreur('Impossible de charger la conversation');
        }
    } catch (error) {
        console.error('Erreur:', error);
        afficherErreur('Erreur lors du chargement de la conversation');
    }
}

/**
 * Affiche une conversation complète
 */
function afficherConversation(conversation) {
    const panel = document.getElementById('conversation-panel');
    const header = document.getElementById('conversation-header-info');
    const messagesContainer = document.getElementById('messages-container');
    
    if (!panel || !header || !messagesContainer) return;
    
    // Afficher le panneau
    panel.classList.add('open');
    
    // Mettre à jour l'en-tête
    header.innerHTML = `
        <div>
            <h3 class="conversation-title">${echapperHTML(conversation.info.contact_name)}</h3>
            <p class="text-small text-muted">${echapperHTML(conversation.info.contact)}</p>
        </div>
        <div class="text-small text-muted">
            ${conversation.messages.length} message(s)
        </div>
    `;
    
    // Afficher les messages
    messagesContainer.innerHTML = conversation.messages.map(msg => 
        creerBulleMessage(msg)
    ).join('');
    
    // Scroll vers le bas (dernier message)
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

/**
 * Crée une bulle de message type conversation
 */
function creerBulleMessage(message) {
    const meta = message.metadata || {};
    const direction = meta.direction || 'incoming';
    const isOutgoing = direction === 'outgoing';
    
    return `
        <div class="message-bubble ${direction}" id="msg-${message.id}" data-msg-id="${message.id}">
            <div class="message-header">
                <span class="message-sender">
                    ${isOutgoing ? '➡️ Vous' : '⬅️ ' + echapperHTML(meta.contact_name || meta.from || 'Inconnu')}
                </span>
                <span class="message-time">${formatTimestampCourt(meta.timestamp)}</span>
            </div>
            <div class="message-content">
                ${echapperHTML(message.document || '')}
            </div>
            ${creerMetadatasBadge(meta)}
        </div>
    `;
}

/**
 * Crée un badge de métadonnées (discret, cliquable pour plus d'infos)
 */
function creerMetadatasBadge(metadata) {
    const badges = [];
    
    if (metadata.app && metadata.app !== 'sms') {
        badges.push(`<span class="badge">📱 ${metadata.app}</span>`);
    }
    
    if (metadata.gps_lat && metadata.gps_lon && metadata.gps_lat !== 0 && metadata.gps_lon !== 0) {
        badges.push(`<span class="badge" title="GPS: ${metadata.gps_lat}, ${metadata.gps_lon}">📍</span>`);
    }
    
    if (metadata.is_noise) {
        badges.push(`<span class="badge badge-warning">🚫 Spam</span>`);
    }
    
    return badges.length > 0 ? `<div class="message-badges">${badges.join('')}</div>` : '';
}

/**
 * Démarre la recherche dans la conversation (style CTRL+F)
 */
function demarrerRechercheMessages(e) {
    const terme = e.target.value.trim();
    
    if (!conversationActive) return;
    
    if (!terme) {
        effacerRecherche();
        return;
    }
    
    searchState.terme = terme.toLowerCase();
    
    // Réafficher la conversation avec highlights
    afficherConversationAvecHighlights();
    
    // Trouver toutes les occurrences
    trouverOccurrences();
    
    // Afficher les contrôles de navigation
    const controls = document.getElementById('search-controls');
    if (controls) {
        controls.style.display = 'flex';
    }
    
    // Aller à la première occurrence
    if (searchState.occurrences.length > 0) {
        searchState.indexActuel = 0;
        allerAOccurrence(0);
    }
}

/**
 * Affiche la conversation avec les termes de recherche highlightés
 */
function afficherConversationAvecHighlights() {
    if (!conversationActive) return;
    
    const messagesContainer = document.getElementById('messages-container');
    if (!messagesContainer) return;
    
    // Afficher tous les messages avec highlights
    messagesContainer.innerHTML = conversationActive.messages.map(msg => 
        creerBulleMessageAvecHighlight(msg)
    ).join('');
}

/**
 * Crée une bulle de message avec highlight des termes recherchés
 */
function creerBulleMessageAvecHighlight(message) {
    const meta = message.metadata || {};
    const direction = meta.direction || 'incoming';
    const isOutgoing = direction === 'outgoing';
    
    // Highlighter le texte
    let contenu = echapperHTML(message.document || '');
    if (searchState.terme) {
        const regex = new RegExp(`(${escapeRegex(searchState.terme)})`, 'gi');
        contenu = contenu.replace(regex, '<span class="search-highlight">$1</span>');
    }
    
    return `
        <div class="message-bubble ${direction}" id="msg-${message.id}" data-msg-id="${message.id}">
            <div class="message-header">
                <span class="message-sender">
                    ${isOutgoing ? '➡️ Vous' : '⬅️ ' + echapperHTML(meta.contact_name || meta.from || 'Inconnu')}
                </span>
                <span class="message-time">${formatTimestampCourt(meta.timestamp)}</span>
            </div>
            <div class="message-content">
                ${contenu}
            </div>
            ${creerMetadatasBadge(meta)}
        </div>
    `;
}

/**
 * Trouve toutes les occurrences du terme de recherche
 */
function trouverOccurrences() {
    searchState.occurrences = [];
    
    if (!conversationActive || !searchState.terme) return;
    
    conversationActive.messages.forEach((msg, index) => {
        const contenu = msg.document.toLowerCase();
        if (contenu.includes(searchState.terme)) {
            searchState.occurrences.push({
                messageIndex: index,
                messageId: msg.id
            });
        }
    });
    
    // Mettre à jour le compteur
    mettreAJourCompteur();
}

/**
 * Met à jour l'affichage du compteur d'occurrences
 */
function mettreAJourCompteur() {
    const counter = document.getElementById('search-counter');
    if (!counter) return;
    
    if (searchState.occurrences.length === 0) {
        counter.textContent = '0/0';
    } else {
        counter.textContent = `${searchState.indexActuel + 1}/${searchState.occurrences.length}`;
    }
    
    // Activer/désactiver les boutons
    const prevBtn = document.getElementById('search-prev');
    const nextBtn = document.getElementById('search-next');
    
    if (prevBtn) {
        prevBtn.disabled = searchState.indexActuel <= 0;
    }
    if (nextBtn) {
        nextBtn.disabled = searchState.indexActuel >= searchState.occurrences.length - 1;
    }
}

/**
 * Va à l'occurrence suivante
 */
function allerOccurrenceSuivante() {
    if (searchState.indexActuel < searchState.occurrences.length - 1) {
        searchState.indexActuel++;
        allerAOccurrence(searchState.indexActuel);
    }
}

/**
 * Va à l'occurrence précédente
 */
function allerOccurrencePrecedente() {
    if (searchState.indexActuel > 0) {
        searchState.indexActuel--;
        allerAOccurrence(searchState.indexActuel);
    }
}

/**
 * Va à une occurrence spécifique
 */
function allerAOccurrence(index) {
    const occurrence = searchState.occurrences[index];
    if (!occurrence) return;
    
    // Enlever la classe active de l'occurrence précédente
    document.querySelectorAll('.search-highlight.active').forEach(el => {
        el.classList.remove('active');
    });
    
    // Trouver le message
    const messageElement = document.getElementById(`msg-${occurrence.messageId}`);
    if (!messageElement) return;
    
    // Scroller vers le message
    messageElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
    
    // Activer le premier highlight dans ce message
    const highlight = messageElement.querySelector('.search-highlight');
    if (highlight) {
        highlight.classList.add('active');
    }
    
    // Mettre à jour le compteur
    mettreAJourCompteur();
}

/**
 * Efface la recherche et restaure l'affichage normal
 */
function effacerRecherche() {
    // Réinitialiser l'état
    searchState.terme = '';
    searchState.occurrences = [];
    searchState.indexActuel = -1;
    
    // Effacer le champ de recherche
    const searchInput = document.getElementById('search-messages');
    if (searchInput) {
        searchInput.value = '';
    }
    
    // Cacher les contrôles
    const controls = document.getElementById('search-controls');
    if (controls) {
        controls.style.display = 'none';
    }
    
    // Réafficher la conversation normale
    if (conversationActive) {
        afficherConversation(conversationActive);
    }
}

/**
 * Échappe les caractères spéciaux pour regex
 */
function escapeRegex(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Ferme le panneau de conversation
 */
function fermerConversation() {
    const panel = document.getElementById('conversation-panel');
    if (panel) {
        panel.classList.remove('open');
    }
    
    // Désélectionner la conversation active
    document.querySelectorAll('.conversation-item').forEach(item => {
        item.classList.remove('active');
    });
    
    conversationActive = null;
    
    // Réinitialiser complètement la recherche
    effacerRecherche();
}

/**
 * Navigation vers un message spécifique (depuis la recherche sémantique)
 */
function naviguerVersMessage(contact, messageId) {
    ouvrirConversation(contact).then(() => {
        // Attendre que la conversation soit chargée
        setTimeout(() => {
            const messageElement = document.getElementById(`msg-${messageId}`);
            if (messageElement) {
                messageElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                messageElement.classList.add('highlight');
                
                // Retirer le highlight après 3s
                setTimeout(() => {
                    messageElement.classList.remove('highlight');
                }, 3000);
            }
        }, 300);
    });
}

/**
 * Affiche le chargement
 */
function afficherChargement(message = 'Chargement...') {
    const overlay = document.getElementById('loading-overlay');
    const messageElement = document.getElementById('loading-message');
    
    if (overlay) {
        overlay.classList.remove('hidden');
        if (messageElement) {
            messageElement.textContent = message;
        }
    }
}

/**
 * Cache le chargement
 */
function cacherChargement() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.classList.add('hidden');
    }
}

/**
 * Affiche une erreur
 */
function afficherErreur(message) {
    cacherChargement();
    
    const container = document.getElementById('conversations-list');
    if (container) {
        container.innerHTML = `
            <div class="alert alert-danger">
                ⚠️ ${echapperHTML(message)}
            </div>
        `;
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
 * Formate un timestamp court (pour les bulles)
 */
function formatTimestampCourt(timestamp) {
    if (!timestamp) return '';
    
    const date = new Date(timestamp);
    const maintenant = new Date();
    
    // Si aujourd'hui, afficher juste l'heure
    if (date.toDateString() === maintenant.toDateString()) {
        return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
    }
    
    // Sinon afficher la date courte
    return date.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
}

/**
 * Échappe le HTML pour éviter les injections
 */
function echapperHTML(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Exposer les fonctions pour navigation externe
window.conversationsModule = {
    naviguerVersMessage
};

