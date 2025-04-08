"use client";
import { useState, useEffect } from 'react';
import Head from 'next/head';
import { 
  FileUploadForm, 
  ProgressSteps, 
  IntermediateResults, 
  ErrorDisplay,
  EnhancedFinalResults, // Use the enhanced version instead of FinalResults
  BlockSizeSelector,
  FilterSelector,
  QualityMetrics
} from './components';

import { 
  uploadImages,
  uploadElementImage,
  uploadTargetImage, 
  preprocessImages,
  setBlockSize,
  getMultiresolutionPreview, 
  generateMosaic,
  generateMultiresolutionMosaics, 
  getJobStatus,
  generateMosaicLegacy,
  applyFilter,
  getAvailableFilters,
  getFilterPreviews,
  compareFilters,
  getQualityMetrics,
  compareMetrics, 
  combineOutputs, 
  pollJobStatus 
} from './services';

// Enum for process mode
const ProcessMode = {
  STEP_BY_STEP: 'step_by_step',
  LEGACY: 'legacy'
};

export default function Home() {
  // State for selected mode (step-by-step or legacy)
  const [processMode, setProcessMode] = useState(ProcessMode.STEP_BY_STEP);
  
  // Legacy mode state
  const [elementImg, setElementImg] = useState(null);
  const [bigImg, setBigImg] = useState(null);
  const [results, setResults] = useState(null);
  
  // Step-by-step mode state
  const [currentStep, setCurrentStep] = useState(0);
  const [jobId, setJobId] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [allOutputs, setAllOutputs] = useState({});
  
  // Common state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Handle legacy form inputs
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

  // Handle legacy form submission
  const handleLegacySubmit = async (e) => {
    e.preventDefault();
    
    if (!elementImg || !bigImg) {
      setError('Please select both images');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('element_img', elementImg);
      formData.append('big_img', bigImg);

      const data = await generateMosaicLegacy(formData);
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Step 1: Handle file upload for step-by-step mode
  const handleStepByStepUpload = async (formData) => {
    setLoading(true);
    setError(null);
    setCurrentStep(0);
    setJobStatus(null);
    setAllOutputs({});
    
    try {
      // Upload files and get job ID
      const uploadResult = await uploadImages(formData);
      setJobId(uploadResult.job_id);
      setJobStatus(uploadResult);
      setCurrentStep(1);
      
      // Update outputs
      setAllOutputs(combineOutputs(uploadResult));
      
      // Process Step 2: Preprocess
      await processPreprocessStep(uploadResult.job_id);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  // Step 2: Process images
  const processPreprocessStep = async (jobId) => {
    try {
      const preprocessResult = await preprocessImages(jobId);
      setJobStatus(preprocessResult);
      setCurrentStep(2);
      
      // Update outputs
      setAllOutputs(current => ({
        ...current,
        ...combineOutputs(preprocessResult)
      }));
      
      // Process Step 3: Generate Mosaic
      await processGenerateMosaicStep(jobId);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  // Step 3: Generate mosaic
  const processGenerateMosaicStep = async (jobId) => {
    try {
      const generateResult = await generateMosaic(jobId);
      setJobStatus(generateResult);
      setCurrentStep(3);
      
      // Update outputs with all intermediate and final results
      setAllOutputs(current => ({
        ...current,
        ...combineOutputs(generateResult)
      }));
      
      // Start polling for completion
      pollJobStatus(jobId, (status) => {
        setJobStatus(status);
        setAllOutputs(current => ({
          ...current,
          ...combineOutputs(status)
        }));
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Switch between step-by-step and legacy mode
  const handleModeSwitch = (mode) => {
    setProcessMode(mode);
    setError(null);
    
    // Reset state when switching modes
    if (mode === ProcessMode.STEP_BY_STEP) {
      setCurrentStep(0);
      setJobId(null);
      setJobStatus(null);
      setAllOutputs({});
    } else {
      setResults(null);
    }
  };

  // Simple progress calculation for legacy mode
  const calculateLegacyProgress = () => {
    if (!loading) return 0;
    // This is just a simple animation, not real progress
    return Math.floor(Date.now() / 1000) % 100;
  };

  return (
    <div className="min-h-screen py-8 px-4 bg-gray-50">
      <Head>
        <title>Mosaic Generator</title>
        <meta name="description" content="Generate beautiful mosaic images" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-center mb-6 text-indigo-700">Mosaic Generator</h1>
        
        <p className="text-center text-gray-600 mb-4">
          Upload a small element image and a target image to create a mosaic
        </p>

        {/* Mode selector */}
        <div className="flex justify-center mb-8">
          <div className="inline-flex rounded-md shadow-sm" role="group">
            <button
              type="button"
              onClick={() => handleModeSwitch(ProcessMode.STEP_BY_STEP)}
              className={`px-4 py-2 text-sm font-medium rounded-l-lg ${
                processMode === ProcessMode.STEP_BY_STEP
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              } border border-gray-200`}
            >
              Step-by-Step Process
            </button>
            <button
              type="button"
              onClick={() => handleModeSwitch(ProcessMode.LEGACY)}
              className={`px-4 py-2 text-sm font-medium rounded-r-lg ${
                processMode === ProcessMode.LEGACY
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              } border border-gray-200`}
            >
              One-Step Process
            </button>
          </div>
        </div>

        <ErrorDisplay error={error} onDismiss={() => setError(null)} />

        {processMode === ProcessMode.STEP_BY_STEP ? (
          <>
            {/* Step-by-step process */}
            <ProgressSteps currentStep={currentStep} jobStatus={jobStatus} />
            
            {currentStep === 0 ? (
              <FileUploadForm onSubmit={handleStepByStepUpload} loading={loading} />
            ) : (
              <>
                <IntermediateResults outputs={allOutputs} />
                {jobStatus?.status === 'completed' && (
                  <EnhancedFinalResults outputs={jobStatus.final_outputs} jobId={jobId} />
                )}
              </>
            )}
          </>
        ) : (
          <>
            {/* Legacy one-step process */}
            <form onSubmit={handleLegacySubmit} className="bg-white p-6 rounded-lg shadow-md mb-8">
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
                {loading ? 'Generating...' : 'Generate Mosaic'}
              </button>
              
              {loading && (
                <div className="mt-4">
                  <div className="w-full bg-gray-200 rounded-full h-2.5">
                    <div 
                      className="bg-indigo-600 h-2.5 rounded-full" 
                      style={{ width: `${calculateLegacyProgress()}%` }}
                    ></div>
                  </div>
                  <p className="text-center text-sm text-gray-500 mt-2">Processing...</p>
                </div>
              )}
            </form>

            {results && (
              <div className="bg-white p-6 rounded-lg shadow-md">
                <h2 className="text-2xl font-semibold mb-6 text-center text-gray-800">Results</h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="border rounded-lg overflow-hidden shadow-sm">
                    <h3 className="text-lg font-medium p-4 bg-gray-50 border-b text-center">Simple Mosaic</h3>
                    <div className="p-4">
                      <img 
                        src={`http://localhost:5000${results.simple_mosaic_url}`}
                        alt="Simple Mosaic"
                        className="w-full h-auto rounded"
                      />
                    </div>
                    <div className="px-4 pb-4">
                      <a 
                        href={`http://localhost:5000${results.simple_mosaic_url}`}
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
                        src={`http://localhost:5000${results.mosaic_url}`}
                        alt="Dynamic Mosaic"
                        className="w-full h-auto rounded"
                      />
                    </div>
                    <div className="px-4 pb-4">
                      <a 
                        href={`http://localhost:5000${results.mosaic_url}`}
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
            )}
          </>
        )}
      </main>
    </div>
  );
}