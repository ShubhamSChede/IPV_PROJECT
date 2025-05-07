"use client";
import { useState, useEffect } from 'react';
import { 
  getMultiresolutionPreview, 
  getAvailableFilters, 
  getFilterPreviews, 
  applyFilter, 
  setBlockSize,
  getQualityMetrics ,
  generateMosaic
} from './services';

// Component for file upload form
export function FileUploadForm({ onSubmit, loading }) {
  const [elementImg, setElementImg] = useState(null);
  const [bigImg, setBigImg] = useState(null);

  const handleElementImgChange = (e) => {
    if (e.target.files?.[0]) {
      setElementImg(e.target.files[0]);
    }
  };

  const handleBigImgChange = (e) => {
    if (e.target.files?.[0]) {
      setBigImg(e.target.files[0]);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!elementImg || !bigImg) {
      return;
    }

    const formData = new FormData();
    formData.append('element_img', elementImg);
    formData.append('big_img', bigImg);
    
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg shadow-md mb-8">
      <div className="mb-4">
        <label htmlFor="element-img" className="block text-sm font-medium text-gray-700 mb-2">
          Element Image (Building Block):
        </label>
        <input
          type="file"
          id="element-img"
          accept="image/png,image/jpeg,image/jpg"
          onChange={handleElementImgChange}
          className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
        />
      </div>

      <div className="mb-6">
        <label htmlFor="big-img" className="block text-sm font-medium text-gray-700 mb-2">
          Target Image:
        </label>
        <input
          type="file"
          id="big-img"
          accept="image/png,image/jpeg,image/jpg"
          onChange={handleBigImgChange}
          className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
        />
      </div>

      <button 
        type="submit" 
        className={`w-full py-2 px-4 rounded-md font-medium text-white ${
          loading || !elementImg || !bigImg 
            ? 'bg-indigo-300 cursor-not-allowed' 
            : 'bg-indigo-600 hover:bg-indigo-700'
        } transition duration-150 ease-in-out`}
        disabled={loading || !elementImg || !bigImg}
      >
        {loading ? 'Uploading...' : 'Start Mosaic Generation'}
      </button>
    </form>
  );
}

// Component to display progress steps
export function ProgressSteps({ currentStep, jobStatus }) {
  const steps = [
    { id: 'upload', name: 'Upload Images' },
    { id: 'preprocess', name: 'Preprocess' },
    { id: 'generate', name: 'Generate Mosaic' },
    { id: 'complete', name: 'Complete' }
  ];

  return (
    <div className="mb-8">
      <div className="flex items-center justify-between mb-2">
        {steps.map((step, index) => (
          <div key={step.id} className="flex flex-col items-center">
            <div 
              className={`w-10 h-10 flex items-center justify-center rounded-full border-2 ${
                currentStep >= index 
                  ? 'bg-indigo-600 border-indigo-600 text-white' 
                  : 'bg-white border-gray-300 text-gray-500'
              }`}
            >
              {currentStep > index ? (
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                index + 1
              )}
            </div>
            <span className="mt-2 text-sm font-medium text-gray-700">{step.name}</span>
          </div>
        ))}
      </div>
      
      <div className="relative">
        <div className="absolute inset-0 flex items-center" aria-hidden="true">
          <div className="w-full h-0.5 bg-gray-200"></div>
        </div>
        <div className="relative flex justify-between">
          {steps.map((step, index) => (
            <div key={step.id} className={`w-0.5 h-0.5 ${
              currentStep >= index 
                ? 'bg-indigo-600' 
                : 'bg-gray-200'
            }`}></div>
          ))}
        </div>
      </div>
      
      {jobStatus && (
        <div className="mt-4 flex justify-between items-center">
          <div className="text-sm font-medium text-gray-700">
            Status: <span className="text-indigo-600">{jobStatus.status}</span>
          </div>
          <div className="text-sm font-medium text-gray-700">
            Progress: <span className="text-indigo-600">{jobStatus.progress}%</span>
          </div>
        </div>
      )}
    </div>
  );
}

