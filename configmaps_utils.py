import re
import logging
from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True
yaml.default_flow_style = False 
logger = logging.getLogger(__name__)

# Global dictionary to store placeholder values
placeholder_map = {}

def add_configmap_to_eks_deployment(file_path, microservice_name, configmap_options):
    """Add ConfigMap entries to the eks-deployment.yaml file."""
    global placeholder_map

    try:
        with open(file_path, 'r') as file:
            content = file.read()

            # Generate unique placeholders for each original placeholder
            placeholder_map = {}
            def replace_placeholder(match):
                placeholder = f'__PLACEHOLDER_{len(placeholder_map) + 1}__'
                placeholder_map[placeholder] = match.group(0)
                return placeholder

            content = re.sub(r'\{\{.*?\}\}', replace_placeholder, content)

        yaml_data = list(yaml.load_all(content))

        for doc in yaml_data:
            if isinstance(doc, dict) and doc.get('kind') == 'Deployment':
                container_spec = doc['spec']['template']['spec']['containers'][0]
                env_vars = container_spec.get('env', [])
                configmap_name = f'{microservice_name}-config'

                # Add new ConfigMap entries
                for config_key, default_value in configmap_options.items():
                    env_vars.append({
                        'name': config_key,
                        'valueFrom': {
                            'configMapKeyRef': {
                                'name': configmap_name,
                                'key': config_key
                            }
                        }
                    })

                container_spec['env'] = env_vars

        # Dump YAML data back to file
        with open(file_path, 'w') as file:
            yaml.dump_all(yaml_data, file, explicit_start=True, allow_unicode=True)

        # Replace placeholders with original values
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
    with open(file_path, 'r') as configmap_file:
        return configmap_file.readlines()

def uncomment_configmap_lines(configmap_data):
    uncommented_lines = []
    data_section_start = False
    data_section_end = False

    for line in configmap_data:
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

    return uncommented_lines

def ensure_data_section(uncommented_lines, microservice_name):
    data_section_start = any(line.strip() == 'data:' for line in uncommented_lines)

    if not data_section_start:
        uncommented_lines.extend([
            '#Note: uncomment the below lines before configuring the properties. Key value should be used to configure properties and its values\n',
            'apiVersion: v1\n',
            'kind: ConfigMap\n',
            'metadata:\n',
            f'  name: {microservice_name}-config\n',
            '  namespace: {{deployNamespace}}\n',
            'data:\n'
        ])

    return uncommented_lines

def add_configmap_entries(uncommented_lines, configmap_options):
    for config_key, default_value in configmap_options.items():
        uppercase_key = config_key.upper().replace(' ', '_')
        uncommented_lines.append(f'  {uppercase_key}: "{default_value}"\n')

    return uncommented_lines
