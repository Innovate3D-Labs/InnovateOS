import yaml
import semver
from pathlib import Path
from datetime import datetime

def load_yaml(file_path: Path) -> dict:
    """Load YAML file"""
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)

def save_yaml(data: dict, file_path: Path) -> None:
    """Save YAML file"""
    with open(file_path, 'w') as f:
        yaml.dump(data, f, sort_keys=False)

def update_version(current_version: str, breaking_changes: bool = False) -> str:
    """Update semantic version based on changes"""
    version = semver.VersionInfo.parse(current_version)
    
    if breaking_changes:
        # Major version bump for breaking changes
        return str(version.bump_major())
    else:
        # Minor version bump for non-breaking changes
        return str(version.bump_minor())

def main():
    docs_dir = Path("docs")
    spec_file = docs_dir / "openapi.yaml"
    
    # Load current spec
    spec = load_yaml(spec_file)
    
    # Get current version
    current_version = spec['info']['version']
    
    # Check for breaking changes
    breaking_changes_file = docs_dir / "breaking_changes.txt"
    breaking_changes = breaking_changes_file.exists()
    
    # Update version
    new_version = update_version(current_version, breaking_changes)
    spec['info']['version'] = new_version
    
    # Add version update timestamp
    if 'x-versions' not in spec['info']:
        spec['info']['x-versions'] = []
    
    spec['info']['x-versions'].append({
        'version': new_version,
        'date': datetime.now().isoformat(),
        'breaking_changes': breaking_changes
    })
    
    # Save updated spec
    save_yaml(spec, spec_file)
    
    print(f"Updated API version from {current_version} to {new_version}")
    
    # Clean up
    if breaking_changes_file.exists():
        breaking_changes_file.unlink()

if __name__ == "__main__":
    main()
