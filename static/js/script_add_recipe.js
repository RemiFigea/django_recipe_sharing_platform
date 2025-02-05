async function checkTitle() {
    const titleInputField = document.getElementById("id_title");
    const title = titleInputField?.value;
    const parentContainer = titleInputField?.parentElement;

    if (!titleInputField) {
        console.error("Éléments #id_title manquants.");
        return;
    };

    try {
        const data = await fetchData(`/api/check-title?title=${encodeURIComponent(title)}`);

        if (!data) return;

        const existingErrorList = parentContainer.previousElementSibling;

        if (existingErrorList && existingErrorList.classList.contains("errorlist")) {
            existingErrorList.remove();
        };
        if (data.error_list && data.error_list.length > 0) {
            const errorListHtml = document.createElement("ul");
            errorListHtml.classList.add("errorlist");
            data.error_list.forEach((error) => {
                const errorItem = document.createElement("li");
                errorItem.textContent = error;
                errorListHtml.appendChild(errorItem);
            });
            parentContainer.insertAdjacentElement("beforebegin", errorListHtml);
        };
    } catch (error) {
        console.error("Erreur lors de l'insertion des messages d'erreur:", error);
    };
};

function hideLabelsExceptFirst() {
    const ingredientForms = document.querySelectorAll(".form-ingredient");

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

async function addIngredientForm() {
    try {
        const data = await fetchData(`/api/add-ingredient-form`);
        if (!data || !data.form_html) return;

        const sectionIngredient = document.getElementById("section-ingredient");
        if (!sectionIngredient) {
            console.error("L'élément #section-ingredient est introuvable dans le DOM.");
            return;
        }

        const template = document.createElement("template");
        template.innerHTML = data.form_html.trim();
        const newForm = template.content.firstChild;

        sectionIngredient.appendChild(newForm);

        hideLabelsExceptFirst();
    } catch (error) {
        console.error("Erreur lors de l'ajout d'un formulaire d'ingrédient :", error);
    };
};

function removeIngredientForm(event) {
    if (event.target.classList.contains("btn-secondary")) {
        const ingredientForm = event.target.closest(".form-ingredient");
        if (ingredientForm) {
            ingredientForm.remove();
            hideLabelsExceptFirst();
        }
    }
}

document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("id_title")?.addEventListener("focusout", checkTitle);
    document.getElementById("add-ingredient-btn")?.addEventListener("click", addIngredientForm);
    document.getElementById("section-ingredient")?.addEventListener("click", removeIngredientForm);
    hideLabelsExceptFirst();
});