"""
Schema postprocessing hooks for drf-spectacular.
Handles custom schema modifications and enum documentation.
"""
from typing import Dict, Any


def postprocess_schema_enums(result: Dict[str, Any], generator, request, public: bool) -> Dict[str, Any]:
    """
    Postprocess schema to improve enum documentation in Swagger UI.
    
    Args:
        result: The generated OpenAPI schema
        generator: The schema generator instance
        request: The request object
        public: Whether this is a public schema
        
    Returns:
        Modified schema with improved enum documentation
    """
    if result.get('components', {}).get('schemas'):
        for schema_name, schema_def in result['components']['schemas'].items():
            if 'properties' in schema_def:
                for prop_name, prop_def in schema_def['properties'].items():
                    # Add descriptions to enum fields
                    if 'enum' in prop_def and 'description' not in prop_def:
                        prop_def['description'] = f'Allowed values: {", ".join(str(v) for v in prop_def["enum"])}'
    
    return result
