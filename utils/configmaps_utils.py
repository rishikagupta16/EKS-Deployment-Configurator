import re
import logging
from ruamel.yaml import YAML

# Configure the YAML processor
yaml = YAML()
yaml.preserve_quotes = True
yaml.default_flow_style = False
yaml.width = float('inf')
yaml.indent(mapping=2, sequence=4, offset=2)

logger = logging.getLogger(__name__)

# Global dictionary to store placeholder values
placeholder_map = {}

def add_configmap_to_eks_deployment(file_path, microservice_name, configmap_options):
    """Add ConfigMap entries to the eks-deployment.yaml file."""
    global placeholder_map

    try:
        # Read the YAML file content
        with open(file_path, 'r') as file:
            content = file.read()

            # Replace placeholders with unique identifiers to preserve them during YAML processing
            placeholder_map = {}
            def replace_placeholder(match):
                placeholder = f'__PLACEHOLDER_{len(placeholder_map) + 1}__'
                placeholder_map[placeholder] = match.group(0)
                return placeholder

            content = re.sub(r'\{\{.*?\}\}', replace_placeholder, content)

        # Load the YAML data
        yaml_data = list(yaml.load_all(content))

        # Iterate through documents to find the Deployment kind
        for doc in yaml_data:
            if isinstance(doc, dict) and doc.get('kind') == 'Deployment':
                container_spec = doc['spec']['template']['spec']['containers'][0]
                env_vars = container_spec.get('env', [])

                # Find the insertion point
                insert_index = len(env_vars)
                for i, env in reversed(list(enumerate(env_vars))):
                    if 'configMapKeyRef' in env.get('valueFrom', {}):
                        insert_index = i + 1
                        break
                    if 'secretKeyRef' in env.get('valueFrom', {}):
                        insert_index = i
                
                try:
                    configmap_name = get_configmap_name('eks-config-maps.yaml')
                except ValueError as e:
                    logger.warning(str(e))
                    configmap_name = microservice_name  # Fallback to using microservice_name

                # Append new ConfigMap entries to the env section at the insertion point
                for config_key, _ in configmap_options.items():
                    new_env = {
                        'name': config_key,
                        'valueFrom': {
                            'configMapKeyRef': {
                                'name': configmap_name,
                                'key': config_key
                            }
                        }
                    }
                    env_vars.insert(insert_index, new_env)
                    insert_index += 1

                container_spec['env'] = env_vars

        # Write the modified YAML back to the file
        with open(file_path, 'w') as file:
            yaml.dump_all(yaml_data, file)

        # Replace placeholders back to their original values
        with open(file_path, 'r+') as file:
            content = file.read()
            for placeholder, original_value in placeholder_map.items():
                content = content.replace(placeholder, original_value)
            file.seek(0)
            file.write(content)
            file.truncate()

        logger.info(f"ConfigMap entries added to the container specification in {file_path}")

    except Exception as e:
        logger.error(f"Failed to add ConfigMap to EKS deployment: {e}")
        raise

def read_configmap_file(file_path):
    # Read the content of the EKS ConfigMap YAML file.
    with open(file_path, 'r') as configmap_file:
        return configmap_file.readlines()

def uncomment_configmap_lines(configmap_data):
    # Uncomment relevant lines in the ConfigMap YAML file.
    uncommented_lines = []
    data_section_start = False
    data_section_end = False
    full_file_commented = True

    for line in configmap_data:
        # Check if the entire file is commented
        if not line.strip().startswith('#') and line.strip():
            full_file_commented = False

        if line.startswith('apiVersion: v1'):
            uncommented_lines.append(line.lstrip('#'))
        elif line.strip() == 'data:':
            data_section_start = True
            uncommented_lines.append(line)
        elif data_section_start and not line.strip():
            data_section_end = True
        elif data_section_start and not data_section_end:
            uncommented_lines.append(line)
        else:
            uncommented_lines.append(line)

    return uncommented_lines, full_file_commented

def ensure_config_data_section(uncommented_lines, microservice_name, full_file_commented):
    """Ensure that the data section is present or add a template if the entire file was commented."""

    if full_file_commented:
        # If the entire file was commented, clear the content and add the template
        uncommented_lines.clear()
        uncommented_lines.extend([
            '# Note: uncomment the below lines before configuring the properties. Key value should be used to configure properties and its values\n',
            'apiVersion: v1\n',
            'kind: ConfigMap\n',
            'metadata:\n',
            f'  name: {microservice_name}\n',
            '  namespace: {{deployNamespace}}\n',
            'data:\n'
        ])

    return uncommented_lines

def add_configmap_entries(uncommented_lines, configmap_options):
    """Add ConfigMap entries to the data section."""
    for config_key, default_value in configmap_options.items():
        uppercase_key = config_key.upper().replace(' ', '_')
        uncommented_lines.append(f'  {uppercase_key}: "{default_value}"\n')

    return uncommented_lines

def get_configmap_name(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
        # Remove comments
        uncommented = '\n'.join(line for line in content.split('\n') if not line.strip().startswith('#'))
        if uncommented.strip():
            # If uncommented content exists, parse it
            data = yaml.load(uncommented)
        else:
            # If all content is commented, parse with comments
            data = yaml.load(content)
    
    if data and isinstance(data, dict):
        return data.get('metadata', {}).get('name')
    else:
        # If no valid data is found, return a default name or raise an exception
        raise ValueError(f"No valid ConfigMap name found in {file_path}")
