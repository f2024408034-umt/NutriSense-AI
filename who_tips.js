// ================================================================
// NUTRISENSE AI - WHO HEALTH TIPS WIDGET
// ================================================================
// This file creates a small floating card in the bottom-right
// corner of the page that shows rotating health tips.
//
// Tips are sourced from World Health Organization (WHO)
// guidelines on nutrition, hydration, and physical activity.
//
// How it works:
//   1. A list of tips is defined below (WHO_HEALTH_TIPS)
//   2. The widget HTML is injected into the page automatically
//   3. A timer rotates through the tips every few seconds
//   4. User can close the widget if they don't want to see it
//
// How to use this file:
//   Add this line before </body> in any page:
//   <script src="who_tips.js"></script>
//   Then call: initWhoTips();
// ================================================================


// ----------------------------------------------------------------
// TIP DATA
// ----------------------------------------------------------------
// Each tip is based on general WHO nutrition and health guidance.
// Feel free to add more tips to this array - the widget will
// automatically rotate through however many are listed here.
// ----------------------------------------------------------------
const WHO_HEALTH_TIPS = [
    "Drink at least 8 glasses of water daily to support digestion and energy levels.",
    "Aim for at least 150 minutes of moderate physical activity per week.",
    "Fill half your plate with fruits and vegetables at every meal.",
    "Limit free sugar intake to less than 10% of your total daily calories.",
    "Choose whole grains over refined grains for better long-term health.",
    "Reduce salt intake to less than 5 grams per day to support heart health.",
    "Include a source of protein in every meal to maintain muscle health.",
    "Avoid sugary drinks - water, milk, or unsweetened tea are healthier choices.",
    "Eating a variety of foods helps ensure you get all essential nutrients.",
    "Regular meals help maintain stable energy and blood sugar levels."
];

// How long each tip stays visible before switching (in milliseconds)
const TIP_ROTATION_INTERVAL = 7000;   // 7 seconds

// Keeps track of which tip is currently shown
let currentTipIndex = 0;

// Stores the timer so it can be stopped later if needed
let tipRotationTimer = null;


// ================================================================
// STEP 1 - INJECT WIDGET STYLES
// ================================================================
// Adds the CSS for the widget directly into the page <head>.
// Keeping this self-contained means the widget works on any
// page just by including this one script file.
// ================================================================
function injectWhoTipsStyles() {

    const styleTag = document.createElement("style");

    styleTag.textContent = `

        /* ============================================
           WHO TIPS WIDGET - Floating card container
           ============================================ */
        #whoTipsWidget {
            position: fixed;
            bottom: 24px;
            right: 24px;
            width: 300px;
            background: white;
            border-radius: 16px;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
            padding: 18px 20px;
            font-family: Arial, sans-serif;
            z-index: 9999;
            border-left: 5px solid #2E8B57;

            /* Slide-in animation when the widget first appears */
            animation: whoTipsSlideIn 0.5s ease-out;
        }

        /* ============================================
           HEADER ROW - Icon, title, and close button
           ============================================ */
        #whoTipsWidget .who-tips-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }

        #whoTipsWidget .who-tips-title {
            font-size: 13px;
            font-weight: bold;
            color: #2E8B57;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        #whoTipsWidget .who-tips-close {
            background: none;
            border: none;
            color: #999;
            font-size: 18px;
            cursor: pointer;
            line-height: 1;
            padding: 0 4px;
            transition: color 0.2s;
        }

        #whoTipsWidget .who-tips-close:hover {
            color: #333;
        }

        /* ============================================
           TIP TEXT - The rotating message itself
           ============================================ */
        #whoTipsWidget .who-tips-text {
            font-size: 14px;
            line-height: 1.6;
            color: #444;
            min-height: 44px;

            /* Fade transition when text changes */
            transition: opacity 0.4s ease;
        }

        /* Used to fade the text out before swapping content */
        #whoTipsWidget .who-tips-text.fading {
            opacity: 0;
        }

        /* ============================================
           FOOTER - Small WHO source credit
           ============================================ */
        #whoTipsWidget .who-tips-footer {
            margin-top: 10px;
            text-align: right;
            font-size: 11px;
            color: #aaa;
            font-weight: bold;
            letter-spacing: 0.5px;
        }

        /* ============================================
           ENTRANCE ANIMATION
           ============================================ */
        @keyframes whoTipsSlideIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        /* ============================================
           RESPONSIVE - Smaller width on mobile screens
           ============================================ */
        @media (max-width: 480px) {
            #whoTipsWidget {
                width: calc(100% - 32px);
                right: 16px;
                bottom: 16px;
            }
        }

    `;

    document.head.appendChild(styleTag);
}


// ================================================================
// STEP 2 - BUILD AND INSERT THE WIDGET HTML
// ================================================================
// Creates the widget's HTML structure and adds it to the page.
// ================================================================
function createWhoTipsWidget() {

    const widget = document.createElement("div");
    widget.id = "whoTipsWidget";

    widget.innerHTML = `
        <div class="who-tips-header">
            <span class="who-tips-title">💡 Health Tip</span>
            <button class="who-tips-close" onclick="closeWhoTipsWidget()" aria-label="Close health tip">✕</button>
        </div>

        <div class="who-tips-text" id="whoTipsText">
            ${WHO_HEALTH_TIPS[0]}
        </div>

        <div class="who-tips-footer">WHO</div>
    `;

    document.body.appendChild(widget);
}


// ================================================================
// STEP 3 - ROTATE THROUGH TIPS
// ================================================================
// Every few seconds, fades the current tip out, swaps the text,
// then fades the new tip back in. This creates a smooth visual
// transition instead of the text just jumping/changing instantly.
// ================================================================
function rotateToNextTip() {

    const textEl = document.getElementById("whoTipsText");
    if (!textEl) return;   // Widget might have been closed already

    // Step A: Fade the current tip out
    textEl.classList.add("fading");

    // Step B: After the fade-out finishes, swap the text and fade back in
    setTimeout(() => {

        currentTipIndex = (currentTipIndex + 1) % WHO_HEALTH_TIPS.length;
        textEl.textContent = WHO_HEALTH_TIPS[currentTipIndex];

        textEl.classList.remove("fading");

    }, 400);   // Matches the CSS transition duration above
}


// ================================================================
// STEP 4 - CLOSE THE WIDGET
// ================================================================
// Removes the widget from the page and stops the rotation timer.
// Called when the user clicks the ✕ close button.
// ================================================================
function closeWhoTipsWidget() {

    const widget = document.getElementById("whoTipsWidget");
    if (widget) widget.remove();

    if (tipRotationTimer) {
        clearInterval(tipRotationTimer);
        tipRotationTimer = null;
    }
}


// ================================================================
// MAIN ENTRY POINT
// ================================================================
// Call this function once when the page loads to start the widget.
// Example: initWhoTips();
// ================================================================
function initWhoTips() {

    // Don't create a duplicate widget if one already exists
    if (document.getElementById("whoTipsWidget")) return;

    injectWhoTipsStyles();
    createWhoTipsWidget();

    // Start rotating tips automatically
    tipRotationTimer = setInterval(rotateToNextTip, TIP_ROTATION_INTERVAL);
}