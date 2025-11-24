"""
IFC Processor - Extract alignment information from IFC files
"""

import ifcopenshell


class IFCProcessor:
    """Process IFC files to extract alignment information."""
    
    def __init__(self, filepath):
        """Initialize with IFC file path."""
        self.filepath = filepath
        self.ifc_file = ifcopenshell.open(filepath)
    
    def get_alignments(self):
        """Get all alignments from the IFC file."""
        alignments = []
        
        for alignment in self.ifc_file.by_type('IfcAlignment'):
            # Get basic info
            alignment_info = {
                'id': alignment.id(),
                'global_id': alignment.GlobalId,
                'name': alignment.Name if alignment.Name else f"Alignment {alignment.id()}",
                'description': alignment.Description if alignment.Description else "",
                'type': alignment.PredefinedType if hasattr(alignment, 'PredefinedType') else "USERDEFINED"
            }
            
            # Check if it has both base and gradient curves
            has_base = False
            has_gradient = False
            
            if alignment.Representation:
                for rep in alignment.Representation.Representations:
                    if rep.RepresentationType == 'Curve2D':
                        has_base = True
                    elif rep.RepresentationType == 'Curve3D':
                        has_gradient = True
            
            alignment_info['has_base_curve'] = has_base
            alignment_info['has_gradient_curve'] = has_gradient
            alignment_info['is_complete'] = has_base and has_gradient
            
            alignments.append(alignment_info)
        
        return alignments
    
    def get_alignment_by_global_id(self, global_id):
        """Get a specific alignment by its GlobalId."""
        for alignment in self.ifc_file.by_type('IfcAlignment'):
            if alignment.GlobalId == global_id:
                return alignment
        return None
    
    def get_alignment_by_id(self, alignment_id):
        """Get a specific alignment by its ID."""
        try:
            return self.ifc_file.by_id(int(alignment_id))
        except:
            return None

