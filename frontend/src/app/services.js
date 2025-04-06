"use client";

const API_BASE_URL = 'http://localhost:5000';

// Step 1: Upload images and initialize job
export async function uploadImages(formData) {
  const response = await fetch(`${API_BASE_URL}/api/upload`, {
    method: 'POST',
    body: formData,
  });
  
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to upload images');
  }
  
  return await response.json();
}

// Step 2: Preprocess images
export async function preprocessImages(jobId) {
  const response = await fetch(`${API_BASE_URL}/api/preprocess/${jobId}`);
  
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to preprocess images');
  }
  
  return await response.json();
}

// Step 3: Generate mosaic
export async function generateMosaic(jobId) {
  const response = await fetch(`${API_BASE_URL}/api/generate_mosaic/${jobId}`);
  
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to generate mosaic');
  }
  
  return await response.json();
}

// Get current job status
export async function getJobStatus(jobId) {
  const response = await fetch(`${API_BASE_URL}/api/job/${jobId}`);
  
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to get job status');
  }
  
  return await response.json();
}

// Legacy method (single step)
export async function generateMosaicLegacy(formData) {
  const response = await fetch(`${API_BASE_URL}/api/generate_mosaic`, {
    method: 'POST',
    body: formData,
  });
  
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to generate mosaic');
  }
  
  return await response.json();
}

// Helper function to combine all outputs from job status
export function combineOutputs(jobStatus) {
  if (!jobStatus) return {};
  
  return {
    ...(jobStatus.element_url ? { element_url: jobStatus.element_url } : {}),
    ...(jobStatus.big_url ? { big_url: jobStatus.big_url } : {}),
    ...(jobStatus.intermediate_outputs || {}),
    ...(jobStatus.final_outputs || {})
  };
}

// Poll job status until complete or error
export async function pollJobStatus(jobId, onUpdate, intervalMs = 1000) {
  try {
    const status = await getJobStatus(jobId);
    onUpdate(status);
    
    if (status.status === 'completed' || status.status === 'error') {
      return status;
    }
    
    // Continue polling
    return new Promise(resolve => {
      setTimeout(async () => {
        const result = await pollJobStatus(jobId, onUpdate, intervalMs);
        resolve(result);
      }, intervalMs);
    });
  } catch (error) {
    throw error;
  }
}