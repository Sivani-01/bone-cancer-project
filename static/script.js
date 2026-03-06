// script.js - Final version for Bone Cancer Project

document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('form');
    const fileInput = document.querySelector('input[type="file"]');
    const submitBtn = document.querySelector('button[type="submit"]');

    if (form) {
        form.addEventListener('submit', (e) => {
            // 1. Validation: Ensure a file is selected
            if (!fileInput || fileInput.files.length === 0) {
                alert("Please select a bone scan image or X-ray first.");
                e.preventDefault(); // Stop the upload
                return;
            }

            // 2. Visual Feedback: Disable button to prevent double-submissions
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = "<span>⌛</span> Analyzing Scan... Please wait.";
                submitBtn.style.backgroundColor = "#6c757d"; // Change to a "loading" grey
                submitBtn.style.cursor = "not-allowed";
            }

            console.log("Analysis started... Model is processing the bone scan.");
        });
    }

    // 3. Optional: Log file selection to console for debugging
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const fileName = this.files[0].name;
                console.log("File ready for analysis: " + fileName);
                
                // If you have a filename display element, you can update it here
                const nameDisplay = document.querySelector('#file-name-display');
                if (nameDisplay) {
                    nameDisplay.textContent = fileName;
                }
            }
        });
    }
});