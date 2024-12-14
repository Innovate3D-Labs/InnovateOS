import yaml
import sys
from pathlib import Path
from typing import Dict, Any, List

def load_yaml(file_path: Path) -> dict:
    """Load YAML file"""
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)

def compare_schemas(old_schema: Dict, new_schema: Dict, path: str = "") -> List[str]:
    """Compare two OpenAPI schemas and detect breaking changes"""
    breaking_changes = []
    
    # Check for removed endpoints
    old_paths = set(old_schema.get('paths', {}).keys())
    new_paths = set(new_schema.get('paths', {}).keys())
    removed_paths = old_paths - new_paths
    if removed_paths:
        breaking_changes.extend([f"Removed endpoint: {path}" for path in removed_paths])
    
    # Check for changes in existing endpoints
    for path in old_paths & new_paths:
        old_methods = old_schema['paths'][path]
        new_methods = new_schema['paths'][path]
        
        # Check for removed methods
        old_operations = set(old_methods.keys())
        new_operations = set(new_methods.keys())
        removed_operations = old_operations - new_operations
        if removed_operations:
            breaking_changes.extend([
                f"Removed method {method} for endpoint {path}"
                for method in removed_operations
            ])
        
        # Check for changes in parameters
        for method in old_operations & new_operations:
            old_params = {
                p['name']: p
                for p in old_methods[method].get('parameters', [])
            }
            new_params = {
                p['name']: p
                for p in new_methods[method].get('parameters', [])
            }
            
            # Check for removed required parameters
            for param_name, param in old_params.items():
                if (param.get('required', False) and 
                    param_name not in new_params):
                    breaking_changes.append(
                        f"Removed required parameter {param_name} "
                        f"from {method} {path}"
                    )
            
            # Check for changed parameter types
            for param_name in old_params.keys() & new_params.keys():
                old_type = old_params[param_name].get('schema', {}).get('type')
                new_type = new_params[param_name].get('schema', {}).get('type')
                if old_type != new_type:
                    breaking_changes.append(
                        f"Changed parameter type for {param_name} in "
                        f"{method} {path} from {old_type} to {new_type}"
                    )
    
    return breaking_changes

def main():
    docs_dir = Path("docs")
    
    # Load current spec
    current_spec = load_yaml(docs_dir / "openapi.yaml")
    
    # Load previous spec from main branch
    previous_spec_path = docs_dir / "openapi.yaml.old"
    if not previous_spec_path.exists():
        print("No previous API spec found. Skipping breaking change detection.")
        return 0
    
    previous_spec = load_yaml(previous_spec_path)
    
    # Compare specs
    breaking_changes = compare_schemas(previous_spec, current_spec)
    
    if breaking_changes:
        print("Breaking changes detected:")
        for change in breaking_changes:
            print(f"- {change}")
        return 1
    
    print("No breaking changes detected")
    return 0

if __name__ == "__main__":
    sys.exit(main())
