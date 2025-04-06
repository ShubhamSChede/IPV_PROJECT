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