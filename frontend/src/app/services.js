"use client";

const API_BASE_URL = 'http://localhost:5000';

// ==== UPLOAD ENDPOINTS ====

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

// Upload only the element image
export async function uploadElementImage(elementImgFile) {
  const formData = new FormData();
  formData.append('element_img', elementImgFile);

  const response = await fetch(`${API_BASE_URL}/api/upload_element`, {
    method: 'POST',
    body: formData,
  });
  
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to upload element image');
  }
  
  return await response.json();
}

// Upload target image for an existing job
export async function uploadTargetImage(jobId, targetImgFile) {
  const formData = new FormData();
  formData.append('big_img', targetImgFile);

  const response = await fetch(`${API_BASE_URL}/api/upload_target/${jobId}`, {
    method: 'POST',
    body: formData,
  });
  
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to upload target image');
  }
  
  return await response.json();
}

// ==== PREPROCESS ENDPOINTS ====

// Step 2: Preprocess images
export async function preprocessImages(jobId) {
  const response = await fetch(`${API_BASE_URL}/api/preprocess/${jobId}`);
  
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to preprocess images');
  }
  
  return await response.json();
}

// Set or update block size
// In services.js
export async function setBlockSize(jobId, blockSize) {
  console.log(`Calling API to set block size ${blockSize} for job ${jobId}`);
  
  const response = await fetch(`${API_BASE_URL}/api/set_block_size/${jobId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ block_size: blockSize }),
  });
  
  if (!response.ok) {
    const text = await response.text();
    console.error('Error response:', text);
    try {
      const errorData = JSON.parse(text);
      throw new Error(errorData.error || 'Failed to set block size');
    } catch (e) {
      throw new Error(`Failed to set block size: ${response.status} ${response.statusText}`);
    }
  }
  
  return await response.json();
}

// Generate previews at different block sizes
export async function getMultiresolutionPreview(jobId) {
  const response = await fetch(`${API_BASE_URL}/api/multiresolution_preview/${jobId}`);
  
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to generate multiresolution previews');
  }
  
  return await response.json();
}

// ==== GENERATION ENDPOINTS ====

// Step 3: Generate mosaic
export async function generateMosaic(jobId) {
  const response = await fetch(`${API_BASE_URL}/api/generate_mosaic/${jobId}`);
  
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to generate mosaic');
  }
  
  return await response.json();
}

// Generate mosaics at multiple resolutions
export async function generateMultiresolutionMosaics(jobId) {
  const response = await fetch(`${API_BASE_URL}/api/multiresolution/${jobId}`);
  
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to generate multiresolution mosaics');
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

// ==== FILTER ENDPOINTS ====

// Update applyFilter function
export async function applyFilter(jobId, filterName, options = {}) {
  console.log(`Applying filter ${filterName} to job ${jobId}`);
  
  const response = await fetch(`${API_BASE_URL}/api/apply_filter/${jobId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ filter: filterName, options }),
  });
  
  if (!response.ok) {
    // Handle HTML error responses properly
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.indexOf('application/json') !== -1) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to apply filter');
    } else {
      const text = await response.text();
      console.error('Server returned non-JSON response:', text.substring(0, 100));
      throw new Error(`Server error: ${response.status}`);
    }
  }
  
  return await response.json();
}

// Get list of available filters
export async function getAvailableFilters() {
  const response = await fetch(`${API_BASE_URL}/api/available_filters`);
  
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to get available filters');
  }
  
  return await response.json();
}

// Generate filter previews
export async function getFilterPreviews(jobId) {
  const response = await fetch(`${API_BASE_URL}/api/filter_preview/${jobId}`);
  
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to generate filter previews');
  }
  
  const data = await response.json();
  // Structure the response for component consumption
  return { 
    previews: data.filter_previews || {}  // Match the expected format in the FilterSelector component
  };
}

// Compare filters side by side
export async function compareFilters(jobId, filters = []) {
  const response = await fetch(`${API_BASE_URL}/api/compare_filters/${jobId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ filters }),
  });
  
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to compare filters');
  }
  
  return await response.json();
}

// ==== METRICS ENDPOINTS ====

// In services.js - Update getQualityMetrics
export async function getQualityMetrics(jobId) {
  const response = await fetch(`${API_BASE_URL}/api/metrics/${jobId}`);
  
  if (!response.ok) {
    console.warn('Failed to get metrics:', await response.text());
    // Return default N/A values instead of throwing
    return {
      ssim: null,
      mse: null,
      psnr: null
    };
  }
  
  try {
    const data = await response.json();
    // Return the metrics in the format expected by the component
    return {
      ssim: data.metrics?.ssim,
      mse: data.metrics?.mse,
      psnr: data.metrics?.psnr
    };
  } catch (error) {
    console.error('Error parsing metrics:', error);
    return {
      ssim: null,
      mse: null,
      psnr: null
    };
  }
}

// Compare metrics for different block sizes or filters
export async function compareMetrics(jobId) {
  const response = await fetch(`${API_BASE_URL}/api/metrics/compare/${jobId}`);
  
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to compare metrics');
  }
  
  return await response.json();
}

// Calculate metrics for multiple jobs
export async function batchCalculateMetrics(jobIds) {
  const response = await fetch(`${API_BASE_URL}/api/metrics/batch`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ job_ids: jobIds }),
  });
  
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to calculate batch metrics');
  }
  
  return await response.json();
}

// ==== UTILITY ENDPOINTS ====

// Get current job status
export async function getJobStatus(jobId) {
  const response = await fetch(`${API_BASE_URL}/api/job/${jobId}`);
  
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to get job status');
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
    ...(jobStatus.final_outputs || {}),
    ...(jobStatus.filter_outputs || {}),
    ...(jobStatus.multiresolution_outputs || {}),
    ...(jobStatus.metrics || {})
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