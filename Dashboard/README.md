# Grasshopper Dashboard

A web-based dashboard for executing Grasshopper definitions via Rhino.Compute with real-time 3D visualization using Three.js.

## Features

- 📁 **GH File Selection**: Select Grasshopper definition files from local directories
- 🔍 **I/O Discovery**: Automatically discover inputs and outputs from GH definitions
- ✅ **Input Validation**: Validate and format user inputs before execution
- 🚀 **Rhino.Compute Integration**: Execute definitions via Rhino.Compute API
- 🎨 **3D Visualization**: Render geometry results in an interactive Three.js viewer
- 🎛️ **Interactive Controls**: Rotate, zoom, and explore rendered geometry

## Workflow

```
User Input (Web) 
    ↓
Validation & Formatting
    ↓
Send to Rhino.Compute 
    ↓
Grasshopper Definition Execution
    ↓
Return Results (JSON/Geometry)
    ↓
Render in Browser (Three.js)
```

## Prerequisites

1. **Rhino.Compute Server**: Must be running locally on `http://localhost:8081`
   - See [Rhino.Compute documentation](https://developer.rhino3d.com/guides/compute/development/) for setup instructions
   - Default port can be changed in `js/config.js`

2. **Web Server**: The dashboard needs to be served via HTTP (not file://)
   - Use Python: `python -m http.server 8000`
   - Use Node.js: `npx http-server`
   - Or any other web server

3. **Grasshopper Files**: Place `.gh` or `.ghx` files in accessible directories
   - Default paths configured in `js/config.js`
   - Currently configured to look in `compute.rhino3d/src/hops/definitions/`

## Installation

1. Clone or download this repository
2. Ensure Rhino.Compute server is running
3. Start a local web server in the project directory
4. Open `index.html` in your browser (via the web server URL)

## Configuration

Edit `js/config.js` to customize:

- **Compute Server URL**: Change `computeUrl` if your server runs on a different port
- **GH File Paths**: Add directories to search for Grasshopper files
- **Viewer Settings**: Adjust camera position, grid size, etc.

### File Path Configuration

For local GH files, you have two options:

1. **Serve files via HTTP** (Recommended): Place GH files in a directory accessible via your web server
   - Update paths in `js/config.js` to be relative to your web root
   - Files will be accessible via HTTP URLs

2. **Use absolute file paths**: Use full Windows paths (e.g., `C:/path/to/file.gh`)
   - Rhino.Compute can access local files via `file://` URLs
   - Update the file paths in `js/main.js` to use absolute paths

## Usage

1. **Select a GH File**: Choose a Grasshopper definition from the dropdown
2. **Review I/O**: Check the discovered inputs and outputs
3. **Enter Input Values**: Fill in the input fields based on parameter types
4. **Execute**: Click "Execute Definition" to run the computation
5. **View Results**: See output values and rendered geometry in the 3D viewer

## File Structure

```
.
├── index.html          # Main HTML file
├── styles.css          # Styling
├── js/
│   ├── config.js       # Configuration
│   ├── api-client.js   # Rhino.Compute API client
│   ├── input-validator.js  # Input validation and formatting
│   ├── renderer.js     # Three.js renderer
│   └── main.js         # Main application logic
└── README.md           # This file
```

## API Endpoints Used

- `GET /io?Pointer=<file_url>` - Get inputs/outputs from a GH definition
- `POST /grasshopper` - Execute a GH definition with input values

## Supported Input Types

- **Number**: Numeric values (integers and floats)
- **Point**: 3D coordinates in format "x,y,z" or "x,y"
- **String**: Text values
- **Boolean**: True/False values

## Geometry Rendering

The renderer supports basic geometry types:
- Points
- Lines/Curves
- Meshes
- Breps (via mesh representation)

More complex geometry types may require additional parsing logic.

## Troubleshooting

### Cannot connect to Rhino.Compute
- Ensure the server is running: Check `http://localhost:8081/healthcheck`
- Verify the URL in `js/config.js` matches your server configuration
- Check firewall settings

### GH file not found
- Verify the file path is correct
- Ensure files are accessible via the web server
- Check file permissions

### Geometry not rendering
- Check browser console for errors
- Verify the output contains valid geometry data
- Some geometry types may require additional parsing

## Development

To extend functionality:

1. **Add new input types**: Extend `InputValidator.parseParamType()` and `createInputField()`
2. **Add geometry parsers**: Extend `GeometryRenderer.parseGeometry()` and add specific parsers
3. **Customize UI**: Modify `index.html` and `styles.css`

## License

This project uses:
- [Three.js](https://threejs.org/) - 3D graphics library
- [Rhino.Compute](https://www.rhino3d.com/compute) - Computational geometry server

## Notes

- The dashboard requires CORS to be enabled if accessing files from different origins
- Local file access may be restricted by browser security policies
- For production use, consider implementing a backend proxy for file access
