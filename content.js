const loadTesseract = () => {
  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = chrome.runtime.getURL("libs/tesseract.min.js");
    document.head.appendChild(script);

    script.onload = () => {
      console.log("Tesseract.js loaded");
      resolve();
    };

    script.onerror = () => {
      console.error("Failed to load Tesseract.js");
      reject(new Error("Failed to load Tesseract.js"));
    };
  });
};

async function processTextQuestions() {
  const questions = document.querySelectorAll("[role='listitem']");
  console.log("Questions:", questions);

  questions.forEach(async (questionElement) => {
    const questionTextElement = questionElement.querySelector("div[role='heading']");
    const radioGroup = questionElement.querySelector("[role='radiogroup']");
    let questionText = "";

    if (questionTextElement) {
      questionText = questionTextElement.innerText.trim();
    }

    if (radioGroup) {
    // Find all labels within the radiogroup
    const labels = radioGroup.querySelectorAll("label");

    // Extract text content from spans inside the labels
    const options = Array.from(labels).map((label, index) => {
      const optionSpan = label.querySelector("span"); // Find the span inside the label
      return `${index + 1}) ${optionSpan ? optionSpan.innerText.trim() : "Option not found"}`;
    });

      questionText += ` Choose from one of these MCQ Options: ${options}`;
    }

    if (questionText) {
      console.log(`Processing question: ${questionText}`);
      try {
        const response = await fetch("http://localhost:5000/get-answer", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ question: questionText }),
        });

        if (!response.ok) {
          console.error(`Error fetching answer for question: ${questionText}`);
          return;
        }

        const data = await response.json();
        const answer = data.answer || "No answer found";

        const answerNode = document.createElement("div");
        answerNode.textContent = `Answer: ${answer}`;
        answerNode.style.cssText = `
          margin-top: 8px;
          font-size: 14px;
          color: #1b5e20;
          background: #e8f5e9;
          border: 1px solid #4caf50;
          padding: 6px;
          border-radius: 4px;
        `;
        questionElement.appendChild(answerNode);
      } catch (error) {
        console.error("Error:", error);
      }
    }
  });
}

async function processImageQuestions() {
  const images = document.querySelectorAll("[role='listitem'] img");
  console.log("Images:", images);

  images.forEach(async (image) => {
    try {
      console.log("Processing image question...");
      const { data } = await Tesseract.recognize(image.src, "eng");
      const ocrText = data.text.trim();

      if (ocrText) {
        console.log(`Extracted OCR text: ${ocrText}`);

        const response = await fetch("http://localhost:5000/get-answer", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ question: ocrText }),
        });

        if (!response.ok) {
          console.error(`Error fetching answer for image text: ${ocrText}`);
          return;
        }

        const data = await response.json();
        const answer = data.answer || "No answer found";

        const container = image.closest("[role='listitem']");

        const ocrTextNode = document.createElement("div");
        ocrTextNode.textContent = `Extracted Text: ${ocrText}`;
        ocrTextNode.style.cssText = `
          margin-top: 8px;
          font-size: 12px;
          color: #333;
          background: #f9f9f9;
          border: 1px solid #ddd;
          padding: 6px;
          border-radius: 4px;
        `;
        container.appendChild(ocrTextNode);

        const answerNode = document.createElement("div");
        answerNode.textContent = `Answer: ${answer}`;
        answerNode.style.cssText = `
          margin-top: 8px;
          font-size: 14px;
          color: #1b5e20;
          background: #e8f5e9;
          border: 1px solid #4caf50;
          padding: 6px;
          border-radius: 4px;
        `;
        container.appendChild(answerNode);
      }
    } catch (error) {
      console.error("Error processing image:", error);
    }
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  console.log("Google Forms detected. Processing questions...");
  await loadTesseract();
  console.log("Processing text questions...");
  processTextQuestions();
  console.log("Processing image questions...");
  processImageQuestions();
});
