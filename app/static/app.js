const elements = {
  analyzeButton: document.getElementById("analyze-button"),
  errorPanel: document.getElementById("error-panel"),
  errorCode: document.getElementById("error-code"),
  errorMessage: document.getElementById("error-message"),
  errorDetail: document.getElementById("error-detail"),
  errorRaw: document.getElementById("error-raw"),
  emptyState: document.getElementById("empty-state"),
  results: document.getElementById("results"),
  previewImage: document.getElementById("preview-image"),
  previewMeta: document.getElementById("preview-meta"),
  planConfidence: document.getElementById("plan-confidence"),
  planSummary: document.getElementById("plan-summary"),
  planCurrentView: document.getElementById("plan-current-view"),
  planGoals: document.getElementById("plan-goals"),
  planNextSteps: document.getElementById("plan-next-steps"),
  planRisks: document.getElementById("plan-risks"),
  rawJson: document.getElementById("raw-json"),
};

function formatConfidence(value) {
  return `Confidence ${Math.round(value * 100)}%`;
}

function surfaceLabel(surfaceType) {
  if (surfaceType === "monitor") return "Monitor";
  if (surfaceType === "window") return "Window";
  if (surfaceType === "browser") return "Tab";
  return "Unknown source";
}

function showElement(element, shouldShow) {
  element.classList.toggle("hidden", !shouldShow);
}

function resetList(element, items) {
  element.innerHTML = "";
  items.forEach((item) => {
    const listItem = document.createElement("li");
    listItem.textContent = item;
    element.appendChild(listItem);
  });
}

function normalizeError(error) {
  if (error && typeof error === "object" && "code" in error && "message" in error) {
    return error;
  }

  if (error instanceof Error) {
    return {
      code: "UNKNOWN_ERROR",
      message: error.message,
    };
  }

  return {
    code: "UNKNOWN_ERROR",
    message: "An unknown error occurred.",
  };
}

async function captureBrowserSurface() {
  if (!navigator.mediaDevices?.getDisplayMedia) {
    throw {
      code: "CAPTURE_UNSUPPORTED",
      message: "This browser does not support screen capture. Use a recent Chromium-based browser.",
    };
  }

  let stream;
  try {
    stream = await navigator.mediaDevices.getDisplayMedia({
      video: {
        displaySurface: "monitor",
        frameRate: { ideal: 1, max: 2 },
      },
      audio: false,
      preferCurrentTab: false,
      selfBrowserSurface: "exclude",
      surfaceSwitching: "include",
      monitorTypeSurfaces: "include",
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "NotAllowedError") {
      throw {
        code: "CAPTURE_DENIED",
        message: "Capture permission was denied or canceled. Re-run the action and approve the browser picker.",
      };
    }

    throw {
      code: "CAPTURE_START_FAILED",
      message: error instanceof Error ? error.message : "The browser could not start the capture flow.",
    };
  }

  const videoTrack = stream.getVideoTracks()[0];
  const settings = videoTrack?.getSettings?.() ?? {};
  const surfaceType = settings.displaySurface ?? "unknown";

  const video = document.createElement("video");
  video.srcObject = stream;
  video.muted = true;
  video.playsInline = true;

  try {
    await video.play();
    await new Promise((resolve, reject) => {
      if (video.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA) {
        resolve();
        return;
      }

      const handleLoadedData = () => {
        cleanup();
        resolve();
      };

      const handleError = () => {
        cleanup();
        reject(new Error("The browser could not load the captured video stream."));
      };

      const cleanup = () => {
        video.removeEventListener("loadeddata", handleLoadedData);
        video.removeEventListener("error", handleError);
      };

      video.addEventListener("loadeddata", handleLoadedData, { once: true });
      video.addEventListener("error", handleError, { once: true });
    });

    const width = video.videoWidth;
    const height = video.videoHeight;

    if (!width || !height) {
      throw {
        code: "CAPTURE_EMPTY_FRAME",
        message: "The browser capture returned an empty frame.",
      };
    }

    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const context = canvas.getContext("2d");

    if (!context) {
      throw {
        code: "CAPTURE_CANVAS_ERROR",
        message: "Failed to create a canvas context for the screenshot.",
      };
    }

    context.drawImage(video, 0, 0, width, height);

    return {
      dataUrl: canvas.toDataURL("image/png"),
      width,
      height,
      surfaceType,
    };
  } finally {
    video.pause();
    video.srcObject = null;
    stream.getTracks().forEach((track) => track.stop());
  }
}

async function analyzeImage(image) {
  const response = await fetch("/api/analyze", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ image }),
  });

  const payload = await response.json().catch(() => null);

  if (!response.ok) {
    throw payload ?? {
      code: "API_ERROR",
      message: "The Python backend returned an unexpected error.",
    };
  }

  return payload;
}

function renderError(error) {
  const normalized = normalizeError(error);

  elements.errorCode.textContent = normalized.code;
  elements.errorMessage.textContent = normalized.message;
  elements.errorDetail.textContent = normalized.details ?? "";
  elements.errorRaw.textContent = normalized.rawResponse ?? "";

  showElement(elements.errorDetail, Boolean(normalized.details));
  showElement(elements.errorRaw, Boolean(normalized.rawResponse));
  showElement(elements.errorPanel, true);
  showElement(elements.results, false);
  showElement(elements.emptyState, true);
}

function renderResult(result) {
  const { image, plan, rawResponse } = result;
  elements.previewImage.src = image.dataUrl;
  elements.previewMeta.textContent = `${surfaceLabel(image.surfaceType)} · ${image.width} x ${image.height}`;
  elements.planConfidence.textContent = formatConfidence(plan.confidence);
  elements.planSummary.textContent = plan.summary;
  elements.planCurrentView.textContent = ` ${plan.current_view}`;
  resetList(elements.planGoals, plan.goals);
  resetList(elements.planNextSteps, plan.next_steps);
  resetList(elements.planRisks, plan.risks);
  elements.rawJson.textContent = rawResponse;

  showElement(elements.errorPanel, false);
  showElement(elements.emptyState, false);
  showElement(elements.results, true);
}

async function handleAnalyze() {
  elements.analyzeButton.disabled = true;
  elements.analyzeButton.textContent = "Capturing And Analyzing...";
  showElement(elements.errorPanel, false);

  try {
    const image = await captureBrowserSurface();
    const result = await analyzeImage(image);
    renderResult(result);
  } catch (error) {
    renderError(error);
  } finally {
    elements.analyzeButton.disabled = false;
    elements.analyzeButton.textContent = "Capture And Analyze";
  }
}

elements.analyzeButton.addEventListener("click", () => {
  void handleAnalyze();
});
