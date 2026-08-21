import yaml

def generate_yaml_instructions(yaml_path: str, optional_columns: list = None) -> str:
    """Generates an HTML instruction string from a column aliases YAML file."""
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            
        if not data:
            return ""
            
        lines = []
        lines.append("<p><b>Required columns (with list of all accepted column names)</b></p>")
        lines.append("<ul>")
        
        for key, aliases in data.items():
            # If the key is all uppercase, title-case it. Otherwise, keep original casing (e.g., Ol, Opx, SiO2).
            key_name = key.title() if isinstance(key, str) and key.isupper() else key
            
            # Format optional columns string
            opt_str = ""
            if optional_columns and key in optional_columns:
                opt_str = " <i>(Optional)</i>"
                
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
                lines.append(f"<li><b>{key_name}</b>{opt_str}: <i>{display_aliases}</i></li>")
            else:
                lines.append(f"<li><b>{key_name}</b>{opt_str}</li>")
                
        lines.append("</ul>")
        return "".join(lines)
    except Exception as e:
        return f"<p style='color: red; font-size: 12px;'>Error loading instructions: {str(e)}</p>"
