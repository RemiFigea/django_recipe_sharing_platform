async function updateCollectionButton(dropdown, recipeId) {
    const collectionName = dropdown.getAttribute("collection-name")
    const collectionButton = dropdown.querySelector(".collection-button");
    const addToCollection = dropdown.querySelector(".add-to-collection");
    const removeFromCollection = dropdown.querySelector(".remove-from-collection");

    if (!collectionName || !collectionButton || !addToCollection || !removeFromCollection) {
        console.error("Éléments manquants dans le dropdown.");
        return;
    }
    
    const requestData = {
        recipe_id: recipeId,
        collection_name: collectionName
    };
    

    try {
        const data = await fetchData("api/check-collection-status", "POST", requestData);
        
        if (!data) return;

        if (data.is_in_collection) {
            collectionButton.style.opacity = "1";
            removeFromCollection.classList.remove("hidden");

            if (collectionName !== "history") {
                addToCollection.classList.add("hidden");
            }
        } else {
            collectionButton.style.opacity = "0.2";
            addToCollection.classList.remove("hidden");
            removeFromCollection.classList.add("hidden");
        }
    } catch (error) {
        console.error("Erreur lors de la mise à jour du bouton :", error);
    }

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

async function handleCollectionUpdate(event, url) {
    const buttonContainer = document.getElementById("collection-buttons");
    const recipeId = buttonContainer?.getAttribute("current-recipe-id");
    const dropdown = event.target.closest(".dropdown");
    
    if (!buttonContainer || !recipeId || !dropdown) {
        console.error("Données manquantes pour la mise à jour.");
        return;
    }
    
    const collectionName = dropdown.getAttribute("collection-name");

    if (collectionName === "trials" || collectionName === "album") {
        const requestData = {
            recipe_id: recipeId,
            collection_name: collectionName
        };

        try {
            const data = await fetchData(url, "POST", requestData);

            if (!data) return;

            if (data.message) {
                showMessage(data.message);
                updateAllCollectionButton();
            }
        } catch (error) {
            console.error("Erreur lors de la mise à jour du bouton :", error);
        }
    };
};

function resetMessages(modal) {
    modal.querySelector(".error-message").textContent = "";
    modal.querySelectorAll(".success-message, .error-message").forEach(msg => msg.classList.add("hidden"));
};


function handleResponse(data, modal) {
    const succesMsg = modal.querySelector(".success-message");
    const errorMsg = modal.querySelector(".error-message");

    if (modal.id === "modal-remove-recipe-history") {
        insertRemoveRecipeHistoryForm(data, modal);
    };

    if (data.success) {
        succesMsg.classList.remove("hidden");
        errorMsg.classList.add("hidden");
    } else if (errorMsg) {
            errorMsg.innerHTML = Object.values(data.errors).map(e => `<p>${e}</p>`).join("");
            succesMsg.classList.add("hidden");
            errorMsg.classList.remove("hidden");
        }
    };

function insertRemoveRecipeHistoryForm(data, modal) {
    const formContainer = modal.querySelector("#select-date-to-remove");

    if (data.form_html && formContainer) {
        formContainer.innerHTML = "";
        formContainer.innerHTML = data.form_html;
    };
};

function setupCalendar() {
    const calendarInput = document.getElementById("date-picker");
    if (calendarInput) {
        return flatpickr(calendarInput, {
            dateFormat: "Y-m-d",
            defaultDate: "today",
        });
    }
    return null;
};

function setupModal(modalId, openBtnId, formId, apiUrl, calendar) {
    const modal = document.getElementById(modalId);
    const openBtn = document.getElementById(openBtnId);
    const closeButton = modal.querySelector(".btn-close")
    const form = document.getElementById(formId);

    openBtn.onclick = function() {
        modal.classList.add("show");
        resetMessages(modal);
        if (modalId === "modal-remove-recipe-history") {


            const formContainer = modal.querySelector("#select-date-to-remove");
            formContainer.querySelectorAll("input, select, textarea").forEach(input => {
                input.value = "";
            });
            
            const form = document.getElementById(formId);

            let submitEvent = new Event("submit", { bubbles: true, cancelable: true });
            form.dispatchEvent(submitEvent);
        };
    };


    closeButton.onclick = function() {
        modal.classList.remove("show");
        if (calendar) calendar.close();
    };

    window.onclick = function(event) {
        if (event.target === modal ) {
            modal.classList.remove("show");
            if (calendar) calendar.close();
        }
    };

    form.addEventListener("submit", async function(event) {
        event.preventDefault();

        let formData = new FormData(form);

        try {
            const data = await fetchData(apiUrl, "POST", formData)

            if (data) {
                handleResponse(data, modal);
                updateAllCollectionButton();
            }
        } catch (error) {
            console.error("Erreur lors de la soumission du formulaire :", error);
        }
    });  

};

function setupModals(calendar) {
    setupModal("modal-add-recipe-history", "add-to-history", "add-recipe-history-form", "api/add-recipe-history", calendar);
    setupModal("modal-remove-recipe-history", "remove-from-history", "remove-recipe-history-form", "api/remove-recipe-history", calendar);
};

function checkLoggedUser(){
    const headerList = document.getElementById("header-link-list");
    const loggedUser = headerList.getAttribute("logged-user-id");
    return !!loggedUser;
};

function showLoginMessageInCollectionButtonDropdown() {
    const buttonContainer = document.getElementById("collection-buttons");
    
    if (!buttonContainer) {
        console.error("Boutons manquants.");
        return;
    }

    buttonContainer.querySelectorAll(".dropdown").forEach((dropdown) => {
        const addToCollection = dropdown.querySelector(".add-to-collection");
        const removeFromCollection = dropdown.querySelector(".remove-from-collection");
        const loginRequiredMsg = dropdown.querySelector(".login-required-msg");

        if (!addToCollection || !removeFromCollection || !loginRequiredMsg) {
            console.error("Éléments manquants dans le dropdown.");
            return;
        };

        addToCollection.classList.add("hidden");
        removeFromCollection.classList.add("hidden");
        loginRequiredMsg.classList.remove("hidden");
    });
};

document.addEventListener("DOMContentLoaded", () => {
    if (checkLoggedUser()) {
        updateAllCollectionButton();
        document.getElementById("collection-buttons")?.addEventListener("click", (event) => {
            if (event.target.classList.contains("add-to-collection")) {
                handleCollectionUpdate(event, "/api/add-to-collection");
            } else if (event.target.classList.contains("remove-from-collection")) {
                handleCollectionUpdate(event, "/api/remove-from-collection");
            }
        });
        const calendar = setupCalendar();
        setupModals(calendar);
    } else {
        showLoginMessageInCollectionButtonDropdown();
    };
});