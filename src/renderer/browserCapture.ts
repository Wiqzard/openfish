import { capturedImageSchema, type CapturedImage } from '../shared/contracts';

type DisplayMediaOptionsWithCurrentTab = DisplayMediaStreamOptions & {
  preferCurrentTab?: boolean;
};

function waitForVideoFrame(video: HTMLVideoElement) {
  return new Promise<void>((resolve, reject) => {
    if (video.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA) {
      resolve();
      return;
    }

    const cleanup = () => {
      video.removeEventListener('loadeddata', handleLoadedData);
      video.removeEventListener('error', handleError);
    };

    const handleLoadedData = () => {
      cleanup();
      resolve();
    };

    const handleError = () => {
      cleanup();
      reject(new Error('The browser could not load the captured video stream.'));
    };

    video.addEventListener('loadeddata', handleLoadedData, { once: true });
    video.addEventListener('error', handleError, { once: true });
  });
}

export async function captureBrowserSurface(): Promise<CapturedImage> {
  if (!navigator.mediaDevices?.getDisplayMedia) {
    throw {
      code: 'CAPTURE_UNSUPPORTED',
      message:
        'This browser does not support screen or tab capture. Use a recent Chromium-based browser.',
    };
  }

  let stream: MediaStream;

  try {
    stream = await navigator.mediaDevices.getDisplayMedia({
      video: {
        frameRate: { ideal: 1, max: 2 },
      },
      audio: false,
      preferCurrentTab: true,
    } as DisplayMediaOptionsWithCurrentTab);
  } catch (error) {
    if (error instanceof DOMException && error.name === 'NotAllowedError') {
      throw {
        code: 'CAPTURE_DENIED',
        message:
          'Capture permission was denied or canceled. Re-run the action and approve the browser picker.',
      };
    }

    throw {
      code: 'CAPTURE_START_FAILED',
      message:
        error instanceof Error
          ? error.message
          : 'The browser could not start the capture flow.',
    };
  }

  const video = document.createElement('video');
  video.srcObject = stream;
  video.muted = true;
  video.playsInline = true;

  try {
    await video.play();
    await waitForVideoFrame(video);

    const width = video.videoWidth;
    const height = video.videoHeight;

    if (!width || !height) {
      throw {
        code: 'CAPTURE_EMPTY_FRAME',
        message: 'The browser capture returned an empty frame.',
      };
    }

    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;

    const context = canvas.getContext('2d');
    if (!context) {
      throw {
        code: 'CAPTURE_CANVAS_ERROR',
        message: 'Failed to create a canvas context for the screenshot.',
      };
    }

    context.drawImage(video, 0, 0, width, height);

    return capturedImageSchema.parse({
      dataUrl: canvas.toDataURL('image/png'),
      width,
      height,
    });
  } finally {
    video.pause();
    video.srcObject = null;
    stream.getTracks().forEach((track) => track.stop());
  }
}
