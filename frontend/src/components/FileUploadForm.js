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