// Component to display intermediate results with enhanced visualization
export function IntermediateResults({ outputs, jobStatus }) {
  if (!outputs || Object.keys(outputs).length === 0) {
    return null;
  }

  // Group outputs logically with enhanced details
  const groups = {
    'Input Images': ['element_url', 'big_url'],
    'Processed Images': ['resized_element', 'resized_big', 'adjusted_big'],
    'Generated Mosaics': ['simple_mosaic', 'partial_mosaic']
  };

  // Image type explanations
  const imageDescriptions = {
    'element_url': 'The small image used as building blocks for the mosaic',
    'big_url': 'The target image that will be recreated using element blocks',
    'resized_element': 'Element image resized to optimize processing',
    'resized_big': 'Target image resized to optimize processing',
    'adjusted_big': 'Target image with dimensions adjusted to fit the block grid',
    'simple_mosaic': 'Simple tiling of element images without color adjustment',
    'partial_mosaic': 'Partial rendering of the mosaic during generation'
  };

  // Filter outputs based on what's available
  const filteredGroups = {};
  Object.entries(groups).forEach(([groupName, keys]) => {
    const availableOutputs = keys.filter(key => outputs[key]).map(key => ({
      key,
      url: outputs[key],
      description: imageDescriptions[key] || ''
    }));
    
    if (availableOutputs.length > 0) {
      filteredGroups[groupName] = availableOutputs;
    }
  });

  return (
    <div className="bg-white p-6 rounded-lg shadow-md mb-8">
      <h2 className="text-xl font-semibold mb-4 text-gray-800">Processing Pipeline</h2>
      
      {/* Display processing details if available */}
      {jobStatus && <ProcessingDetails jobStatus={jobStatus} />}
      
      {Object.entries(filteredGroups).map(([groupName, items]) => (
        <div key={groupName} className="mb-6">
          <h3 className="text-lg font-medium mb-3 text-gray-700 border-b pb-1">{groupName}</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {items.map(item => (
              <div key={item.key} className="border rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-shadow">
                <h4 className="text-sm font-medium p-2 bg-gray-50 border-b text-center">
                  {item.key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
                </h4>
                <div className="p-2">
                  <img 
                    src={`http://localhost:5000${item.url}`}
                    alt={item.key}
                    className=" rounded"
                  />
                </div>
                {item.description && (
                  <div className="px-2 pb-2 text-xs text-gray-600">
                    {item.description}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// Component to display final results
export function FinalResults({ outputs }) {
  if (!outputs || Object.keys(outputs).length === 0) {
    return null;
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-2xl font-semibold mb-6 text-center text-gray-800">Final Results</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="border rounded-lg overflow-hidden shadow-sm">
          <h3 className="text-lg font-medium p-4 bg-gray-50 border-b text-center">Simple Mosaic</h3>
          <div className="p-4">
            <img 
              src={`http://localhost:5000${outputs.simple_mosaic}`}
              alt="Simple Mosaic"
              className="rounded"
            />
          </div>
          <div className="px-4 pb-4">
            <a 
              href={`http://localhost:5000${outputs.simple_mosaic}`}
              download
              target="_blank"
              rel="noopener noreferrer"
              className="block text-center py-2 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded transition duration-150 ease-in-out"
            >
              Download
            </a>
          </div>
        </div>
        
        <div className="border rounded-lg overflow-hidden shadow-sm">
          <h3 className="text-lg font-medium p-4 bg-gray-50 border-b text-center">Dynamic Mosaic</h3>
          <div className="p-4">
            <img 
              src={`http://localhost:5000${outputs.mosaic}`}
              alt="Dynamic Mosaic"
              className=" h-auto rounded"
            />
          </div>
          <div className="px-4 pb-4">
            <a 
              href={`http://localhost:5000${outputs.mosaic}`}
              download
              target="_blank"
              rel="noopener noreferrer"
              className="block text-center py-2 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded transition duration-150 ease-in-out"
            >
              Download
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}

// Component for error display
export function ErrorDisplay({ error, onDismiss }) {
  if (!error) return null;
  
  return (
    <div className="p-4 mb-6 text-red-700 bg-red-100 rounded-lg flex justify-between items-center">
      <p className="font-medium">Error: {error}</p>
      {onDismiss && (
        <button 
          onClick={onDismiss}
          className="ml-4 text-red-700 hover:text-red-800"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      )}
    </div>
  );
}

// In your BlockSizeSelector component
export function BlockSizeSelector({ jobId, onBlockSizeChange, loading }) {
  const [blockSizes, setBlockSizes] = useState([8, 16, 32, 64]);
  const [selectedSize, setSelectedSize] = useState(32);
  const [previews, setPreviews] = useState(null);
  const [isChangingSize, setIsChangingSize] = useState(false);
  const [error, setError] = useState(null);
  
  const handleSizeChange = async (size) => {
    if (isChangingSize || !jobId) return;
    
    setIsChangingSize(true);
    setError(null);
    
    try {
      // First update the UI to show the selection
      setSelectedSize(size);
      
      // Then call the API to update block size on the server
      console.log(`Setting block size to ${size} for job ${jobId}`);
      const result = await setBlockSize(jobId, size);
      console.log('Block size set result:', result);
      
      // Notify parent component
      if (onBlockSizeChange) {
        onBlockSizeChange(size);
      }
    } catch (error) {
      console.error("Failed to set block size:", error);
      setError(`Failed to set block size: ${error.message}`);
      // Revert selection if it failed
      setSelectedSize(selectedSize);
    } finally {
      setIsChangingSize(false);
    }
  };
  
  useEffect(() => {
    if (jobId) {
      const fetchPreviews = async () => {
        try {
          console.log(`Fetching multiresolution preview for job ${jobId}`);
          const result = await getMultiresolutionPreview(jobId);
          console.log('Preview result:', result);
          setPreviews(result.preview_outputs);
        } catch (error) {
          console.error("Failed to load block size previews:", error);
          setError(`Failed to load previews: ${error.message}`);
        }
      };
      
      fetchPreviews();
    }
  }, [jobId]);

  return (
    <div className="bg-white p-6 rounded-lg shadow-md mb-6">
      <h3 className="text-lg font-medium mb-3 text-gray-700">Block Size Selection</h3>
      
      {error && (
        <div className="mb-4 p-3 bg-red-50 text-red-700 text-sm rounded-md">
          {error}
        </div>
      )}
      
      <div className="flex flex-wrap gap-2 mb-4">
        {blockSizes.map((size) => (
          <button
            key={size}
            onClick={() => handleSizeChange(size)}
            disabled={loading || isChangingSize}
            className={`px-4 py-2 rounded-md text-sm font-medium ${
              selectedSize === size
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-800 hover:bg-gray-200'
            } transition-colors ${isChangingSize ? 'opacity-70 cursor-wait' : ''}`}
          >
            {size}x{size}
          </button>
        ))}
      </div>
      
      {isChangingSize && (
        <div className="text-sm text-gray-500 mb-3">
          Applying block size change...
        </div>
      )}
      
      {previews && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          {Object.entries(previews).map(([size, urls]) => (
            <div 
              key={size} 
              className={`border rounded overflow-hidden cursor-pointer ${
                selectedSize === parseInt(size) ? 'ring-2 ring-indigo-500' : ''
              }`}
              onClick={() => handleSizeChange(parseInt(size))}
            >
              <div className="p-2 bg-gray-50 text-center text-xs font-medium">
                {size}x{size}
              </div>
              <img 
                src={`http://localhost:5000${urls.mosaic}`}
                alt={`Preview at ${size}x${size}`}
                className=""
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Updated FilterSelector Component
export function FilterSelector({ jobId, onFilterApply, loading }) {
  const [filters, setFilters] = useState([]);
  const [selectedFilter, setSelectedFilter] = useState("none");
  const [filterPreviews, setFilterPreviews] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  
  // Fetch available filters
  useEffect(() => {
    const fetchFilters = async () => {
      try {
        const result = await getAvailableFilters();
        
        // Normalize the response format
        if (result.filters && typeof result.filters === 'object' && !Array.isArray(result.filters)) {
          const filtersArray = Object.entries(result.filters).map(([id, name]) => ({
            name: id,
            displayName: name
          }));
          setFilters(filtersArray);
        } else if (Array.isArray(result.filters)) {
          setFilters(result.filters);
        } else {
          console.warn('Unexpected filter data format:', result);
          // Fallback to default filters
          setFilters([
            { name: 'none', displayName: 'No Filter' },
            { name: 'sepia', displayName: 'Sepia' },
            { name: 'grayscale', displayName: 'Grayscale' }
          ]);
        }
      } catch (error) {
        console.error("Failed to load filters:", error);
        // Set default filters
        setFilters([
          { name: 'none', displayName: 'No Filter' },
          { name: 'sepia', displayName: 'Sepia' },
          { name: 'grayscale', displayName: 'Grayscale' }
        ]);
      }
    };
    
    fetchFilters();
  }, []);
  
  // Fetch filter previews
  useEffect(() => {
    if (jobId) {
      const fetchFilterPreviews = async () => {
        setIsLoading(true);
        try {
          const result = await getFilterPreviews(jobId);
          setFilterPreviews(result.previews);
        } catch (error) {
          console.error("Failed to load filter previews:", error);
        } finally {
          setIsLoading(false);
        }
      };
      
      fetchFilterPreviews();
    }
  }, [jobId]);
  
  const handleFilterChange = async (filter) => {
    try {
      setSelectedFilter(filter);
      
      // Call parent component's handler with the selected filter
      if (onFilterApply) {
        console.log(`Calling onFilterApply with filter: ${filter}`);
        await onFilterApply(filter);
      }
    } catch (error) {
      console.error("Error applying filter:", error);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md mb-6">
      <h3 className="text-lg font-medium mb-3 text-gray-700">Available Filters</h3>
      
      {isLoading && (
        <div className="flex justify-center items-center py-8">
          <svg className="animate-spin h-8 w-8 text-indigo-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span className="ml-2 text-gray-600">Loading filter previews...</span>
        </div>
      )}
      
      {(!filterPreviews || Object.keys(filterPreviews).length === 0) && !isLoading && (
        <div className="text-gray-500 text-center py-4">
          No filter previews available
        </div>
      )}
      
      {filterPreviews && Object.keys(filterPreviews).length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
          {Object.entries(filterPreviews).map(([filter, url]) => (
            <div 
              key={filter} 
              className={`bg-white border rounded-lg overflow-hidden cursor-pointer transition-all hover:shadow-md ${
                selectedFilter === filter ? 'ring-2 ring-indigo-500 shadow-md transform scale-[1.02]' : ''
              }`}
              onClick={() => handleFilterChange(filter)}
            >
              <div className="relative aspect-square overflow-hidden">
                <img 
                  src={`http://localhost:5000${url}`}
                  alt={`${filter} filter preview`}
                  className="object-cover"
                />
                {loading && selectedFilter === filter && (
                  <div className="absolute inset-0 bg-black bg-opacity-30 flex items-center justify-center">
                    <svg className="animate-spin h-8 w-8 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                  </div>
                )}
              </div>
              <div className={`p-2 text-center text-sm font-medium ${
                selectedFilter === filter ? 'bg-indigo-600 text-white' : 'bg-gray-50 text-gray-800'
              }`}>
                {filter.charAt(0).toUpperCase() + filter.slice(1)}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Component for Quality Metrics Display
export function QualityMetrics({ jobId }) {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    if (jobId) {
      const fetchMetrics = async () => {
        setLoading(true);
        try {
          const result = await getQualityMetrics(jobId);
          setMetrics(result);
        } catch (error) {
          console.error("Failed to load quality metrics:", error);
        } finally {
          setLoading(false);
        }
      };
      
      fetchMetrics();
    }
  }, [jobId]);

  if (loading) {
    return <div className="text-center p-4">Loading metrics...</div>;
  }
  
  if (!metrics) {
    return null;
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-md mt-6">
      <h3 className="text-lg font-medium mb-3 text-gray-900">Quality Metrics</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gray-50 p-4 rounded-lg border">
          <div className="text-sm font-medium text-gray-900 mb-1">SSIM</div>
          <div className="text-2xl font-bold">
            {typeof metrics.ssim === 'number' ? metrics.ssim.toFixed(4) : 'N/A'}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            Structural Similarity (higher is better)
          </div>
        </div>
        
        <div className="bg-gray-50 p-4 rounded-lg border">
          <div className="text-sm font-medium text-gray-900 mb-1">MSE</div>
          <div className="text-2xl font-bold">
            {typeof metrics.mse === 'number' ? metrics.mse.toFixed(2) : 'N/A'}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            Mean Squared Error (lower is better)
          </div>
        </div>
        
        <div className="bg-gray-50 p-4 rounded-lg border">
          <div className="text-sm font-medium text-gray-900 mb-1">PSNR</div>
          <div className="text-2xl font-bold">
            {typeof metrics.psnr === 'number' ? metrics.psnr.toFixed(2) + ' dB' : 'N/A'}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            Peak Signal-to-Noise Ratio (higher is better)
          </div>
        </div>
      </div>
      
      {metrics.comparison && (
        <div className="mt-6">
          <h4 className="text-md font-medium mb-2">Comparison Charts</h4>
          <img 
            src={`http://localhost:5000${metrics.comparison.chart_url}`}
            alt="Metrics comparison chart"
            className=" border rounded-lg"
          />
        </div>
      )}
    </div>
  );
}

// Enhanced FinalResults component with detailed information display
export function EnhancedFinalResults({ outputs: initialOutputs, jobId }) {
  // Use local state to manage outputs
  const [outputs, setOutputs] = useState(initialOutputs || {});
  const [selectedView, setSelectedView] = useState('dynamic');
  const [filterName, setFilterName] = useState(null);
  const [isApplyingChanges, setIsApplyingChanges] = useState(false);
  
  // Update local state when props change
  useEffect(() => {
    if (initialOutputs && Object.keys(initialOutputs).length > 0) {
      setOutputs(initialOutputs);
    }
  }, [initialOutputs]);
  
  // Handle filter application
  const handleFilterApply = async (filter) => {
    if (!jobId || filter === filterName || isApplyingChanges) return;
    
    console.log(`EnhancedFinalResults: Applying filter ${filter} to job ${jobId}`);
    setIsApplyingChanges(true);
    
    try {
      // This is the actual API call that applies the filter
      const result = await applyFilter(jobId, filter);
      console.log('Filter API response:', result);
      
      // Update state with the filter name
      setFilterName(filter);
      
      // Automatically switch view to filtered
      setSelectedView('filtered');
      
      // Check if we got a filtered mosaic back
      if (result.filter_outputs && result.filter_outputs.filtered_mosaic) {
        // Update our local state with the new filtered image URL
        setOutputs(prevOutputs => ({
          ...prevOutputs,
          filtered_mosaic: result.filter_outputs.filtered_mosaic
        }));
        console.log('Filter applied successfully, filtered_mosaic URL:', result.filter_outputs.filtered_mosaic);
      } else {
        console.warn('No filtered mosaic returned from server');
      }
    } catch (error) {
      console.error("Failed to apply filter:", error);
    } finally {
      setIsApplyingChanges(false);
    }
  };
  
  if (!outputs || Object.keys(outputs).length === 0) {
    return null;
  }

  // Image selection logic
  const getImageUrl = () => {
    switch (selectedView) {
      case 'simple':
        return outputs.simple_mosaic;
      case 'filtered':
        if (outputs.filtered_mosaic) {
          return outputs.filtered_mosaic;
        } else {
          setSelectedView('dynamic');
          return outputs.mosaic;
        }
      case 'dynamic':
      default:
        return outputs.mosaic;
    }
  };
  
  // Title based on selected view
  const getImageTitle = () => {
    switch (selectedView) {
      case 'simple':
        return 'Simple Mosaic';
      case 'filtered':
        return `Filtered Mosaic (${filterName || 'none'})`;
      case 'dynamic':
      default:
        return 'Dynamic Mosaic';
    }
  };

  // Image explanation based on selected view
  const getImageExplanation = () => {
    switch (selectedView) {
      case 'simple':
        return 'A basic mosaic created by simply repeating the element image without any color adjustments';
      case 'filtered':
        return `The dynamic mosaic with ${filterName || 'no'} filter effect applied as post-processing`;
      case 'dynamic':
      default:
        return 'A mosaic where each element block has been color-adjusted to match the corresponding area of the target image';
    }
  };

  return (
    <>
      {jobId && (
        <FilterSelector 
          jobId={jobId} 
          onFilterApply={handleFilterApply} 
          loading={isApplyingChanges} 
        />
      )}
      
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-2xl font-semibold mb-4 text-center text-gray-800">Final Results</h2>
        
        <div className="flex justify-center mb-6">
          <div className="inline-flex rounded-md shadow-sm" role="group">
            <button
              type="button"
              onClick={() => setSelectedView('simple')}
              className={`px-4 py-2 text-sm font-medium ${
                selectedView === 'simple'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              } border rounded-l-lg`}
            >
              Simple
            </button>
            <button
              type="button"
              onClick={() => setSelectedView('dynamic')}
              className={`px-4 py-2 text-sm font-medium ${
                selectedView === 'dynamic'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              } border-t border-b border-r`}
            >
              Dynamic
            </button>
            <button
              type="button"
              onClick={() => setSelectedView('filtered')}
              disabled={!outputs.filtered_mosaic}
              className={`px-4 py-2 text-sm font-medium ${
                selectedView === 'filtered'
                  ? 'bg-indigo-600 text-white'
                  : outputs.filtered_mosaic 
                    ? 'bg-white text-gray-700 hover:bg-gray-50' 
                    : 'bg-gray-100 text-gray-400 cursor-not-allowed'
              } border-t border-b border-r rounded-r-lg`}
            >
              Filtered
            </button>
          </div>
        </div>
        
        <div className="border rounded-lg overflow-hidden shadow-sm mb-6">
          <h3 className="text-lg font-medium p-4 bg-gray-50 border-b text-center">{getImageTitle()}</h3>
          <div className="p-4">
            <img 
              src={`http://localhost:5000${getImageUrl()}`}
              alt={getImageTitle()}
              className=" rounded"
            />
          </div>
          <div className="px-4 pb-2 text-sm text-center text-gray-600">
            {getImageExplanation()}
          </div>
          <div className="px-4 pb-4">
            <a 
              href={`http://localhost:5000${getImageUrl()}`}
              download
              target="_blank"
              rel="noopener noreferrer"
              className="block text-center py-2 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded transition duration-150 ease-in-out"
            >
              Download
            </a>
          </div>
        </div>
        
        {jobId && <QualityMetrics jobId={jobId} />}
      </div>
    </>
  );
}

// Component to display detailed processing information
export function ProcessingDetails({ jobStatus }) {
  if (!jobStatus) return null;
  
  // Extract different types of details
  const uploadDetails = jobStatus.upload_details || {};
  const elementDetails = jobStatus.element_details || {};
  const bigDetails = jobStatus.big_details || {};
  const mosaicPlanning = jobStatus.mosaic_planning || {};
  const generationInfo = jobStatus.generation_info || {};
  
  return (
    <div className="bg-white p-6 rounded-lg shadow-md mb-6">
      <h3 className="text-lg font-medium mb-4 text-gray-900">Processing Details</h3>
      
      {/* Upload Information */}
      {Object.keys(uploadDetails).length > 0 && (
        <div className="mb-6">
          <h4 className="text-md font-medium mb-2 text-gray-800 border-b pb-1">Upload Information</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm"><span className="font-medium">Element Image:</span> {uploadDetails.element_filename}</p>
              <p className="text-sm"><span className="font-medium">Size:</span> {uploadDetails.element_filesize_kb?.toFixed(2)} KB</p>
              <p className="text-sm"><span className="font-medium">Dimensions:</span> {uploadDetails.element_dimensions}</p>
            </div>
            <div>
              <p className="text-sm"><span className="font-medium">Target Image:</span> {uploadDetails.big_filename}</p>
              <p className="text-sm"><span className="font-medium">Size:</span> {uploadDetails.big_filesize_kb?.toFixed(2)} KB</p>
              <p className="text-sm"><span className="font-medium">Dimensions:</span> {uploadDetails.big_dimensions}</p>
            </div>
          </div>
        </div>
      )}
      
      {/* Element and Target Image Details */}
      {(Object.keys(elementDetails).length > 0 || Object.keys(bigDetails).length > 0) && (
        <div className="mb-6">
          <h4 className="text-md font-medium mb-2 text-gray-800 border-b pb-1">Image Processing</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.keys(elementDetails).length > 0 && (
              <div className="bg-gray-50 p-3 rounded">
                <p className="text-sm font-medium mb-1">Element Image Details:</p>
                <p className="text-xs"><span className="font-medium">Original Size:</span> {elementDetails.original_dimensions}</p>
                <p className="text-xs"><span className="font-medium">Processed Size:</span> {elementDetails.resized_dimensions?.[0]}×{elementDetails.resized_dimensions?.[1]}</p>
                <p className="text-xs"><span className="font-medium">Pixel Count:</span> {elementDetails.pixel_count?.toLocaleString()}</p>
                <p className="text-xs"><span className="font-medium">Color Mode:</span> {elementDetails.color_mode}</p>
                <p className="text-xs"><span className="font-medium">Memory Usage:</span> {elementDetails.memory_usage_mb?.toFixed(2)} MB</p>
              </div>
            )}
            
            {Object.keys(bigDetails).length > 0 && (
              <div className="bg-gray-50 p-3 rounded">
                <p className="text-sm font-medium mb-1">Target Image Details:</p>
                <p className="text-xs"><span className="font-medium">Original Size:</span> {bigDetails.original_dimensions}</p>
                <p className="text-xs"><span className="font-medium">Processed Size:</span> {bigDetails.resized_dimensions?.[0]}×{bigDetails.resized_dimensions?.[1]}</p>
                <p className="text-xs"><span className="font-medium">Pixel Count:</span> {bigDetails.pixel_count?.toLocaleString()}</p>
                <p className="text-xs"><span className="font-medium">Color Mode:</span> {bigDetails.color_mode}</p>
                <p className="text-xs"><span className="font-medium">Memory Usage:</span> {bigDetails.memory_usage_mb?.toFixed(2)} MB</p>
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* Mosaic Planning */}
      {Object.keys(mosaicPlanning).length > 0 && (
        <div className="mb-6">
          <h4 className="text-md font-medium mb-2 text-gray-800 border-b pb-1">Mosaic Configuration</h4>
          <div className="bg-gray-50 p-3 rounded">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              <p className="text-sm"><span className="font-medium">Block Size:</span> {mosaicPlanning.block_size}×{mosaicPlanning.block_size}</p>
              <p className="text-sm"><span className="font-medium">Grid Dimensions:</span> {mosaicPlanning.grid_dimensions}</p>
              <p className="text-sm"><span className="font-medium">Total Blocks:</span> {mosaicPlanning.total_blocks?.toLocaleString()}</p>
              <p className="text-sm"><span className="font-medium">Estimated Output Size:</span> {mosaicPlanning.estimated_output_dimensions}</p>
              <p className="text-sm"><span className="font-medium">Adjustments:</span> {mosaicPlanning.adjusted_dimensions}</p>
              <p className="text-sm"><span className="font-medium">Memory Usage:</span> {mosaicPlanning.estimated_memory_usage_mb?.toFixed(2)} MB</p>
            </div>
          </div>
        </div>
      )}
      
      {/* Generation Information */}
      {Object.keys(generationInfo).length > 0 && (
        <div>
          <h4 className="text-md font-medium mb-2 text-gray-800 border-b pb-1">Generation Statistics</h4>
          <div className="bg-gray-50 p-3 rounded">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              <p className="text-sm"><span className="font-medium">Processing Time:</span> {generationInfo.processing_time_sec} seconds</p>
              <p className="text-sm"><span className="font-medium">Algorithm:</span> {generationInfo.algorithm}</p>
              <p className="text-sm"><span className="font-medium">Element Shape:</span> {generationInfo.element_shape?.join('×')}</p>
              <p className="text-sm"><span className="font-medium">Target Shape:</span> {generationInfo.target_shape?.join('×')}</p>
              <p className="text-sm"><span className="font-medium">Output Shape:</span> {generationInfo.output_shape?.join('×')}</p>
              <p className="text-sm"><span className="font-medium">Memory Usage:</span> {generationInfo.memory_usage_mb?.toFixed(2)} MB</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

