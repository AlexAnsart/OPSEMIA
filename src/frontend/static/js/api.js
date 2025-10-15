/**
 * Classe API pour communiquer avec le backend OPSEMIA
 */
class OpsemiaAPI {
    constructor(baseURL = 'http://127.0.0.1:5000') {
        this.baseURL = baseURL;
    }

    /**
     * Effectue une requête HTTP
     */
    async _request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        
        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.erreur || `Erreur HTTP ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error(`Erreur API ${endpoint}:`, error);
            throw error;
        }
    }

    /**
     * Recherche sémantique avec filtres
     */
    async rechercher(requete, collection, options = {}) {
        return this._request('/api/search', {
            method: 'POST',
            body: JSON.stringify({
                requete,
                nom_collection: collection,
                nombre_resultats: options.nombreResultats || 10,
                exclure_bruit: options.excludeBruit !== undefined ? options.excludeBruit : true,
                filtres: options.filtres || {}
            })
        });
    }

    /**
     * Obtenir un message spécifique
     */
    async obtenirMessage(messageId, collection) {
        return this._request(`/api/message/${messageId}?collection=${collection}`);
    }

    /**
     * Obtenir le contexte d'un message (messages avant/après)
     */
    async obtenirContexte(messageId, collection, fenetreAvant = 5, fenetreApres = 5) {
        return this._request(
            `/api/context/${messageId}?collection=${collection}&fenetre_avant=${fenetreAvant}&fenetre_apres=${fenetreApres}`
        );
    }

    /**
     * Charger et indexer un fichier CSV
     */
    async chargerCSV(cheminCSV, nomCas = null, reinitialiser = false) {
        return this._request('/api/load', {
            method: 'POST',
            body: JSON.stringify({
                chemin_csv: cheminCSV,
                nom_cas: nomCas,
                reinitialiser: reinitialiser
            })
        });
    }

    /**
     * Charger tous les CSV d'un dossier
     */
    async chargerDossier(cheminDossier, nomCas = null, reinitialiser = false) {
        return this._request('/api/load_dossier', {
            method: 'POST',
            body: JSON.stringify({
                chemin_dossier: cheminDossier,
                nom_cas: nomCas,
                reinitialiser: reinitialiser
            })
        });
    }

    /**
     * Obtenir la configuration actuelle
     */
    async obtenirConfig() {
        return this._request('/api/config');
    }

    /**
     * Modifier la configuration
     */
    async modifierConfig(parametres) {
        return this._request('/api/config', {
            method: 'POST',
            body: JSON.stringify(parametres)
        });
    }

    /**
     * Obtenir les statistiques d'indexation
     */
    async obtenirStats() {
        return this._request('/api/stats');
    }

    /**
     * Lister toutes les collections
     */
    async listerCollections() {
        return this._request('/api/collections');
    }

    /**
     * Vérifier la santé de l'API
     */
    async verifierSante() {
        return this._request('/api/health');
    }

    /**
     * Lister toutes les conversations
     */
    async listerConversations(collection = 'messages_cas1') {
        return this._request(`/api/conversations?collection=${collection}`);
    }

    /**
     * Obtenir tous les messages d'une conversation
     */
    async obtenirConversation(contact, collection = 'messages_cas1') {
        return this._request(`/api/conversation/${encodeURIComponent(contact)}?collection=${collection}`);
    }

    /**
     * Rechercher dans une conversation spécifique
     */
    async rechercherDansConversation(contact, query, collection = 'messages_cas1') {
        return this._request(`/api/conversation/${encodeURIComponent(contact)}/search`, {
            method: 'POST',
            body: JSON.stringify({
                query: query,
                collection: collection
            })
        });
    }
}

// Instance globale de l'API
const api = new OpsemiaAPI();

