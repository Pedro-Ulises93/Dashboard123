# Quick Start Guide

## Step 1: Start Rhino.Compute Server

Make sure Rhino.Compute is running on `http://localhost:8081`.

If you haven't set it up yet:
1. Navigate to `compute.rhino3d` directory
2. Follow the setup instructions in the Rhino.Compute documentation
3. Start the server (usually runs on port 8081 by default)

## Step 2: Start the Web Server

Choose one of these methods:

### Option A: Python (Recommended)
```bash
python server.py
```
Or on Windows:
```bash
server.bat
```

### Option B: Python Simple Server
```bash
python -m http.server 8000
```

### Option C: Node.js
```bash
npx http-server -p 8000
```

## Step 3: Open the Dashboard

Open your browser and navigate to:
```
http://localhost:8000
```

## Step 4: Select a GH File

1. Use the dropdown to select a Grasshopper definition file
2. The dashboard will automatically discover inputs and outputs
3. Fill in the input values
4. Click "Execute Definition"
5. View results in the 3D viewer

## Troubleshooting

### File Not Found Error

If you get a "file not found" error:

1. **For relative paths**: Make sure the GH files are accessible via your web server
   - Place files in a directory served by your web server
   - Update paths in `js/main.js` to match your file locations

2. **For absolute paths**: Use full Windows paths
   - Example: `C:/Users/YourName/Documents/file.gh`
   - Update the file paths in `js/main.js` to use absolute paths
   - Rhino.Compute will access them via `file://` URLs

### Cannot Connect to Rhino.Compute

1. Verify Rhino.Compute is running:
   ```
   http://localhost:8081/healthcheck
   ```

2. Check the URL in `js/config.js` matches your server

3. Ensure no firewall is blocking the connection

### Geometry Not Rendering

1. Check browser console (F12) for errors
2. Verify the output contains valid geometry data
3. Some complex geometry types may need additional parsing

## Example: Adding Your Own GH Files

Edit `js/main.js` and update the `ghFiles` array:

```javascript
const ghFiles = [
    { name: 'MyFile.gh', path: 'path/to/MyFile.gh' },
    // Add more files here
];
```

Or use absolute paths:
```javascript
const ghFiles = [
    { name: 'MyFile.gh', path: 'C:/Users/YourName/Documents/MyFile.gh' },
];
```
