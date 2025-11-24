# IFC Alignment Viewer 🏗️

A modern web application for visualizing and analyzing IFC alignment data with interactive 3D visualizations.

## 📋 Features

- **📂 File Upload**: Drag & drop or browse to upload IFC files
- **🎯 Alignment Selection**: View all alignments with their details (GlobalId, Name, Type)
- **📊 Interactive Visualizations**:
  - 🗺️ Base Curve (Horizontal Alignment) - Plan View
  - 📈 Vertical Profile (Elevation vs Distance)
  - 🌐 3D Alignment Curve with color-coded elevation
- **📋 Analysis Tables**:
  - Summary statistics
  - Base curve segments breakdown
  - Vertical profile segments breakdown
- **🔍 Pattern Detection**: Automatically identifies Civil 3D vs IMX patterns
- **✨ Modern UI**: Beautiful gradient design with responsive layout

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip or uv package manager

### Installation

1. **Navigate to the project directory:**
   ```bash
   cd alignment_viewer
   ```

2. **Install dependencies:**
   
   Using pip:
   ```bash
   pip install -r requirements.txt
   ```
   
   Or using uv:
   ```bash
   uv pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```

4. **Open your browser:**
   ```
   http://localhost:5000
   ```

---

## 📁 Project Structure

```
alignment_viewer/
├── app.py                 # Flask application (main entry point)
├── requirements.txt       # Python dependencies
├── README.md             # This file
│
├── templates/            # HTML templates
│   └── index.html        # Main web interface
│
├── static/               # Static files (CSS, JS, images)
│
├── utils/                # Utility modules
│   ├── ifc_processor.py  # IFC file processing
│   └── visualizer.py     # Visualization generation
│
├── uploads/              # Uploaded IFC files (auto-created)
│
└── output/               # Generated visualizations (auto-created)
```

---

## 🎯 How to Use

### 1. Upload IFC File

- Click the upload zone or drag & drop your IFC file
- Supported format: `.ifc`
- Maximum file size: 100MB

### 2. Select Alignment

- Browse the list of available alignments
- Each card shows:
  - Alignment name
  - ID and GlobalId
  - Type (HORIZONTAL, VERTICAL, etc.)
  - Status (✓ Complete / ⚠ Incomplete)
- Click on a **complete** alignment to visualize it

### 3. Explore Visualization

The visualization includes 6 interactive panels:

**Left Side (Visualizations):**
- **Top**: Plan view of base curve (horizontal alignment)
- **Middle**: Vertical profile with polynomial curves highlighted in red
- **Bottom**: 3D alignment curve with color-coded elevation

**Right Side (Analysis Tables):**
- **Top**: Summary statistics
- **Middle**: Base curve segments (lines, circles, etc.)
- **Bottom**: Vertical profile segments with pattern detection

**Interactive Features:**
- **Hover**: See exact coordinates and values
- **Zoom**: Scroll to zoom in/out
- **Pan**: Click and drag to pan
- **Rotate 3D**: Click and drag on 3D plot
- **Reset**: Double-click to reset view

---

## 🔧 API Endpoints

### `GET /`
Main page with upload interface.

### `POST /upload`
Upload an IFC file.

**Request:**
- Form data with `file` parameter

**Response:**
```json
{
  "success": true,
  "filename": "example.ifc",
  "alignments": [
    {
      "id": 9091,
      "global_id": "0NgtFk1uH6Ixc3NIKH1GHa",
      "name": "West-Zuid - VERT west zuid",
      "type": "USERDEFINED",
      "has_base_curve": true,
      "has_gradient_curve": true,
      "is_complete": true
    }
  ]
}
```

### `GET /visualize/<alignment_id>`
Generate visualization for a specific alignment.

**Response:**
```json
{
  "success": true,
  "html_path": "alignment_9091_West-Zuid.html",
  "summary": [...],
  "base_segments": [...],
  "vertical_segments": [...]
}
```

### `GET /output/<filename>`
Serve generated visualization files.

