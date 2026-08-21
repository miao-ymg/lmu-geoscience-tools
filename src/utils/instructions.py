import yaml

def get_instructions_data(yaml_path: str, optional_columns: list = None) -> dict:
    """Reads column aliases YAML and returns a dictionary for the instructions UI."""
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            
        if not data:
            return {}
            
        bullets = []
        for key, aliases in data.items():
            # If the key is all uppercase, title-case it. Otherwise, keep original casing (e.g., Ol, Opx, SiO2).
            key_name = key.title() if isinstance(key, str) and key.isupper() else key
            
            # Format optional columns string
            opt_str = ""
            if optional_columns and key in optional_columns:
                opt_str = " (Optional)"
                
            if isinstance(aliases, list):
                # Keep original casing from YAML, unless the alias is ALL UPPERCASE, 
                # in which case we title-case it (to prevent QUARTZ, FOID from screaming, 
                # while preserving Ol, Opx, SiO2).
                title_aliases = []
                for a in aliases:
                    a_str = str(a)
                    if a_str.isupper():
                        title_aliases.append(a_str.title())
                    else:
                        title_aliases.append(a_str)
                display_aliases = ", ".join(title_aliases)
                bullets.append(f"<b>{key_name}</b>{opt_str}: {display_aliases}")
            else:
                bullets.append(f"<b>{key_name}</b>{opt_str}")
                
        return {
            "header": "<b>Required columns</b> (with list of all accepted column names)",
            "bullets": bullets
        }
    except Exception as e:
        return {"header": f"Error loading instructions: {str(e)}", "bullets": []}
