// form + result
const form = document.getElementById("donationForm");
const resultCard = document.getElementById("resultCard");
const resultShell = document.getElementById("resultShell"); // 🔥 NEW

// main fields
const ngoName = document.getElementById("ngo_name");
const distance = document.getElementById("distance");
const score = document.getElementById("score");
const statusEl = document.getElementById("status");
const pickupTime = document.getElementById("pickup_time");
const reason = document.getElementById("reason");

// alternatives
let alternativesContainer = document.getElementById("alternativesContainer");

// API
const API_URL = "http://127.0.0.1:8000/process-food";

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const button = form.querySelector("button");
  button.innerText = "Analyzing...";
  button.disabled = true;

  try {
    // 📦 Build payload
    const data = {
      id: "don_" + Date.now(),
      source_name: document.getElementById("source_name").value,
      contact_phone: document.getElementById("contact_phone").value,

      food_type: document.getElementById("food_type").value,
      quantity: parseInt(document.getElementById("quantity").value),
      is_veg: document.getElementById("is_veg").value === "true",

      prepared_at:
        document.getElementById("prepared_at").value ||
        new Date().toISOString(),
      expiry_hours: parseInt(
        document.getElementById("expiry_hours").value
      ),

      pickup_address: document.getElementById("pickup_address").value,
      pickup_lat: parseFloat(
        document.getElementById("pickup_lat").value
      ),
      pickup_lng: parseFloat(
        document.getElementById("pickup_lng").value
      ),

      special_notes:
        document.getElementById("special_notes").value || ""
    };

    // 🚀 API call
    const response = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(data)
    });

    const result = await response.json();

    if (result.status !== "success") {
      throw new Error(result.message || "API error");
    }

    const res = result.data;

    console.log("FULL RESPONSE:", res);

    const match = res.match_result;
    const pickup = res.pickup_request || {};

    const recommended = match.recommended;
    const alternatives = match.alternatives || [];

    // =========================
    // ⭐ Recommended NGO
    // =========================
    ngoName.innerText = recommended.ngo_name;
    distance.innerText = recommended.distance_km;
    score.innerText = recommended.match_score;

    const statusMap = {
      notification_sent: "Notification sent",
      pickup_planned: "Pickup planned",
      pickup_confirmed: "Pickup confirmed",
      pending: "Pending"
    };

    statusEl.innerText = statusMap[pickup.status] || pickup.status || "Pending";
    pickupTime.innerText = pickup.pickup_time
      ? new Date(pickup.pickup_time).toLocaleString()
      : "N/A";

    // =========================
    // 🧠 AI reasoning
    // =========================
    reason.innerText = match.comparison_reason;

    // =========================
    // 📋 Alternatives
    // =========================
    if (alternativesContainer) {
      alternativesContainer.innerHTML = "";

      alternatives.forEach((ngo) => {
        const card = document.createElement("div");
        card.className = "alt-card";

        card.innerHTML = `
          <h4>${ngo.ngo_name}</h4>
          <p>${ngo.distance_km} km away</p>
          <p>Score: ${ngo.match_score}</p>
        `;

        card.addEventListener("click", () => {
          ngoName.innerText = ngo.ngo_name;
          distance.innerText = ngo.distance_km;
          score.innerText = ngo.match_score;
        });

        alternativesContainer.appendChild(card);
      });
    }

    // =========================
    // 🚀 SHOW RESULT (FIXED)
    // =========================
    resultShell.classList.remove("hidden"); // 🔥 NEW
    resultCard.classList.remove("hidden");

    resultShell.scrollIntoView({ behavior: "smooth" });

  } catch (err) {
    alert("Error: " + err.message);
  }

  button.innerText = "Process Donation";
  button.disabled = false;
});