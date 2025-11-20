const POLL_INTERVAL_MS = 1000;

let pollHandle = null;
let countdownHandle = null;
let currentQuestion = null;
let sessionStarted = false;
let timeLeft = 0;

// --- DOM elements ---
const questionTextEl = document.getElementById("question-text");
const answerButtons = [...document.querySelectorAll(".answer-btn")];
const questionCounterEl = document.getElementById("question-counter");
const timerEl = document.getElementById("timer");
const startSessionBtn = document.getElementById("start-session");
const introEl = document.getElementById("intro");
const startScreenEl = document.getElementById("start-screen");
const contentEl = document.querySelector(".content");
const mainCardEl = document.querySelector(".main-card");
const endScreenEl = document.getElementById("end-screen");
const correctSoundEl = document.getElementById("correct-sound");
const incorrectSoundEl = document.getElementById("incorrect-sound");
const FEEDBACK_DELAY_MS = 2000;

// --- Event listeners ---
answerButtons.forEach((btn) => {
  btn.addEventListener("click", () => submitAnswer(parseInt(btn.dataset.index, 10)));
});

if (startSessionBtn) {
  startSessionBtn.addEventListener("click", () => {
    sessionStarted = true;
    if (startScreenEl) startScreenEl.style.display = "none";
    if (contentEl) {
      contentEl.style.display = "block";
      contentEl.setAttribute("aria-hidden", "false");
    }
    hideIntroOverlay();
    showWaitingState("Waiting for the first question...");
    // Notify backend so the robot knows it can read the first question.
    try {
      fetch("/api/start", { method: "POST" }).catch(() => {});
    } catch (_) {
      /* network hiccup is non-fatal here */
    }
    startPolling();
  });
}

document.addEventListener("DOMContentLoaded", () => {
  setupIntroOverlay();
});

// --- Intro overlay helpers ---
function setupIntroOverlay() {
  const introDuration = 4200;
  const video = document.getElementById("intro-video");
  const overlay = document.getElementById("intro-play-overlay");

  const tryPlay = async () => {
    if (!video) return;
    try {
      await video.play();
    } catch (_) {
      if (overlay) overlay.style.display = "inline-block";
    }
  };

  tryPlay();

  if (overlay) {
    overlay.addEventListener("click", async () => {
      if (video) {
        try {
          await video.play();
        } catch (_) {
          /* no-op */
        }
      }
      overlay.style.display = "none";
    });
  }

  setTimeout(() => hideIntroOverlay(), introDuration);
}

function hideIntroOverlay() {
  try {
    const video = document.getElementById("intro-video");
    if (video) {
      video.pause();
      video.currentTime = 0;
    }
  } catch (_) {
    /* best effort */
  }
  if (introEl) introEl.style.display = "none";
}

// --- Polling + rendering ---
function startPolling() {
  if (pollHandle) return;
  fetchLatestQuestion(true);
  pollHandle = setInterval(() => fetchLatestQuestion(false), POLL_INTERVAL_MS);
}

function stopPolling() {
  if (pollHandle) {
    clearInterval(pollHandle);
    pollHandle = null;
  }
}

async function fetchLatestQuestion(forceUpdate) {
  if (!sessionStarted) return;
  try {
    const response = await fetch("/api/question", { cache: "no-cache" });
    if (!response.ok) {
      console.warn("Question poll failed", response.statusText);
      return;
    }
    const payload = await response.json();

    if (payload.finished && !payload.question) {
      showEndScreen();
      return;
    }

    if (!payload.question) {
      showWaitingState("Waiting for the next question...");
      return;
    }

    if (forceUpdate || !currentQuestion || currentQuestion.id !== payload.question.id) {
      renderQuestion(payload.question);
    }
  } catch (err) {
    console.error("Unable to fetch question", err);
  }
}

function renderQuestion(question) {
  currentQuestion = question;
  if (endScreenEl) endScreenEl.style.display = "none";
  if (mainCardEl) mainCardEl.style.display = "flex";

  questionTextEl.textContent = question.text;
  answerButtons.forEach((btn, idx) => {
    const optionText = Array.isArray(question.options) && typeof question.options[idx] !== "undefined"
      ? question.options[idx]
      : "";
    btn.textContent = `${String.fromCharCode(65 + idx)}) ${optionText}`;
    btn.disabled = !optionText;
    btn.classList.remove("correct", "incorrect");
    btn.style.visibility = optionText ? "visible" : "hidden";
  });

  const total = question.total_questions;
  const number = question.question_number;
  if (questionCounterEl) {
    if (number && total) {
      questionCounterEl.textContent = `Question ${number} / ${total}`;
    } else if (number) {
      questionCounterEl.textContent = `Question ${number}`;
    } else {
      questionCounterEl.textContent = "Question";
    }
  }

  startTimer(question.time_limit || 60);
}

