// steamroomandselfcare/static/steamroomandselfcare/js/breathing.js

document.addEventListener("DOMContentLoaded", function () {
    const timerDiv = document.getElementById("breathing-timer");
    if (!timerDiv) return;

    const breathDuration = 4; // Duration in seconds for each phase
    let timer = breathDuration;
    let phase = "Inhale"; // Alternates between "Inhale" and "Exhale"

    // Initialize display
    timerDiv.innerHTML = `${phase}... (${timer})`;

    setInterval(() => {
        timer--;
        if (timer <= 0) {
            // Reset timer and toggle phase
            timer = breathDuration;
            phase = phase === "Inhale" ? "Exhale" : "Inhale";
        }
        timerDiv.innerHTML = `${phase}... (${timer})`;
    }, 1000);
});

