function showMessage(message) {
    const messageBox = document.getElementById("modal-notification");
    const messageContent = document.getElementById("notification-message");

    messageContent.textContent = message;
    messageBox.classList.add("show");
};

function closeMessage() {
    const messageBox = document.getElementById("modal-notification");
    messageBox.classList.remove("show");
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
        link.addEventListener("click", () => showMessage(message));
    });
    const messageBox = document.getElementById("modal-notification");
    const closeButton = messageBox?.querySelector(".btn-close")
    closeButton?.addEventListener("click", closeMessage);
    hideLoadingImageError();
 });

