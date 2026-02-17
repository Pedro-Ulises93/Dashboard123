import json
import os

# ghpython component inputs:
# M: Mesh (item access)
# path: str (item access)  
# export: bool (item access)

# CRITICAL: In ghpython, 'result' must be assigned at the module level
# Make sure this variable name matches your output parameter name

result = "Script started"

try:
    # Check inputs safely
    has_export = False
    has_mesh = False
    has_path = False
    
    # Check export
    try:
        if export:
            has_export = True
    except:
        pass
    
    # Check mesh
    try:
        if M is not None:
            has_mesh = True
    except:
        pass
    
    # Check path
    try:
        if path and isinstance(path, str) and len(path.strip()) > 0:
            has_path = True
            file_path = path.strip()
        else:
            file_path = ""
    except:
        file_path = ""
    
    # Determine status
    if not has_export:
        result = "Set export = True"
    elif not has_mesh:
        result = "Connect mesh to M"
    elif not has_path:
        result = "Set file path"
    else:
        # All inputs valid - proceed with export
        try:
            if M.Vertices.Count == 0:
                result = "Mesh has no vertices"
            elif M.Faces.Count == 0:
                result = "Mesh has no faces"
            else:
                # Extract data
                vertices = []
                faces = []
                
                for i in range(M.Vertices.Count):
                    v = M.Vertices[i]
                    vertices.extend([v.X, v.Y, v.Z])
                
                for i in range(M.Faces.Count):
                    f = M.Faces[i]
                    faces.extend([f.A, f.B, f.C])
                    if f.IsQuad:
                        faces.extend([f.A, f.C, f.D])
                
                # Create JSON
                data = {
                    "vertices": vertices,
                    "faces": faces,
                    "vertexCount": M.Vertices.Count,
                    "faceCount": len(faces) // 3
                }
                
                # Write file
                normalized_path = os.path.normpath(file_path)
                dir_path = os.path.dirname(normalized_path)
                if dir_path and not os.path.exists(dir_path):
                    os.makedirs(dir_path)
                
                with open(normalized_path, 'w') as f:
                    json.dump(data, f, indent=2)
                
                if os.path.exists(normalized_path):
                    result = "Exported: {} vertices, {} triangles".format(
                        M.Vertices.Count, 
                        len(faces) // 3
                    )
                else:
                    result = "Failed to create file"
        except Exception as e:
            result = "Error: " + str(e)
            
except Exception as e:
    result = "Fatal error: " + str(e)

# Final safety check
if result is None:
    result = "Result was None"
