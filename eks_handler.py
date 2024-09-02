import yaml
import logging
import re
import os

from configmaps_utils import (
    add_configmap_to_eks_deployment,
    read_configmap_file,
    uncomment_configmap_lines,
    ensure_data_section,
    add_configmap_entries,
)

# Set up logging
logger = logging.getLogger(__name__)

def handle_eks_yaml(file_path, options, ingress_path=None, configmap_options=None):
    try:
        microservice_name = get_microservice_name(file_path)
        if not microservice_name:
            logger.error("Microservice name could not be extracted.")
            return

        if 'Service Account' in options:
            add_configuration(file_path, microservice_name, template_path='templates/service-account.yaml')

        if 'Ingress' in options:
            if not ingress_path:
                logger.error("Ingress path is required but not provided.")
                return
            add_configuration(file_path, microservice_name, template_path='templates/ingress.yaml', ingress_path='/api')
        if 'Config-map' in options and configmap_options:
            add_configuration(file_path, microservice_name, configmap_options=configmap_options)

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

def add_configuration(file_path, microservice_name, template_path=None, ingress_path=None, configmap_options=None):
    """Add the specified configuration to the YAML file"""
    if template_path:
        template = load_template(template_path)
        if not template:
            return

        configuration_yaml = template.replace('{{microservice_name}}', microservice_name)

        if ingress_path:
            configuration_yaml = configuration_yaml.replace('{{microservice_path}}', ingress_path)

        try:
            with open(file_path, 'a') as file:
                file.write(configuration_yaml)
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
        configmap_file_path = os.path.join(os.path.dirname(__file__), 'eks-config-maps.yaml')

        if not os.path.exists(configmap_file_path):
            logger.error("eks-config-maps.yaml file not found in the current directory.")
            return

        configmap_data = read_configmap_file(configmap_file_path)
        uncommented_lines = uncomment_configmap_lines(configmap_data)
        uncommented_lines = ensure_data_section(uncommented_lines, microservice_name)
        uncommented_lines = add_configmap_entries(uncommented_lines, configmap_options)

        with open(configmap_file_path, 'w') as configmap_file:
            configmap_file.writelines(uncommented_lines)

        logger.info(f"ConfigMap entries added successfully to {configmap_file_path}")
        print("ConfigMap entries added successfully to the deployment.")


def load_template(file_path):
    """Load the YAML template from a file."""
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except FileNotFoundError:
        logger.error(f"File '{file_path}' not found.")
        return None
