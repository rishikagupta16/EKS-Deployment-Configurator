import re
import logging
import os
from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True
yaml.default_flow_style = False
yaml.width = float('inf')
yaml.indent(mapping=2, sequence=4, offset=2)

logger = logging.getLogger(__name__)

placeholder_map = {}

def add_secretmap_to_eks_deployment(file_path, microservice_name, secretmap_options):
    try:
        with open(file_path, 'r') as file:
            content = file.read()

            placeholder_map.clear()
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

                insert_index = len(env_vars)
                for i, env in reversed(list(enumerate(env_vars))):
                    if 'secretKeyRef' in env.get('valueFrom', {}):
                        insert_index = i + 1
                        break

                try:
                    secretmap_name = get_secretmap_name('eks-config-secrets.yaml')
                except ValueError as e:
                    logger.warning(str(e))
                    secretmap_name = f"{microservice_name}"

                for secret_key, _ in secretmap_options.items():
                    new_env = {
                        'name': secret_key,
                        'valueFrom': {
                            'secretKeyRef': {
                                'name': secretmap_name,
                                'key': secret_key
                            }
                        }
                    }
                    env_vars.insert(insert_index, new_env)
                    insert_index += 1

                container_spec['env'] = env_vars

        with open(file_path, 'w') as file:
            yaml.dump_all(yaml_data, file)

        with open(file_path, 'r+') as file:
            content = file.read()
            for placeholder, original_value in placeholder_map.items():
                content = content.replace(placeholder, original_value)
            file.seek(0)
            file.write(content)
            file.truncate()

        logger.info(f"Secret-map entries added to the container specification in {file_path}")

    except Exception as e:
        logger.error(f"Failed to add Secret-map to EKS deployment: {e}")
        raise

def read_secretmap_file(file_path):
    with open(file_path, 'r') as secretmap_file:
        return secretmap_file.readlines()

def uncomment_secretmap_lines(secretmap_data):
    uncommented_lines = []
    data_section_start = False
    data_section_end = False
    full_file_commented = True

    for line in secretmap_data:
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

def ensure_data_section(uncommented_lines, microservice_name, full_file_commented):
    if full_file_commented:
        uncommented_lines.clear()
        uncommented_lines.extend([
            '# Note: uncomment the below lines before configuring the properties. Key value should be used to configure properties and its values\n',
            'apiVersion: v1\n',
            'kind: Secret\n',
            'metadata:\n',
            f'  name: {microservice_name}\n',
            '  namespace: {{deployNamespace}}\n',
            'data:\n'
        ])

    return uncommented_lines

def add_secretmap_entries(uncommented_lines, secretmap_options):
    for secret_key, default_value in secretmap_options.items():
        uppercase_key = secret_key.upper().replace(' ', '_')
        uncommented_lines.append(f'  {uppercase_key}: "{default_value}"\n')
    return uncommented_lines

def get_secretmap_name(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
        uncommented = '\n'.join(line for line in content.split('\n') if not line.strip().startswith('#'))
        if uncommented.strip():
            data = yaml.load(uncommented)
        else:
            data = yaml.load(content)
    
    if data and isinstance(data, dict):
        return data.get('metadata', {}).get('name')
    else:
        raise ValueError(f"No valid Secret-map name found in {file_path}")

def update_eks_secret_maps(file_path, microservice_name, secretmap_options):
    secretmap_file_path = os.path.join(os.path.dirname(file_path), 'eks-config-secrets.yaml')

    if not os.path.exists(secretmap_file_path):
        logger.error("eks-config-secrets.yaml file not found in the current directory.")
        return

    secretmap_data = read_secretmap_file(secretmap_file_path)
    uncommented_lines, full_file_commented = uncomment_secretmap_lines(secretmap_data)
    uncommented_lines = ensure_data_section(uncommented_lines, microservice_name, full_file_commented)
    uncommented_lines = add_secretmap_entries(uncommented_lines, secretmap_options)

    with open(secretmap_file_path, 'w') as secretmap_file:
        secretmap_file.writelines(uncommented_lines)

    logger.info(f"Secret-map entries added successfully to {secretmap_file_path}")
    print("Secret-map entries added successfully to the deployment.")
