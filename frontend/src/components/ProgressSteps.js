"use client";

import { useState } from 'react';

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