import json
import os
import Rhino

# ghpython component inputs:
# M: Mesh or List[Mesh] (list access) - Meshes/Breps/Volumes to export
# path: str (item access) - Output file path
# export: bool (item access) - Export trigger
# colorIndex: int or List[int] (list access) - Color index for each volume (maps to indexPalette)
# indexPalette: int or List[int] (list access) - Maps colorIndex values to colorPalette positions (e.g., [0, 1, 2] means index 0->palette[0], index 1->palette[1], etc.)
# colorPalette: str, tuple, list, or List of any (list access) - RGB color palette in format "R,G,B", (R,G,B), [R,G,B], or Color objects (e.g., ["255,0,0", (0,255,0), [0,0,255]])
# transparencyRate: float or List[float] (list access) - Transparency rate(s) (0.0 = fully opaque, 1.0 = fully transparent)
# gradientDirection: str or List[str] (list access) - Gradient direction(s): "Z" (vertical), "X", "Y", "radial"
# contourColor: str or List[str] (list access) - RGB color(s) for contours/edges in format "R,G,B"
# showContours: bool or List[bool] (list access) - Whether to include contours/edges (default: True)

def convert_to_mesh(geom_input):
    """Convert geometry input (Guid, Brep, etc.) to Mesh - handles multiple formats"""
    if geom_input is None:
        return None
    
    # If it's already a mesh, return it directly
    if isinstance(geom_input, Rhino.Geometry.Mesh):
        return geom_input
    
    # If it has Vertices and Faces attributes, assume it's a mesh-like object
    if hasattr(geom_input, 'Vertices') and hasattr(geom_input, 'Faces'):
        # Verify it's actually usable
        try:
            if geom_input.Vertices.Count > 0:
                return geom_input
        except:
            pass
    
    # Try to convert from other geometry types
    mesh = None
    
    # Method 1: Try ghpythonlib DeconstructObject (for Grasshopper Guids and wrapped geometry)
    if mesh is None:
        try:
            import ghpythonlib.components as ghcomp
            geom = ghcomp.DeconstructObject(geom_input)
            if geom and len(geom) > 0:
                # Check all items in the result
                for item in geom:
                    if isinstance(item, Rhino.Geometry.Mesh):
                        mesh = item
                        break
                    elif hasattr(item, 'ToMesh'):
                        try:
                            mesh = item.ToMesh()
                            if mesh and mesh.Vertices.Count > 0:
                                break
                        except:
                            pass
        except:
            pass
    
    # Method 2: Try Rhino document lookup (for Guid objects)
    if mesh is None:
        try:
            # Check if it's a Guid
            if hasattr(geom_input, 'ToString') or str(type(geom_input)).find('Guid') >= 0:
                doc = Rhino.RhinoDoc.ActiveDoc
                if doc:
                    # Try to get the Guid
                    guid = geom_input
                    if hasattr(geom_input, 'Value'):
                        guid = geom_input.Value
                    obj = doc.Objects.FindId(guid)
                    if obj and obj.Geometry:
                        if isinstance(obj.Geometry, Rhino.Geometry.Mesh):
                            mesh = obj.Geometry
                        elif hasattr(obj.Geometry, 'ToMesh'):
                            mesh = obj.Geometry.ToMesh()
        except:
            pass
    
    # Method 3: Try direct ToMesh() call (for Breps, Surfaces, etc.)
    if mesh is None and hasattr(geom_input, 'ToMesh'):
        try:
            mesh = geom_input.ToMesh()
            # Verify the mesh is valid
            if mesh and (not hasattr(mesh, 'Vertices') or mesh.Vertices.Count == 0):
                mesh = None
        except:
            pass
    
    # Method 4: Try accessing .Value property (for wrapped types)
    if mesh is None and hasattr(geom_input, 'Value'):
        try:
            value = geom_input.Value
            if isinstance(value, Rhino.Geometry.Mesh):
                mesh = value
            elif isinstance(value, Rhino.Geometry.Brep):
                # Use CreateFromBrep to ensure all faces are meshed
                mp = Rhino.Geometry.MeshingParameters.Default
                mp.SimplePlanes = False
                mp.JaggedSeams = True
                mp.RefineGrid = True
                brep_meshes = Rhino.Geometry.Mesh.CreateFromBrep(value, mp)
                if brep_meshes and len(brep_meshes) > 0:
                    mesh = Rhino.Geometry.Mesh()
                    for m in brep_meshes:
                        if m and m.Vertices.Count > 0:
                            mesh.Append(m)
                    if mesh.Vertices.Count == 0:
                        mesh = None
            elif hasattr(value, 'ToMesh'):
                mesh = value.ToMesh()
        except:
            pass
    
    return mesh