### `GET /get_visualization/<filename>`
Get visualization HTML content.

---

## 🎨 Customization

### Modify Visualization

Edit `utils/visualizer.py` to customize:
- Color schemes
- Point density
- Table formatting
- Layout configuration

### Modify UI

Edit `templates/index.html` to customize:
- Styling (CSS in `<style>` section)
- Layout
- Interactive behavior (JavaScript)

### Add Features

The modular structure makes it easy to extend:
- Add new analysis metrics in `utils/ifc_processor.py`
- Add new visualization types in `utils/visualizer.py`
- Add new routes in `app.py`

---

## 📊 Supported IFC Elements

### Alignments
- ✅ `IfcAlignment`
- ✅ `IfcCompositeCurve` (base curve)
- ✅ `IfcGradientCurve` (vertical curve)

### Horizontal Segments
- ✅ `IfcLine` (straight sections)
- ✅ `IfcCircle` (circular arcs)
- ✅ `IfcClothoid` (transition curves)

### Vertical Segments
- ✅ `IfcLine` (constant gradient)
- ✅ `IfcPolynomialCurve` (parabolic transitions)
- ✅ `IfcCircle` (circular vertical curves)

### Pattern Detection
- ✅ Civil 3D pattern (redundant placement)
- ✅ IMX pattern (essential placement)

---

## 🔍 Pattern Detection

The application automatically detects the polynomial curve pattern:

### Civil 3D Pattern 🔴
- Polynomial coefficients include elevation and gradient
- Segment placement is redundant
- Coefficients: `|c₀| > 1.0` or `|c₁| > 0.001`
- **Example**: `c₀=40.744, c₁=0.009104`

### IMX Pattern 🟢
- Pure quadratic polynomial (only c₂ term)
- Segment placement is essential
- Coefficients: `c₀≈0, c₁≈0, c₂≠0`
- **Example**: `c₀=0, c₁=0, c₂=0.0001`

---

## 🐛 Troubleshooting

### Upload Fails
- Check file size (< 100MB)
- Ensure file is valid IFC format
- Check console for errors

### No Alignments Found
- File may not contain `IfcAlignment` entities
- Use IFC viewer to verify file contents

### Visualization Error
- Alignment must have both base and gradient curves
- Check browser console for JavaScript errors
- Check Flask console for Python errors

### Port Already in Use
Change port in `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Change port here
```

---

## 📝 License

This project is part of the Autodesk Test Framework (ATF) alignment analysis tools.

---

## 🤝 Contributing

To contribute:
1. Follow ATF coding standards (see `.code_review_guidelines.md`)
2. Test with various IFC files
3. Update documentation for new features
4. Ensure all visualizations work correctly

---

## 📚 Related Files

This application is part of a larger toolkit:

- `../analyze_alignment.py` - Command-line alignment analyzer
- `../visualize_m25_interactive.py` - Stand-alone M25 visualizer
- `../analyze_m25_gradient.py` - M25 gradient analysis script
- `../TRANSFORMATION_ANALYSIS_SUMMARY.md` - Technical documentation

---

## 🎉 Example Files

Test the application with these sample files:

- `AJ - M25 Intersection - WITH BRIDGES.ifc` - Complex road alignment
- `ParabolicProfile.ifc` - Multiple polynomial curves
- `concrete_bridge_from_imx_ExportAll.ifc` - IMX pattern
- `Corridor_Export_all_Check_Relationship_Priority.ifc` - IMX pattern

---

## ✅ Status

| Feature | Status |
|---------|--------|
| File Upload | ✅ Complete |
| Alignment List | ✅ Complete |
| Interactive Selection | ✅ Complete |
| 3D Visualization | ✅ Complete |
| Analysis Tables | ✅ Complete |
| Pattern Detection | ✅ Complete |
| Responsive Design | ✅ Complete |
| Error Handling | ✅ Complete |

---

**Built with:** Flask, Plotly, IfcOpenShell, Pandas, NumPy  
**Version:** 1.0.0  
**Date:** November 2025

