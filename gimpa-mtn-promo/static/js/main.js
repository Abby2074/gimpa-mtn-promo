/**
 * GIMPA × MTN Promo — Landing Page Scripts
 * =========================================
 * 1. Fake countdown timer that resets every 3 hours.
 * 2. "Bundles remaining" counter that slowly decreases.
 *
 * These urgency elements are classic social-engineering tactics
 * used to pressure users into acting without thinking.
 */

// --- Countdown timer --------------------------------------------------------
// Starts at a random time under 3 hours and counts down.
// When it hits zero, it resets — so the "offer" never actually expires.

(function () {
    const timerEl = document.getElementById("countdown");
    if (!timerEl) return;  // only run on the landing page

    // Start with a random time between 1h and 3h so each visitor sees
    // a different "time remaining" — making it feel more real.
    let totalSeconds = Math.floor(Math.random() * 7200) + 3600; // 1h – 3h

    function pad(n) {
        return n.toString().padStart(2, "0");
    }

    function updateTimer() {
        const h = Math.floor(totalSeconds / 3600);
        const m = Math.floor((totalSeconds % 3600) / 60);
        const s = totalSeconds % 60;
        timerEl.textContent = pad(h) + ":" + pad(m) + ":" + pad(s);

        if (totalSeconds <= 0) {
            // Reset so it never truly runs out
            totalSeconds = 10800; // 3 hours
        } else {
            totalSeconds--;
        }
    }

    updateTimer();              // show immediately (no 1-second blank)
    setInterval(updateTimer, 1000);
})();


// --- "Bundles remaining" counter --------------------------------------------
// Randomly decreases by 1 every 20–60 seconds, but never goes below 3,
// because showing "0 remaining" would defeat the purpose.

(function () {
    const bundlesEl = document.getElementById("bundles-remaining");
    if (!bundlesEl) return;

    let remaining = parseInt(bundlesEl.textContent, 10) || 12;

    function decreaseBundles() {
        if (remaining > 3) {
            remaining--;
            bundlesEl.textContent = remaining;

            // Brief animation to draw attention
            bundlesEl.style.transform = "scale(1.3)";
            setTimeout(() => { bundlesEl.style.transform = "scale(1)"; }, 300);
        }

        // Schedule the next decrease at a random interval (20–60 s)
        const nextDelay = (Math.random() * 40 + 20) * 1000;
        setTimeout(decreaseBundles, nextDelay);
    }

    // First decrease after 15–45 seconds
    const firstDelay = (Math.random() * 30 + 15) * 1000;
    setTimeout(decreaseBundles, firstDelay);
})();
