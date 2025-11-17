// --- Dummy questions just for testing the GUI ---
const dummyQuestions = [
  {
    id: 1,
    text: "What is the capital of France?",
    options: ["Paris", "Madrid", "Berlin", "Rome"],
    correctIndex: 0,
    difficulty: "easy"
  },
  {
    id: 2,
    text: "Which planet is known as the Red Planet?",
    options: ["Venus", "Mars", "Jupiter", "Mercury"],
    correctIndex: 1,
    difficulty: "easy"
  },
  // ... add up to 8 for testing
];

let currentIndex = 0;
let currentQuestion = null;
let timer = null;
let timeLeft = 60;

// --- DOM elements ---
const questionTextEl = document.getElementById("question-text");
const answerButtons = [...document.querySelectorAll(".answer-btn")];
const questionCounterEl = document.getElementById("question-counter");
const timerEl = document.getElementById("timer");
const startSessionBtn = document.getElementById("start-session");
const introEl = document.getElementById("intro");
const startScreenEl = document.getElementById("start-screen");
const contentEl = document.querySelector(".content");
const correctSound = document.getElementById("correct-sound");
const incorrectSound = document.getElementById("incorrect-sound");

// --- Event listeners ---
answerButtons.forEach(btn => {
  btn.addEventListener("click", () => handleAnswer(parseInt(btn.dataset.index, 10)));
});

if (startSessionBtn) startSessionBtn.addEventListener("click", () => {
  // when Start pressed, reveal quiz content and begin
  if (startScreenEl) startScreenEl.style.display = "none";
  // hide end-screen if previously visible
  const endScreenEl = document.getElementById("end-screen");
  if (endScreenEl) endScreenEl.style.display = "none";
  if (contentEl) contentEl.style.display = "block";
  // ensure intro media is stopped/hidden
  if (introEl) introEl.style.display = "none";
  try {
    const introVideo = document.getElementById("intro-video");
    if (introVideo) {
      introVideo.pause();
      introVideo.currentTime = 0;
    }
  } catch (_) {}
  startSession();
});

// Try to autoplay video+audio; if blocked, show a tap-to-play overlay.
document.addEventListener("DOMContentLoaded", () => {
  const introDuration = 4200; // ms - matches CSS animation length

  const tryPlay = async () => {
    // Try to play the intro video (this file now includes its audio track).
    const video = document.getElementById("intro-video");
    if (!video) return;
    try {
      await video.play();
      // If the video starts, the intro can run with audio.
    } catch (err) {
      // autoplay blocked — show the overlay so user can start media
      const overlay = document.getElementById("intro-play-overlay");
      if (overlay) overlay.style.display = "inline-block";
    }
  };

  tryPlay();

  // If user clicks the overlay, start video playback and hide overlay.
  const overlayBtn = document.getElementById("intro-play-overlay");
  if (overlayBtn) {
    overlayBtn.addEventListener("click", async () => {
      const video = document.getElementById("intro-video");
      if (video) {
        try { await video.play(); } catch (_) {}
      }
      overlayBtn.style.display = "none";
    });
  }

  // Hide intro overlay after the duration (even if autoplay succeeded)
  setTimeout(() => {
    if (introEl) introEl.style.display = "none";
  }, introDuration);
});

// --- Functions ---

function startSession() {
  currentIndex = 0;
  if (dummyQuestions.length === 0) return;
  loadQuestion(dummyQuestions[currentIndex]);
}

function loadQuestion(q) {
  currentQuestion = q;
  questionTextEl.textContent = q.text;

  answerButtons.forEach((btn, i) => {
    btn.textContent = String.fromCharCode(65 + i) + ") " + q.options[i];
    btn.disabled = false;
    btn.classList.remove("correct", "incorrect");
  });

  questionCounterEl.textContent = `Question ${currentIndex + 1} / ${dummyQuestions.length}`;
  startTimer(60);
}

function startTimer(seconds) {
  clearInterval(timer);
  timeLeft = seconds;
  updateTimerDisplay();

  timer = setInterval(() => {
    timeLeft--;
    updateTimerDisplay();
    if (timeLeft <= 0) {
      clearInterval(timer);
      handleTimeout();
    }
  }, 1000);
}

function updateTimerDisplay() {
  timerEl.textContent = `${timeLeft}s`;
}

function lockAnswers() {
  answerButtons.forEach(btn => (btn.disabled = true));
}

function handleAnswer(selectedIndex) {
  clearInterval(timer);
  lockAnswers();

  const isCorrect = selectedIndex === currentQuestion.correctIndex;
  answerButtons[selectedIndex].classList.add(isCorrect ? "correct" : "incorrect");

  // play feedback sound if available
  try {
    if (isCorrect && correctSound) {
      correctSound.currentTime = 0;
      correctSound.play().catch(() => {});
    } else if (!isCorrect && incorrectSound) {
      incorrectSound.currentTime = 0;
      incorrectSound.play().catch(() => {});
    }
  } catch (_) {}

  // In a real setup we would POST to /api/answer here

  // Load next question after a 2.5 second delay to give feedback time
  setTimeout(() => {
    currentIndex++;
    if (currentIndex < dummyQuestions.length) {
      loadQuestion(dummyQuestions[currentIndex]);
    } else {
      showEndScreen();
    }
  }, 2500);
}

// Handle timer reaching zero: reveal correct answer, speak it, wait 5s then advance
function handleTimeout() {
  lockAnswers();
  if (!currentQuestion) return;

  const correctIdx = currentQuestion.correctIndex;
  const correctBtn = answerButtons[correctIdx];
  if (correctBtn) correctBtn.classList.add("correct");

  // After 5s, move to next question
  setTimeout(() => {
    currentIndex++;
    if (currentIndex < dummyQuestions.length) {
      loadQuestion(dummyQuestions[currentIndex]);
    } else {
      showEndScreen();
    }
  }, 5000);
}

function handleHelpClick() {
  // help was removed: hints are handled orally in the experiment
}
// (help/proactive behaviour removed — hints are given orally in the experiment)

function showEndScreen() {
  // stop any running timer
  clearInterval(timer);

  // hide the main question card and show a centered end-screen inside the card
  const mainCard = document.querySelector('.main-card');
  const endScreenEl = document.getElementById('end-screen');

  if (mainCard) mainCard.style.display = 'none';
  if (endScreenEl) {
    endScreenEl.style.display = 'flex';
  } else {
    // fallback: replace the question text if end-screen is not present
    questionTextEl.textContent = 'Thank you for playing Who Wants to Be a Furllionaire?';
  }

  // ensure answers are disabled
  answerButtons.forEach(btn => (btn.disabled = true));
}
