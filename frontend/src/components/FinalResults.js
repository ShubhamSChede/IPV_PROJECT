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