def parse_rgb_color(color_str, default=[255, 255, 255]):
    """Parse RGB color string to list of integers"""
    if not color_str or not isinstance(color_str, str):
        return default
    try:
        parts = color_str.split(',')
        if len(parts) >= 3:
            return [
                max(0, min(255, int(float(parts[0].strip())))),
                max(0, min(255, int(float(parts[1].strip())))),
                max(0, min(255, int(float(parts[2].strip()))))
            ]
    except:
        pass
    return default

def flatten_datatree(tree_input):
    """Flatten a DataTree structure to a list, preserving branch order"""
    if tree_input is None:
        return []
    
    # Check if it's a DataTree (has InnerTree or is a dict-like structure)
    if hasattr(tree_input, 'InnerTree'):
        # It's a DataTree object
        result = []
        # Sort paths to ensure consistent ordering (handle path strings like "0;0", "0;1", etc.)
        try:
            paths = sorted(tree_input.InnerTree.keys(), key=lambda x: [int(i) for i in str(x).split(';') if i.isdigit()])
        except:
            paths = sorted(tree_input.InnerTree.keys())
        
        for path in paths:
            branch = tree_input.InnerTree[path]
            if isinstance(branch, list):
                # Add all items from this branch
                for item in branch:
                    if item is not None:
                        result.append(item)
            elif branch is not None:
                result.append(branch)
        return result
    elif isinstance(tree_input, dict) and 'InnerTree' in tree_input:
        # It's a DataTree dictionary structure
        result = []
        # Sort paths to ensure consistent ordering
        try:
            paths = sorted(tree_input['InnerTree'].keys(), key=lambda x: [int(i) for i in str(x).split(';') if i.isdigit()])
        except:
            paths = sorted(tree_input['InnerTree'].keys())
        
        for path in paths:
            branch = tree_input['InnerTree'][path]
            if isinstance(branch, list):
                # Add all items from this branch
                for item in branch:
                    if item is not None:
                        result.append(item)
            elif branch is not None:
                result.append(branch)
        return result
    elif isinstance(tree_input, list):
        # Already a list - in ghpython with list access, this is what we get
        # Even if grafted, ghpython might flatten it to a list
        result = []
        for item in tree_input:
            if item is None:
                continue
            elif isinstance(item, list):
                # Recursively flatten nested lists
                flattened = flatten_datatree(item)
                result.extend(flattened)
            else:
                result.append(item)
        return result
    else:
        # Single item
        return [tree_input] if tree_input is not None else []

def normalize_to_list(value, length, default=None):
    """Normalize a value to a list of specified length, handling DataTrees"""
    if value is None:
        return [default] * length
    
    # Flatten DataTree structures first
    flattened = flatten_datatree(value)
    
    if len(flattened) == 0:
        return [default] * length
    
    # Filter out None values
    result = [v for v in flattened if v is not None]
    
    # Pad with last value if shorter
    while len(result) < length:
        result.append(result[-1] if result else default)
    
    # Trim if longer
    return result[:length]

