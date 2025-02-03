function checkTitle() {
    const titleInputField = document.getElementById("id_title");
    const title = titleInputField?.value;
    const parentContainer = titleInputField?.parentElement;

    if (!titleInputField) {
        console.error("Éléments #id_title manquants.");
        return;
    }

    fetch(`/api/check-title?title=${encodeURIComponent(title)}`)
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
        const existingErrorList = parentContainer.previousElementSibling;
            if (existingErrorList && existingErrorList.classList.contains("errorlist")) {
                existingErrorList.remove();
            }
        if (data.error_list && data.error_list.length > 0) {
            const errorListHtml = document.createElement("ul");
            errorListHtml.classList.add("errorlist");
            data.error_list.forEach((error) => {
                const errorItem = document.createElement("li");
                errorItem.textContent = error;
                errorListHtml.appendChild(errorItem);
            });
            parentContainer.insertAdjacentElement("beforebegin", errorListHtml);
        }
    })
    .catch((error) => console.error("Erreur lors de l'insertion des messages d'erreur:", error));
}

function hideLabelsExceptFirst() {
    const ingredientForms = document.querySelectorAll(".ingredient-form");

    ingredientForms.forEach((form, index) => {
        const labels = form.querySelectorAll("label");

        if (index === 0) {
            labels.forEach(label => {
                label.style.display = "block";
            });
        } else {
            labels.forEach(label => {
                label.style.display = "none";
            });
        }
    });

    return ingredientForms.length;
}

function addIngredientForm() {
    fetch(`/api/add-ingredient-form`)
    .then((response) => {
        if (!response.ok) {
            return response.text().then((errorData) => {
                console.error("Erreur du serveur :", errorData || "Erreur inconnue.");
                throw new Error(errorData || "Erreur inconnue.");
            });
        }
        return response.text();
    })
    .then((html) => {
        const sectionIngredient = document.getElementById("section-ingredient");
        if (!sectionIngredient) {
            console.error("L'élément #section-ingredient est introuvable dans le DOM.");
            return;
        }

        const template = document.createElement("template");
        template.innerHTML = html.trim();

        const newForm = template.content.firstChild;

        sectionIngredient.appendChild(newForm);

        hideLabelsExceptFirst();
    })
    .catch((error) => {
        console.error("Erreur lors de l'ajout d'un formulaire d'ingrédient :", error);
    });
}

function removeIngredientForm(event) {
    if (event.target.classList.contains("btn-secondary")) {
        const ingredientForm = event.target.closest(".ingredient-form");
        if (ingredientForm) {
            ingredientForm.remove();
        }
    }
}

document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("id_title")?.addEventListener("focusout", checkTitle);
    document.getElementById("add-ingredient-btn")?.addEventListener("click", addIngredientForm);
    document.getElementById("section-ingredient")?.addEventListener("click", removeIngredientForm);
    hideLabelsExceptFirst();
});