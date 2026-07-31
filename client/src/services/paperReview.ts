const API_URL ="http://localhost:8000";

const createFormData = (file: File) => {
  const formData = new FormData();
  formData.append("file", file);
  return formData;
};

const handleResponse = async (response: Response) => {
  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail ||
      data.message ||
      "Something went wrong"
    );
  }
  return data;
};

export const reviewPaper = async (file: File) => {
  const response = await fetch(
    `${API_URL}/paper-review/review`,
    {
      method: "POST",
      body: createFormData(file),
    }
  );

  return handleResponse(response);
};

export const reviewOnly = async (file: File) => {
  const response = await fetch(
    `${API_URL}/paper-review/review-only`,
    {
      method: "POST",
      body: createFormData(file),
    }
  );

  return handleResponse(response);
};

export const plagiarismOnly = async (file: File) => {
  const response = await fetch(
    `${API_URL}/paper-review/plagiarism-only`,
    {
      method: "POST",
      body: createFormData(file),
    }
  );

  return handleResponse(response);
};

export const technicalReviewOnly = async (file: File) => {
  const response = await fetch(
    `${API_URL}/paper-review/technical-review`,
    {
      method: "POST",
      body: createFormData(file),
    }
  );

  return handleResponse(response);
};