function updateCollectionButton(dropdown, recipeId) {
    const modelName = dropdown.getAttribute("model-name")
    const collectionButton = dropdown.querySelector(".collection-button");
    const addToCollection = dropdown.querySelector(".add-to-collection");
    const removeFromCollection = dropdown.querySelector(".remove-from-collection");

    if (!modelName || !collectionButton || !addToCollection || !removeFromCollection) {
        console.error("Éléments manquants dans le dropdown.");
        return;
    }

    fetch(`/api/check-collection-status?recipe_id=${encodeURIComponent(recipeId)}&model_name=${encodeURIComponent(modelName)}`)
            .then((response) => {
                if (!response.ok) {
                    return response.json().then((errorData) => {
                        console.error("Erreur du serveur :", errorData.message || "Erreur inconnue.");
                        throw new Error(errorData.message || "Erreur inconnue.");
                    });
                }
                return response.json();
            })
            .then((data) => {
                if (data.is_in_album) {
                    collectionButton.style.opacity = "1";
                    addToCollection.style.display = "none";
                    removeFromCollection.style.display = "block";
                } else {
                    collectionButton.style.opacity = "0.2";
                    addToCollection.style.display = "block";
                    removeFromCollection.style.display = "none";
                }
            })
            .catch((error) => console.error("Erreur lors de la vérification :", error));
};

function updateAllCollectionButton() {
    const buttonContainer = document.getElementById("collection-buttons");
    const recipeId = buttonContainer?.getAttribute("current-recipe-id");

    if (!buttonContainer || !recipeId) {
        console.error("Boutons ou ID de recette manquants.");
        return;
    }

    buttonContainer.querySelectorAll(".dropdown").forEach((dropdown) => {
        updateCollectionButton(dropdown, recipeId);
    });
};


function handleCollectionUpdate(event, url) {
    const buttonContainer = document.getElementById("collection-buttons");
    const recipeId = buttonContainer?.getAttribute("current-recipe-id");
    const dropdown = event.target.closest(".dropdown");
    
    if (!buttonContainer || !recipeId || !dropdown) {
        console.error("Données manquantes pour la mise à jour.");
        return;
    }
    
    const modelName = dropdown.getAttribute("model-name");
    fetch(`${url}?recipe_id=${encodeURIComponent(recipeId)}&model_name=${encodeURIComponent(modelName)}`)
            .then((response) => {
                if (!response.ok) {
                    return response.json().then((errorData) => {
                        console.error("Erreur du serveur :", errorData.message || "Erreur inconnue.");
                        throw new Error(errorData.message || "Erreur inconnue.");
                    });
                }
                return response.json();
            })
            .then((data) => {
                if (data.message) {
                    showPopup(data.message);
                    updateAllCollectionButton();
                }
            })
            .catch((error) => console.error("Erreur lors de la mise à jour :", error));
};

document.addEventListener("DOMContentLoaded", () => {
    updateAllCollectionButton();
    document.getElementById("collection-buttons")?.addEventListener("click", (event) => {
        if (event.target.classList.contains("add-to-collection")) {
            handleCollectionUpdate(event, "/api/add-to-collection");
        } else if (event.target.classList.contains("remove-from-collection")) {
            handleCollectionUpdate(event, "/api/remove-from-collection");
        }
    });
});