if export and M:
    try:
        # Normalize inputs to lists for branch matching
        # Handle both single items, lists, and DataTrees (grafted branches)
        
        # Recursively flatten nested structures to get all meshes from all branches
        def recursive_flatten(obj):
            """Recursively flatten nested lists and DataTrees to a single flat list"""
            if obj is None:
                return []
            elif isinstance(obj, list):
                result = []
                for item in obj:
                    result.extend(recursive_flatten(item))
                return result
            elif hasattr(obj, 'InnerTree'):
                # It's a DataTree object - use flatten_datatree
                return flatten_datatree(obj)
            else:
                # Single item (could be a mesh, Guid, etc.)
                return [obj] if obj is not None else []
        
        # Flatten the input structure completely
        meshes_list = recursive_flatten(M)
        meshes_list = [m for m in meshes_list if m is not None]  # Filter out None values
        
        # IMPORTANT: Make sure the ghpython component is set to "List Access" (not "Item Access")
        # If set to "Item Access", the script will execute once per branch and overwrite the file each time
        # With "List Access", all branches are processed in one execution
        
        if len(meshes_list) == 0:
            result = "Error: No meshes provided. Make sure the component is set to 'List Access' mode."
        elif not path or not isinstance(path, str):
            result = "Error: Invalid file path"
        else:
            # Flatten colorIndex to match meshes_list
            color_index_list = recursive_flatten(colorIndex) if colorIndex is not None else []
            color_index_list = [int(idx) if idx is not None else 0 for idx in color_index_list]
            
            # Flatten indexPalette to create the index-to-palette mapping
            index_palette_list = recursive_flatten(indexPalette) if indexPalette is not None else []
            index_palette_list = [int(idx) if idx is not None else 0 for idx in index_palette_list]
            
            # Flatten colorPalette to create the palette lookup
            # Handle colors in various formats: strings, tuples, lists, or separate R,G,B values
            color_palette_raw = recursive_flatten(colorPalette) if colorPalette is not None else []
            color_palette_list = []
            for item in color_palette_raw:
                if item is not None:
                    if isinstance(item, str):
                        # Already a string like "255,0,0"
                        color_palette_list.append(item)
                    elif isinstance(item, (tuple, list)) and len(item) >= 3:
                        # Tuple or list like (255, 0, 0) or [255, 0, 0]
                        color_palette_list.append("{},{},{}".format(int(item[0]), int(item[1]), int(item[2])))
                    elif hasattr(item, 'R') and hasattr(item, 'G') and hasattr(item, 'B'):
                        # Color object with R, G, B properties
                        color_palette_list.append("{},{},{}".format(int(item.R), int(item.G), int(item.B)))
                    else:
                        # Try to convert to string (fallback)
                        color_palette_list.append(str(item))
            
            # If no palette provided, use default white
            if len(color_palette_list) == 0:
                color_palette_list = ["255,255,255"]
            
            # Normalize colorIndex to match meshes_list length FIRST
            while len(color_index_list) < len(meshes_list):
                if len(color_index_list) > 0:
                    color_index_list.append(color_index_list[-1])  # Repeat last index
                else:
                    color_index_list.append(0)  # Default to index 0
            color_index_list = color_index_list[:len(meshes_list)]
            
            # If no indexPalette provided, create a direct mapping (0->0, 1->1, 2->2, etc.)
            # The indexPalette should be at least as long as the maximum colorIndex value used
            if len(index_palette_list) == 0:
                # Create identity mapping based on max colorIndex found (after normalization)
                # This ensures index 0 maps to palette[0], index 1 maps to palette[1], etc.
                max_color_idx = max(color_index_list) if len(color_index_list) > 0 else 0
                # Make sure we have enough entries for all possible colorIndex values
                # Create identity mapping: [0, 1, 2, ..., max_color_idx]
                index_palette_list = list(range(max(max_color_idx + 1, 1)))
            
            # Ensure indexPalette is long enough for all colorIndex values
            max_needed_idx = max(color_index_list) if len(color_index_list) > 0 else 0
            while len(index_palette_list) <= max_needed_idx:
                # Extend with identity mapping (if index 5 is needed but indexPalette only has [0,1,2], add [3,4,5])
                index_palette_list.append(len(index_palette_list))
            
            # Map color indices through indexPalette to actual RGB colors from palette
            rgb_colors_list = []
            for color_idx in color_index_list:
                # Step 1: Map colorIndex to indexPalette position
                # color_idx is the value from colorIndex (e.g., 0, 1, 2)
                # We use it to look up in indexPalette to get the palette position
                if color_idx >= 0 and color_idx < len(index_palette_list):
                    palette_position = index_palette_list[color_idx]
                else:
                    # If colorIndex is out of range, clamp it
                    if color_idx < 0:
                        palette_position = index_palette_list[0] if len(index_palette_list) > 0 else 0
                    else:
                        # color_idx >= len(index_palette_list), use last valid mapping
                        palette_position = index_palette_list[-1] if len(index_palette_list) > 0 else 0
                
                # Step 2: Map palette position to actual color from colorPalette
                # Clamp palette_position to valid range
                palette_idx = max(0, min(palette_position, len(color_palette_list) - 1))
                rgb_colors_list.append(color_palette_list[palette_idx])
            
            # Normalize other inputs to lists
            transparency_list = normalize_to_list(transparencyRate, len(meshes_list), None)
            gradient_list = normalize_to_list(gradientDirection, len(meshes_list), None)
            contour_colors_list = normalize_to_list(contourColor, len(meshes_list), None)
            show_contours_list = normalize_to_list(showContours, len(meshes_list), True)
            
            # Validate and fix path
            path = path.strip()
            if os.path.isdir(path):
                result = "Error: Path is a directory, not a file. Please provide a full file path (e.g., 'C:\\path\\to\\file.json')"
            else:
                # Add .json extension if missing
                if not path.endswith('.json'):
                    path = path + '.json'
                
                # Check if path is just a filename (no directory)
                if not os.path.dirname(path) or os.path.dirname(path) == '':
                    path = os.path.join(os.getcwd(), path)
                
                # Process all meshes
                combined_vertices = []
                combined_faces = []
                combined_colors = []
                combined_edges = []
                mesh_metadata = []
                vertex_offset = 0
                
                processed_count = 0
                skipped_count = 0
                
                for mesh_idx, mesh_input in enumerate(meshes_list):
                    try:
                        # Convert to mesh
                        mesh = convert_to_mesh(mesh_input)
                        
                        # Validate mesh
                        if mesh is None:
                            skipped_count += 1
                            continue  # Skip None meshes
                        
                        if not hasattr(mesh, 'Vertices'):
                            skipped_count += 1
                            continue  # Skip if no Vertices attribute
                        
                        if mesh.Vertices.Count == 0:
                            skipped_count += 1
                            continue  # Skip empty meshes
                        
                        if not hasattr(mesh, 'Faces') or mesh.Faces.Count == 0:
                            skipped_count += 1
                            continue  # Skip meshes with no faces
                        
                        processed_count += 1
                        
                        # Get properties for this mesh branch (with bounds checking)
                        mesh_rgb_color = rgb_colors_list[mesh_idx] if mesh_idx < len(rgb_colors_list) else None
                        mesh_transparency = transparency_list[mesh_idx] if mesh_idx < len(transparency_list) else None
                        mesh_gradient = gradient_list[mesh_idx] if mesh_idx < len(gradient_list) else None
                        mesh_contour_color = contour_colors_list[mesh_idx] if mesh_idx < len(contour_colors_list) else None
                        mesh_show_contours = show_contours_list[mesh_idx] if mesh_idx < len(show_contours_list) else True
                        
                        # Parse RGB color
                        rgb_values = parse_rgb_color(mesh_rgb_color, [255, 255, 255])
                        r_norm = float(rgb_values[0]) / 255.0
                        g_norm = float(rgb_values[1]) / 255.0
                        b_norm = float(rgb_values[2]) / 255.0
                        
                        # Parse transparency
                        alpha_base = 1.0
                        if mesh_transparency is not None:
                            try:
                                alpha_base = max(0.0, min(1.0, float(mesh_transparency)))
                            except:
                                pass
                        
                        # Parse gradient direction
                        gradient_dir = "Z"
                        if mesh_gradient and isinstance(mesh_gradient, str):
                            gradient_dir = mesh_gradient.strip().upper()
                            if gradient_dir not in ["Z", "X", "Y", "RADIAL"]:
                                gradient_dir = "Z"
                        
                        # Calculate bounding box for gradient
                        bbox = mesh.GetBoundingBox(False)
                        min_x = float(bbox.Min.X)
                        max_x = float(bbox.Max.X)
                        min_y = float(bbox.Min.Y)
                        max_y = float(bbox.Max.Y)
                        min_z = float(bbox.Min.Z)
                        max_z = float(bbox.Max.Z)
                        
                        range_x = max_x - min_x if max_x != min_x else 1.0
                        range_y = max_y - min_y if max_y != min_y else 1.0
                        range_z = max_z - min_z if max_z != min_z else 1.0
                        
                        center_x = (min_x + max_x) / 2.0
                        center_y = (min_y + max_y) / 2.0
                        center_z = (min_z + max_z) / 2.0
                        max_radius = ((range_x**2 + range_y**2 + range_z**2)**0.5) / 2.0
                        if max_radius == 0:
                            max_radius = 1.0
                        
                        # Extract vertices and colors
                        mesh_vertex_start = vertex_offset
                        for i in range(mesh.Vertices.Count):
                            v = mesh.Vertices[i]
                            combined_vertices.extend([float(v.X), float(v.Y), float(v.Z)])
                            
                            # Calculate alpha based on gradient
                            alpha = alpha_base
                            if gradient_dir == "Z":
                                normalized_z = (float(v.Z) - min_z) / range_z
                                alpha = alpha_base + (1.0 - alpha_base) * normalized_z
                            elif gradient_dir == "X":
                                normalized_x = (float(v.X) - min_x) / range_x
                                alpha = alpha_base + (1.0 - alpha_base) * normalized_x
                            elif gradient_dir == "Y":
                                normalized_y = (float(v.Y) - min_y) / range_y
                                alpha = alpha_base + (1.0 - alpha_base) * normalized_y
                            elif gradient_dir == "RADIAL":
                                dx = float(v.X) - center_x
                                dy = float(v.Y) - center_y
                                dz = float(v.Z) - center_z
                                distance = (dx*dx + dy*dy + dz*dz)**0.5
                                normalized_dist = min(1.0, distance / max_radius)
                                alpha = alpha_base + (1.0 - alpha_base) * normalized_dist
                            
                            alpha = max(0.0, min(1.0, alpha))
                            combined_colors.extend([r_norm, g_norm, b_norm, alpha])
                        
                        # Extract faces with vertex offset
                        mesh_face_start = len(combined_faces) // 3
                        for i in range(mesh.Faces.Count):
                            f = mesh.Faces[i]
                            combined_faces.extend([int(f.A) + vertex_offset, int(f.B) + vertex_offset, int(f.C) + vertex_offset])
                            if f.IsQuad:
                                combined_faces.extend([int(f.A) + vertex_offset, int(f.C) + vertex_offset, int(f.D) + vertex_offset])
                        
                        # Extract edges with vertex offset (common processing for all meshes)
                        mesh_edges = []
                        # Use the first non-None contour color for all meshes, or default black
                        if mesh_idx == 0:
                            # Determine common contour color from first mesh or use default
                            common_contour_color = parse_rgb_color(mesh_contour_color, [0, 0, 0])
                        else:
                            # Use the same contour color for all meshes
                            common_contour_color = parse_rgb_color(contour_colors_list[0] if len(contour_colors_list) > 0 else None, [0, 0, 0])
                        
                        # Process edges if any mesh wants contours
                        any_show_contours = any(show_contours_list) if len(show_contours_list) > 0 else True
                        if any_show_contours:
                            edge_set = set()
                            for i in range(mesh.Faces.Count):
                                f = mesh.Faces[i]
                                edge_set.add(tuple(sorted([int(f.A) + vertex_offset, int(f.B) + vertex_offset])))
                                edge_set.add(tuple(sorted([int(f.B) + vertex_offset, int(f.C) + vertex_offset])))
                                edge_set.add(tuple(sorted([int(f.C) + vertex_offset, int(f.A) + vertex_offset])))
                                if f.IsQuad:
                                    edge_set.add(tuple(sorted([int(f.A) + vertex_offset, int(f.C) + vertex_offset])))
                                    edge_set.add(tuple(sorted([int(f.C) + vertex_offset, int(f.D) + vertex_offset])))
                                    edge_set.add(tuple(sorted([int(f.D) + vertex_offset, int(f.A) + vertex_offset])))
                            
                            for edge_pair in edge_set:
                                mesh_edges.extend([int(edge_pair[0]), int(edge_pair[1])])
                                combined_edges.extend([int(edge_pair[0]), int(edge_pair[1])])
                        
                        # Store mesh metadata
                        mesh_metadata.append({
                            "meshIndex": mesh_idx,
                            "vertexStart": mesh_vertex_start,
                            "vertexCount": int(mesh.Vertices.Count),
                            "faceStart": mesh_face_start,
                            "faceCount": int(len(combined_faces) // 3 - mesh_face_start),
                            "edgeCount": int(len(mesh_edges) // 2),
                            "hasEdges": len(mesh_edges) > 0,
                            "colorInfo": {
                                "rgb": rgb_values,
                                "transparencyRate": alpha_base,
                                "gradientDirection": gradient_dir
                            }
                        })
                        
                        vertex_offset += mesh.Vertices.Count
                        
                    except Exception as mesh_error:
                        # Skip this mesh if there's an error, continue with others
                        continue
                
                # Build final JSON structure
                if len(combined_vertices) == 0:
                    result = "Error: No valid meshes to export (processed: {}, skipped: {})".format(processed_count, skipped_count)
                else:
                    data = {
                        "meshes": mesh_metadata,
                        "vertices": combined_vertices,
                        "faces": combined_faces,
                        "colors": combined_colors,
                        "vertexCount": len(combined_vertices) // 3,
                        "faceCount": len(combined_faces) // 3,
                        "meshCount": len(mesh_metadata),
                        "hasColors": True,
                        "colorFormat": "RGBA"
                    }
                    
                    # Add edges with common contour color for all meshes
                    if len(combined_edges) > 0:
                        data["edges"] = combined_edges
                        data["edgeCount"] = len(combined_edges) // 2
                        data["hasEdges"] = True
                        # Use first mesh's contour color or default black for all edges
                        if len(contour_colors_list) > 0 and contour_colors_list[0]:
                            data["contourColor"] = parse_rgb_color(contour_colors_list[0], [0, 0, 0])
                        else:
                            data["contourColor"] = [0, 0, 0]  # Default black
                    else:
                        data["hasEdges"] = False
                    
                    # Ensure directory exists
                    dir_path = os.path.dirname(path)
                    if dir_path and not os.path.exists(dir_path):
                        try:
                            os.makedirs(dir_path)
                        except Exception as e:
                            result = "Error: Cannot create directory '{}': {}".format(dir_path, str(e))
                            path = None
                    
                    # Write to file
                    if path:
                        try:
                            with open(path, 'w') as f:
                                json.dump(data, f, indent=2)
                            
                            edge_info = ""
                            if len(combined_edges) > 0:
                                edge_info = ", {} edges".format(len(combined_edges) // 2)
                            
                            result = "Exported {} meshes (processed: {}, skipped: {}): {} vertices, {} triangles{} to:\n{}".format(
                                len(mesh_metadata),
                                processed_count,
                                skipped_count,
                                len(combined_vertices) // 3,
                                len(combined_faces) // 3,
                                edge_info,
                                path
                            )
                        except Exception as e:
                            result = "Error writing file '{}': {}".format(path, str(e))
    except Exception as e:
        result = "Error: {}".format(str(e))
else:
    result = "Waiting..."
