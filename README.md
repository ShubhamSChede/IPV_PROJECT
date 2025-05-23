# IPV_PROJECT
# Enhanced Mosaic Generator

A powerful image mosaic generator with advanced features including color support, adjustable resolution, post-processing filters, and quality metrics.

## Features

### Core Features
- **Color Mosaic Generation**: Create vibrant color mosaics using RGB images
- **Adjustable Block Size**: Control the resolution of your mosaic with configurable block sizes
- **Visual Effect Filters**: Apply various post-processing filters like sepia, vintage, or pop art
- **Quality Metrics**: Evaluate mosaic quality with SSIM, MSE, and PSNR measurements

### Additional Features
- **Step-by-Step Processing**: Upload, preprocess, generate, and enhance in separate steps
- **Multi-Resolution Comparison**: Generate and compare mosaics at different block sizes
- **Filter Previews**: Preview how different filters affect your mosaic
- **Comprehensive API**: Full API with documentation and status tracking

## Project Structure

```
mosaic_generator/
├── app.py                  # Main application entry point
├── config.py               # Configuration settings
├── utils/                  # Utility functions
│   ├── __init__.py
│   ├── file_utils.py       # File handling functions
│   ├── image_utils.py      # Basic image manipulation functions
│   └── validation.py       # Input validation functions
├── core/                   # Core algorithms
│   ├── __init__.py
│   ├── color_analysis.py   # Color histogram and matching algorithms
│   ├── mosaic.py           # Core mosaic generation logic
│   ├── filters.py          # Post-processing filter effects
│   └── metrics.py          # SSIM and other quality metrics
├── api/                    # API endpoints
│   ├── __init__.py
│   ├── upload.py           # File upload endpoints
│   ├── preprocess.py       # Image preprocessing endpoints
│   ├── generation.py       # Mosaic generation endpoints
│   ├── filters.py          # Filter application endpoints
│   └── metrics.py          # Quality metrics endpoints
└── static/                 # Generated at runtime
    ├── uploads/            # Directory for uploaded files
    ├── temp/               # Directory for intermediate results
    └── outputs/            # Directory for final outputs
```

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/mosaic-generator.git
   cd mosaic-generator
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Running the Server

Start the Flask server:
```
python app.py
```

By default, the server runs on `http://localhost:5000`.

### API Usage

#### Basic Workflow

1. **Upload Images**:
   ```
   POST /api/upload
   ```
   Form data:
   - `element_img`: The small image used as building block
   - `big_img`: The target image to recreate
   - `block_size` (optional): Size of each mosaic block
   - `color_mode` (optional): 'rgb' or 'grayscale'

2. **Preprocess Images**:
   ```
   GET /api/preprocess/{job_id}
   ```

3. **Generate Mosaic**:
   ```
   GET /api/generate_mosaic/{job_id}
   ```

4. **Apply Filter** (optional):
   ```
   POST /api/apply_filter/{job_id}
   ```
   JSON body:
   ```json
   {
     "filter": "sepia"
   }
   ```

5. **Calculate Metrics** (optional):
   ```
   GET /api/metrics/{job_id}
   ```

#### Advanced Options

- **Preview Different Block Sizes**:
  ```
  GET /api/multiresolution_preview/{job_id}
  ```

- **Generate Multiple Block Sizes**:
  ```
  GET /api/multiresolution/{job_id}?block_sizes=8,16,32
  ```

- **Preview All Filters**:
  ```
  GET /api/filter_preview/{job_id}
  ```

- **Compare Multiple Filters**:
  ```
  POST /api/compare_filters/{job_id}
  ```
  JSON body:
  ```json
  {
    "filters": ["sepia", "vintage", "pop_art"]
  }
  ```

- **Compare Metrics**:
  ```
  GET /api/metrics/compare/{job_id}?type=resolution
  ```

### API Documentation

Full API documentation is available at:
```
GET /api/docs
```

## Available Filters

- `none`: No filter
- `sepia`: Sepia tone effect
- `grayscale`: Black & white conversion
- `vintage`: Vintage photo effect
- `pop_art`: Pop art style effect
- `posterize`: Posterization effect
- `negative`: Negative/inverse effect
- `blur`: Gaussian blur effect
- `sharpen`: Image sharpening
- `edge_enhance`: Edge enhancement effect

## Requirements

- Python 3.6+
- Flask
- NumPy
- Pillow (PIL)
- OpenCV (cv2)
- scikit-image
- matplotlib
- Flask-CORS

A complete list of dependencies is in `requirements.txt`.

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.