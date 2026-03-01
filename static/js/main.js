// Countdown timer
(function () {
    var timerEl = document.getElementById('countdown');
    if (!timerEl) return;

    var totalSeconds = 2 * 3600 + 59 * 60 + 59; // 02:59:59

    function pad(n) {
        return n < 10 ? '0' + n : String(n);
    }

    function updateTimer() {
        if (totalSeconds <= 0) {
            timerEl.textContent = '00:00:00';
            return;
        }
        totalSeconds--;
        var h = Math.floor(totalSeconds / 3600);
        var m = Math.floor((totalSeconds % 3600) / 60);
        var s = totalSeconds % 60;
        timerEl.textContent = pad(h) + ':' + pad(m) + ':' + pad(s);
    }

    setInterval(updateTimer, 1000);
})();

// Bundles remaining (fake decrement)
(function () {
    var bundlesEl = document.getElementById('bundles-remaining');
    if (!bundlesEl) return;

    var count = parseInt(bundlesEl.textContent, 10) || 12;

    function decrement() {
        if (count <= 1) return;
        count--;
        bundlesEl.textContent = String(count);
        // Schedule next decrement at a random interval (30-90 seconds)
        var next = (Math.random() * 60 + 30) * 1000;
        setTimeout(decrement, next);
    }

    // First decrement after 20-50 seconds
    var first = (Math.random() * 30 + 20) * 1000;
    setTimeout(decrement, first);
})();
