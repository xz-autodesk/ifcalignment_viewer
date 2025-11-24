"""
Alignment Visualizer - Create interactive visualizations for IFC alignments
"""

import ifcopenshell
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import os


class AlignmentVisualizer:
    """Create interactive visualizations for IFC alignments."""
    
    def __init__(self, filepath):
        """Initialize with IFC file path."""
        self.filepath = filepath
        self.ifc_file = ifcopenshell.open(filepath)
    
    def create_visualization(self, alignment_id, output_folder):
        """Create complete visualization for an alignment."""
        # Get the alignment
        alignment = self.ifc_file.by_id(int(alignment_id))
        
        if not alignment or not alignment.is_a('IfcAlignment'):
            raise ValueError(f"Alignment {alignment_id} not found or invalid")
        
        # Get representations
        base_rep = None
        gradient_rep = None
        
        for rep in alignment.Representation.Representations:
            if rep.RepresentationType == 'Curve2D':
                base_rep = rep
            elif rep.RepresentationType == 'Curve3D':
                gradient_rep = rep
        
        if not base_rep or not gradient_rep:
            raise ValueError("Alignment missing base or gradient curve")
        
        base_curve = base_rep.Items[0]
        gradient_curve = gradient_rep.Items[0]
        
        # Evaluate curves
        base_points, base_distances = self._evaluate_base_curve(base_curve)
        vert_distances, elevations = self._evaluate_vertical_profile(gradient_curve, base_distances[-1] if len(base_distances) > 0 else 1000)
        
        # Create 3D curve
        base_elevations = np.interp(base_distances, vert_distances, elevations)
        
        # Create analysis tables
        base_df, vert_df, summary_df = self._create_analysis_tables(alignment, base_curve, gradient_curve)
        
        # Create visualization
        fig = self._create_plotly_figure(
            base_points, base_distances, base_curve,
            vert_distances, elevations, gradient_curve,
            base_elevations,
            base_df, vert_df, summary_df,
            alignment
        )
        
        # Save HTML
        html_filename = f"alignment_{alignment_id}_{alignment.Name.replace(' ', '_') if alignment.Name else 'unnamed'}.html"
        html_path = os.path.join(output_folder, html_filename)
        fig.write_html(html_path)
        
        return {
            'html_filename': html_filename,
            'html_path': html_path,
            'summary': summary_df.to_dict('records'),
            'base_segments': base_df.to_dict('records'),
            'vertical_segments': vert_df.to_dict('records')
        }
    
    def _evaluate_line_segment(self, placement, parent_curve, start, length, num_points=50):
        """Evaluate points along a line segment."""
        loc = placement.Location.Coordinates
        if hasattr(placement, 'RefDirection') and placement.RefDirection:
            ref_dir = placement.RefDirection.DirectionRatios
        else:
            ref_dir = (1.0, 0.0)
        
        t_values = np.linspace(0, length, num_points)
        local_points = np.column_stack([t_values, np.zeros_like(t_values)])
        
        cos_angle = ref_dir[0]
        sin_angle = ref_dir[1]
        
        global_points = []
        for pt in local_points:
            x_global = loc[0] + pt[0] * cos_angle - pt[1] * sin_angle
            y_global = loc[1] + pt[0] * sin_angle + pt[1] * cos_angle
            global_points.append([x_global, y_global])
        
        return np.array(global_points)
    
    def _evaluate_circle_segment(self, placement, parent_curve, start, length, num_points=50):
        """Evaluate points along a circular arc segment."""
        loc = placement.Location.Coordinates
        if hasattr(placement, 'RefDirection') and placement.RefDirection:
            ref_dir = placement.RefDirection.DirectionRatios
        else:
            ref_dir = (1.0, 0.0)
        
        radius = parent_curve.Radius
        total_angle = length / radius
        angles = np.linspace(0, total_angle, num_points)
        
        if length > 0:
            local_points = np.column_stack([radius * np.sin(angles), radius * (1 - np.cos(angles))])
        else:
            angles = np.linspace(0, -length / radius, num_points)
            local_points = np.column_stack([radius * np.sin(angles), -radius * (1 - np.cos(angles))])
        
        cos_angle = ref_dir[0]
        sin_angle = ref_dir[1]
        
        global_points = []
        for pt in local_points:
            x_global = loc[0] + pt[0] * cos_angle - pt[1] * sin_angle
            y_global = loc[1] + pt[0] * sin_angle + pt[1] * cos_angle
            global_points.append([x_global, y_global])
        
        return np.array(global_points)
    
    def _evaluate_base_curve(self, composite_curve):
        """Evaluate all points along the base curve."""
        all_points = []
        distances = []
        current_dist = 0.0
        
        for segment in composite_curve.Segments:
            placement = segment.Placement
            parent_curve = segment.ParentCurve
            start = segment.SegmentStart.wrappedValue
            length = segment.SegmentLength.wrappedValue
            
            if parent_curve.is_a('IfcLine'):
                points = self._evaluate_line_segment(placement, parent_curve, start, length)
            elif parent_curve.is_a('IfcCircle'):
                points = self._evaluate_circle_segment(placement, parent_curve, start, length)
            else:
                continue
            
            if len(all_points) > 0:
                points = points[1:]
            
            for pt in points:
                all_points.append(pt)
                if len(all_points) > 1:
                    dx = pt[0] - all_points[-2][0]
                    dy = pt[1] - all_points[-2][1]
                    current_dist += np.sqrt(dx**2 + dy**2)
                distances.append(current_dist)
        
        return np.array(all_points), np.array(distances)
    
    def _evaluate_vertical_profile(self, gradient_curve, max_distance):
        """Evaluate elevation along the gradient curve."""
        distances = []
        elevations = []
        
        for segment in gradient_curve.Segments:
            placement = segment.Placement
            parent_curve = segment.ParentCurve
            start_param = segment.SegmentStart.wrappedValue
            length = segment.SegmentLength.wrappedValue
            
            if length == 0:
                continue
            
            seg_start_dist = placement.Location.Coordinates[0]
            seg_start_elev = placement.Location.Coordinates[1]
            
            if parent_curve.is_a('IfcLine'):
                num_points = 50
                t_values = np.linspace(0, length, num_points)
                
                for t in t_values:
                    distances.append(seg_start_dist + t)
                    elevations.append(seg_start_elev + t * placement.RefDirection.DirectionRatios[1] / placement.RefDirection.DirectionRatios[0])
            
            elif parent_curve.is_a('IfcPolynomialCurve'):
                coeffs = parent_curve.CoefficientsY
                c0 = coeffs[0]
                c1 = coeffs[1] if len(coeffs) > 1 else 0
                c2 = coeffs[2] if len(coeffs) > 2 else 0
                
                num_points = 100
                u_values = np.linspace(0, length, num_points)
                
                is_civil3d = (abs(c0) > 1.0 or abs(c1) > 0.001)
                
                for u in u_values:
                    if is_civil3d:
                        distances.append(seg_start_dist + u)
                        elevations.append(c0 + c1 * u + c2 * u * u)
                    else:
                        distances.append(seg_start_dist + u)
                        elevations.append(seg_start_elev + c0 + c1 * u + c2 * u * u)
        
        return np.array(distances), np.array(elevations)
    
    def _create_analysis_tables(self, alignment, base_curve, gradient_curve):
        """Create analysis tables."""
        # Base Curve Table
        base_data = []
        for idx, segment in enumerate(base_curve.Segments):
            parent = segment.ParentCurve
            curve_type = parent.is_a().replace('Ifc', '')
            length = segment.SegmentLength.wrappedValue
            
            extra = ""
            if parent.is_a('IfcCircle'):
                radius = parent.Radius
                extra = f"R={radius:.1f}m"
            
            base_data.append({
                'Seg': idx,
                'Type': curve_type,
                'Length': f"{length:.2f}",
                'Details': extra
            })
        
        base_df = pd.DataFrame(base_data)
        
        # Vertical Profile Table
        vert_data = []
        cumulative_dist = 0.0
        
        for idx, segment in enumerate(gradient_curve.Segments):
            parent = segment.ParentCurve
            curve_type = parent.is_a().replace('Ifc', '')
            length = segment.SegmentLength.wrappedValue
            start_elev = segment.Placement.Location.Coordinates[1]
            
            extra = ""
            if parent.is_a('IfcPolynomialCurve'):
                coeffs = parent.CoefficientsY
                c0 = coeffs[0]
                c1 = coeffs[1] if len(coeffs) > 1 else 0
                c2 = coeffs[2] if len(coeffs) > 2 else 0
                
                is_civil3d = (abs(c0) > 1.0 or abs(c1) > 0.001)
                pattern = "Civil3D" if is_civil3d else "IMX"
                
                start_grad = c1 * 100
                end_grad = (c1 + 2 * c2 * length) * 100
                
                extra = f"{pattern}, {start_grad:.2f}%→{end_grad:.2f}%"
            elif parent.is_a('IfcLine'):
                if hasattr(segment.Placement, 'RefDirection') and segment.Placement.RefDirection:
                    ref = segment.Placement.RefDirection.DirectionRatios
                    grad = (ref[1] / ref[0]) * 100 if ref[0] != 0 else 0
                    extra = f"{grad:.2f}%"
            
            vert_data.append({
                'Seg': idx,
                'Type': curve_type,
                'Distance': f"{cumulative_dist:.2f}",
                'Length': f"{length:.2f}",
                'Elevation': f"{start_elev:.2f}",
                'Details': extra
            })
            
            cumulative_dist += length
        
        vert_df = pd.DataFrame(vert_data)
        
        # Summary Table
        polynomial_count = sum(1 for s in gradient_curve.Segments if s.ParentCurve.is_a('IfcPolynomialCurve'))
        
        summary_data = {
            'Property': [
                'Name',
                'STEP ID',
                'Global ID',
                'Type',
                'Base Segments',
                'Vertical Segments',
                'Polynomial Curves',
                'Total Length',
                'Start Elevation',
                'Pattern Detected'
            ],
            'Value': [
                alignment.Name if alignment.Name else f"#{alignment.id()}",
                f"#{alignment.id()}",
                alignment.GlobalId if hasattr(alignment, 'GlobalId') else "N/A",
                alignment.PredefinedType if hasattr(alignment, 'PredefinedType') else "N/A",
                str(len(base_curve.Segments)),
                str(len(gradient_curve.Segments)),
                str(polynomial_count),
                f"{cumulative_dist:.2f} m",
                vert_df['Elevation'].iloc[0] if len(vert_df) > 0 else 'N/A',
                '🔴 Civil3D' if polynomial_count > 0 else '🟢 IMX/None'
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        
        return base_df, vert_df, summary_df
    
    def _create_plotly_figure(self, base_points, base_distances, base_curve,
                              vert_distances, elevations, gradient_curve,
                              base_elevations, base_df, vert_df, summary_df, alignment):
        """Create the Plotly figure."""
        fig = make_subplots(
            rows=3, cols=2,
            row_heights=[0.4, 0.3, 0.3],
            column_widths=[0.7, 0.3],
            specs=[
                [{'type': 'scatter'}, {'type': 'table'}],
                [{'type': 'scatter'}, {'type': 'table'}],
                [{'type': 'scatter3d'}, {'type': 'table'}]
            ],
            subplot_titles=(
                '🗺️ Base Curve (Plan View)',
                '📊 Summary',
                '📈 Vertical Profile',
                '📋 Base Segments',
                '🌐 3D Alignment',
                '📋 Vertical Segments'
            ),
            vertical_spacing=0.12,
            horizontal_spacing=0.1
        )
        
        # 1. Base Curve
        fig.add_trace(
            go.Scatter(
                x=base_points[:, 0],
                y=base_points[:, 1],
                mode='lines',
                name='Base Curve',
                line=dict(color='blue', width=2),
                hovertemplate='X: %{x:.2f}m<br>Y: %{y:.2f}m<extra></extra>'
            ),
            row=1, col=1
        )
        
        # 2. Vertical Profile
        fig.add_trace(
            go.Scatter(
                x=vert_distances,
                y=elevations,
                mode='lines',
                name='Elevation',
                line=dict(color='green', width=2),
                hovertemplate='Distance: %{x:.2f}m<br>Elevation: %{y:.2f}m<extra></extra>'
            ),
            row=2, col=1
        )
        
        # Highlight polynomial sections
        for segment in gradient_curve.Segments:
            if segment.ParentCurve.is_a('IfcPolynomialCurve'):
                start_dist = segment.Placement.Location.Coordinates[0]
                length = segment.SegmentLength.wrappedValue
                end_dist = start_dist + length
                
                mask = (vert_distances >= start_dist) & (vert_distances <= end_dist)
                fig.add_trace(
                    go.Scatter(
                        x=vert_distances[mask],
                        y=elevations[mask],
                        mode='lines',
                        name='Polynomial',
                        line=dict(color='red', width=3),
                        showlegend=False
                    ),
                    row=2, col=1
                )
        
        # 3. 3D Curve
        fig.add_trace(
            go.Scatter3d(
                x=base_points[:, 0],
                y=base_points[:, 1],
                z=base_elevations,
                mode='lines',
                name='3D Alignment',
                line=dict(color=base_elevations, colorscale='Viridis', width=4,
                         colorbar=dict(title="Elevation (m)", x=1.15, len=0.3, y=0.15)),
                hovertemplate='X: %{x:.2f}m<br>Y: %{y:.2f}m<br>Z: %{z:.2f}m<extra></extra>'
            ),
            row=3, col=1
        )
        
        # 4. Summary Table
        fig.add_trace(
            go.Table(
                header=dict(values=['<b>Property</b>', '<b>Value</b>'],
                           fill_color='paleturquoise', align='left',
                           font=dict(size=11)),
                cells=dict(values=[summary_df['Property'], summary_df['Value']],
                          fill_color='lavender', align='left',
                          font=dict(size=10))
            ),
            row=1, col=2
        )
        
        # 5. Base Segments Table
        fig.add_trace(
            go.Table(
                header=dict(values=list(base_df.columns),
                           fill_color='lightblue', align='left',
                           font=dict(size=10)),
                cells=dict(values=[base_df[col] for col in base_df.columns],
                          fill_color='white', align='left',
                          font=dict(size=9), height=20)
            ),
            row=2, col=2
        )
        
        # 6. Vertical Segments Table
        fig.add_trace(
            go.Table(
                header=dict(values=list(vert_df.columns),
                           fill_color='lightgreen', align='left',
                           font=dict(size=9)),
                cells=dict(values=[vert_df[col] for col in vert_df.columns],
                          fill_color='white', align='left',
                          font=dict(size=8), height=20)
            ),
            row=3, col=2
        )
        
        # Update layout
        fig.update_xaxes(title_text="X (m)", row=1, col=1)
        fig.update_yaxes(title_text="Y (m)", row=1, col=1)
        fig.update_xaxes(title_text="Distance Along (m)", row=2, col=1)
        fig.update_yaxes(title_text="Elevation (m)", row=2, col=1)
        
        alignment_name = alignment.Name if alignment.Name else f"Alignment #{alignment.id()}"
        step_id = f"#{alignment.id()}"
        global_id = alignment.GlobalId if hasattr(alignment, 'GlobalId') else "N/A"
        
        fig.update_layout(
            title=dict(
                text=f"<b style='font-size: 18px;'>{alignment_name}</b><br><span style='font-size: 14px;'>Interactive 3D Alignment Analysis</span><br><span style='font-size: 11px; color: #666;'>STEP ID: {step_id} | Global ID: {global_id}</span>",
                x=0.5,
                xanchor='center',
                y=0.98,
                yanchor='top',
                font=dict(size=16)
            ),
            height=1400,
            margin=dict(t=120),
            showlegend=True,
            legend=dict(x=0.02, y=0.98),
            scene=dict(
                xaxis_title="X (m)",
                yaxis_title="Y (m)",
                zaxis_title="Elevation (m)",
                aspectmode='data'
            ),
            hovermode='closest'
        )
        
        return fig

