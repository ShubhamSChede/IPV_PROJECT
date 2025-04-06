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