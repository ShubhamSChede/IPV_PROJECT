"use client";
import { useState } from 'react';

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

// Component to display intermediate results
export function IntermediateResults({ outputs }) {
  if (!outputs || Object.keys(outputs).length === 0) {
    return null;
  }

  // Group outputs logically
  const groups = {
    'Input Images': ['element_url', 'big_url', 'gray_element', 'gray_big'],
    'Processing Steps': ['resized_element', 'resized_big', 'adjusted_big', 'simple_mosaic', 'partial_mosaic']
  };

  // Filter outputs based on what's available
  const filteredGroups = {};
  Object.entries(groups).forEach(([groupName, keys]) => {
    const availableOutputs = keys.filter(key => outputs[key]).map(key => ({
      key,
      url: outputs[key]
    }));
    
    if (availableOutputs.length > 0) {
      filteredGroups[groupName] = availableOutputs;
    }
  });

  return (
    <div className="bg-white p-6 rounded-lg shadow-md mb-8">
      <h2 className="text-xl font-semibold mb-4 text-gray-800">Intermediate Results</h2>
      
      {Object.entries(filteredGroups).map(([groupName, items]) => (
        <div key={groupName} className="mb-6">
          <h3 className="text-lg font-medium mb-3 text-gray-700">{groupName}</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {items.map(item => (
              <div key={item.key} className="border rounded-lg overflow-hidden shadow-sm">
                <h4 className="text-sm font-medium p-2 bg-gray-50 border-b text-center">
                  {item.key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
                </h4>
                <div className="p-2">
                  <img 
                    src={`http://localhost:5000${item.url}`}
                    alt={item.key}
                    className="w-full h-auto rounded"
                  />
                </div>
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
              className="w-full h-auto rounded"
            />
          </div>
          <div className="px-4 pb-4">
            <a 
              href={`http://localhost:5000${outputs.simple_mosaic}`}
              download
              target="_blank"
              rel="noopener noreferrer"
              className="block w-full text-center py-2 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded transition duration-150 ease-in-out"
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
              className="w-full h-auto rounded"
            />
          </div>
          <div className="px-4 pb-4">
            <a 
              href={`http://localhost:5000${outputs.mosaic}`}
              download
              target="_blank"
              rel="noopener noreferrer"
              className="block w-full text-center py-2 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded transition duration-150 ease-in-out"
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