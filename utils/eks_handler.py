import yaml
import logging
import re
import os

from utils.configmaps_utils import (
    add_configmap_to_eks_deployment,
    read_configmap_file,
    uncomment_configmap_lines,
    ensure_data_section,
    add_configmap_entries,
)

from utils.secretmap_utils import (
    add_secretmap_to_eks_deployment,
    read_secretmap_file,
    uncomment_secretmap_lines,
    ensure_data_section,
    add_secretmap_entries,
)

# Set up logging
logger = logging.getLogger(__name__)

def handle_eks_yaml(file_path, options, ingress_path=None, configmap_options=None, secretmap_options=None):
    try:
        microservice_name = get_microservice_name(file_path)
        if not microservice_name:
            logger.error("Microservice name could not be extracted.")
            return

        if 'Service Account' in options:
            add_configuration(file_path, microservice_name, template_path='templates/service-account.yaml')

        if 'Ingress' in options:
            add_configuration(file_path, microservice_name, template_path='templates/ingress.yaml', ingress_path=ingress_path)
            update_azure_pipeline_ingress('azure-pipeline-CD.yaml', add_ingress=True)

        if 'Config-map' in options and configmap_options:
            add_configuration(file_path, microservice_name, configmap_options=configmap_options)

        if 'Secret-map' in options and secretmap_options:
            add_configuration(file_path, microservice_name, secretmap_options=secretmap_options)

    except Exception as e:
        logger.exception("Error handling EKS YAML:")
        raise

def get_microservice_name(file_path):
    """Extract the microservice name from the EKS YAML file."""
    microservice_name = None
    try:
        with open(file_path, 'r') as file:
            content = file.read()

            # Replace placeholders with dummy values to avoid parsing errors
            content = re.sub(r'\{\{.*?\}\}', 'dummy_value', content)

            # Load YAML content
            data = yaml.safe_load_all(content)
            for document in data:
                if isinstance(document, dict):
                    metadata = document.get('metadata', {})
                    labels = metadata.get('labels', {})
                    if 'app' in labels:
                        microservice_name = labels['app']
                        break
    except yaml.YAMLError as e:
        logger.error(f"YAML Error: {e}")
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
    return microservice_name

def add_configuration(file_path, microservice_name, template_path=None, ingress_path=None, configmap_options=None, secretmap_options=None):
    """Add the specified configuration to the YAML file"""
    if template_path:
        template = load_template(template_path)
        if not template:
            return

        configuration_yaml = template.replace('{{microservice_name}}', microservice_name)

        if 'ingress' in template_path.lower():
            configuration_yaml = configuration_yaml.replace('{{microservice_path}}', ingress_path)

        try:
            with open(file_path, 'r+') as file:
                content = file.read().rstrip()
                file.seek(0)
                file.truncate()
                file.write('\n')
                file.write(content + '\n\n' + configuration_yaml)
            logger.info(f"Added configuration from {template_path} to {file_path}")
            logging.info("Configurations added successfully!")
            print("Configurations added successfully!")
        except IOError as e:
            logger.error(f"Error writing to file '{file_path}': {e}")
            logging.error("Error in adding configurations!")

    if configmap_options:
        """Add ConfigMap entries to eks-deployment."""
        add_configmap_to_eks_deployment(file_path, microservice_name, configmap_options)

        """Add ConfigMap entries to eks-config-maps.yaml"""
        configmap_file_path = os.path.join(os.getcwd(), 'eks-config-maps.yaml')

        if not os.path.exists(configmap_file_path):
            logger.error("eks-config-maps.yaml file not found in the current directory.")
            return

        configmap_data = read_configmap_file(configmap_file_path)
        uncommented_lines, full_file_commented = uncomment_configmap_lines(configmap_data)
        uncommented_lines = ensure_data_section(uncommented_lines, microservice_name, full_file_commented)
        uncommented_lines = add_configmap_entries(uncommented_lines, configmap_options)

        with open(configmap_file_path, 'w') as configmap_file:
            configmap_file.writelines(uncommented_lines)

        logger.info(f"ConfigMap entries added successfully to {configmap_file_path}")
        print("ConfigMap entries added successfully to the deployment.")

    if secretmap_options:
        add_secretmap_to_eks_deployment(file_path, microservice_name, secretmap_options)

        secretmap_file_path = os.path.join(os.getcwd(), 'eks-config-secrets.yaml')

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


def load_template(file_path):
    """Load the YAML template from a file."""
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except FileNotFoundError:
        logger.error(f"File '{file_path}' not found.")
        return None

def update_azure_pipeline_ingress(file_path, add_ingress=False):
    if not add_ingress:
        return

    try:
        with open(file_path, 'r') as file:
            content = file.readlines()

        stages = {
            'dev': ('non-prod', 'dev.apps.api.it.philips.com'),
            'test': ('non-prod', 'dev.apps.api.it.philips.com'),
            'acc': ('non-prod', 'acc.apps.api.it.philips.com'),
            'prod': ('prod', 'apps.api.it.philips.com')
        }

        for i, line in enumerate(content):
            if line.strip().startswith('template=`cat eks-deployment.yaml'):
                for stage, (env, host) in stages.items():
                    if stage == 'prod':
                        namespace = 'itaap-prod-hyperautomation'
                    elif stage == 'acc': 
                        namespace = 'itaap-acc-hyperautomation'
                    else:
                        namespace = f'itaap-non-prod-hyperautomation-{stage}'
                    
                    if namespace in line:
                        new_line = line.rstrip() + f' | sed "s/{{{{env}}}}/{env}/g" | sed "s/{{{{envIdentifier}}}}/$(ENV_IDENTIFIER)/g" | sed "s/{{{{host}}}}/{host}/g"`\n'
                        content[i] = new_line
                        break

        with open(file_path, 'w') as file:
            file.writelines(content)
        print(f"Updated Azure pipeline CD file: {file_path}")
        logger.info(f"Updated Azure pipeline CD file: {file_path}")
    except Exception as e:
        logger.error(f"Error updating Azure pipeline CD file: {e}")
