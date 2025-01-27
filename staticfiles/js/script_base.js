function showPopup(message) {
    const popup = document.getElementById("custom-popup");
    const popupMessage = document.getElementById("popup-message");

    popupMessage.textContent = message;
    popup.classList.remove("hidden");
};

function closePopup() {
    const popup = document.getElementById("custom-popup");
    popup.classList.add("hidden");
};


function hideLoadingImageError() {
    const recipeImg = document.querySelectorAll(".recipe-img");

    recipeImg.forEach(img => {
        setTimeout(() => {
            if (!img.complete || img.naturalWidth === 0) {
                img.style.display = "none";
                const placeholder = img.parentElement;
                const errorText = document.createElement("p");
                errorText.textContent = "Photo non disponible";
                errorText.classList.add("error-text");
                placeholder.appendChild(errorText);
            }
        }, 500);
    });
}

document.addEventListener("DOMContentLoaded", () => {
    const message = "Cette fonctionnalité n'a pas encore été implémentée."
    document.querySelectorAll(".not-implemented").forEach((link) => {
        link.addEventListener("click", () => showPopup(message));
    });
    document.getElementById("popup-close")?.addEventListener("click", closePopup);
    hideLoadingImageError();
 });