function startTimer(seconds) {
  clearInterval(countdownHandle);
  timeLeft = seconds;
  updateTimerDisplay();
  countdownHandle = setInterval(() => {
    timeLeft -= 1;
    updateTimerDisplay();
    if (timeLeft <= 0) {
      clearInterval(countdownHandle);
      handleTimeout();
    }
  }, 1000);
}

function updateTimerDisplay() {
  if (timerEl) {
    const display = Math.max(timeLeft, 0);
    timerEl.textContent = `${display}s`;
  }
}

function lockAnswers() {
  answerButtons.forEach((btn) => (btn.disabled = true));
}

async function submitAnswer(selectedIndex) {
  if (!currentQuestion) return;
  lockAnswers();
  if (answerButtons[selectedIndex]) {
    answerButtons[selectedIndex].classList.add("selected");
  }

  const payload = {
    question_id: currentQuestion.id,
    choice: selectedIndex + 1,
  };

  try {
    const response = await fetch("/api/answer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    let result = null;
    try {
      result = await response.json();
    } catch (_) {
      /* ignore JSON errors */
    }

    if (!response.ok) {
      console.warn("Answer rejected", result);
      showWaitingState("Answer not accepted. Waiting for the next question...");
      return;
    }

    if (!result || typeof result !== "object") {
      showWaitingState("Answer submitted! Waiting for the next question...");
      return;
    }

    handleAnswerFeedback(selectedIndex, result);
  } catch (err) {
    console.error("Failed to submit answer", err);
    showWaitingState("Connection issue. Waiting for the next question...");
  }
}

function handleTimeout() {
  showWaitingState("Time's up! Waiting for the next question...");
  reportTimeout();
}

function showWaitingState(message) {
  if (questionTextEl) {
    questionTextEl.textContent = message;
  }
  lockAnswers();
  answerButtons.forEach((btn) => btn.classList.remove("selected", "correct", "incorrect"));
}

async function reportTimeout() {
  if (!currentQuestion) return;
  const payload = { question_id: currentQuestion.id };
  try {
    const response = await fetch("/api/timeout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      console.warn("Timeout not accepted", error);
    }
  } catch (err) {
    console.error("Failed to report timeout", err);
  }
}

function handleAnswerFeedback(selectedIndex, result) {
  const hasCorrectField = Boolean(result && Number.isInteger(result.correct_option));
  const correctIndex = hasCorrectField ? result.correct_option - 1 : null;
  const isCorrect = Boolean(result && result.correct === true);

  highlightAnswerButtons(selectedIndex, correctIndex, isCorrect);

  if (questionTextEl) {
    questionTextEl.textContent = isCorrect
      ? "Correct! Preparing the next question..."
      : "Incorrect. Waiting for the next question...";
  }

  playFeedbackSound(isCorrect);

  setTimeout(() => {
    showWaitingState("Waiting for the next question...");
  }, FEEDBACK_DELAY_MS);
}

function highlightAnswerButtons(selectedIndex, correctIndex, isCorrect) {
  answerButtons.forEach((btn) => btn.classList.remove("selected", "correct", "incorrect"));
  const inBounds = (idx) => typeof idx === "number" && idx >= 0 && idx < answerButtons.length;

  if (isCorrect && inBounds(selectedIndex)) {
    answerButtons[selectedIndex].classList.add("correct");
    return;
  }

  if (inBounds(selectedIndex)) {
    answerButtons[selectedIndex].classList.add("incorrect");
  }
  if (inBounds(correctIndex)) {
    answerButtons[correctIndex].classList.add("correct");
  }
}

function playFeedbackSound(isCorrect) {
  const audioEl = isCorrect ? correctSoundEl : incorrectSoundEl;
  if (!audioEl) return;
  try {
    audioEl.currentTime = 0;
    audioEl.play();
  } catch (_) {
    /* autoplay might be blocked; ignore */
  }
}

function showEndScreen() {
  clearInterval(countdownHandle);
  stopPolling();
  sessionStarted = false;
  if (mainCardEl) mainCardEl.style.display = "none";
  if (endScreenEl) {
    endScreenEl.style.display = "flex";
  }
  questionTextEl.textContent = "Thank you for playing Who Wants to Be a Furllionaire?";
  lockAnswers();
}
