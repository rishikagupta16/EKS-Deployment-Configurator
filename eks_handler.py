import yaml
import logging
import re

# Set up logging
logger = logging.getLogger(__name__)

def handle_eks_yaml(file_path, options):
    """Handle modifications to the YAML file based on user-selected options."""
    try:
        microservice_name = get_microservice_name(file_path)
        if not microservice_name:
            logger.error("Microservice name could not be extracted.")
            return
        
        # Assuming options is a list of selected configuration options
        if 'Service Account' in options:
            add_configuration(file_path, microservice_name, 'templates/service-account.yaml')
            logging.info("Configurations added successfully!")
            print("Configurations added successfully!")
        if 'Ingress' in options:
            add_configuration(file_path, microservice_name, 'templates/ingress.yaml')
            logging.info("Configurations added successfully!")
            print("Configurations added successfully!")

                
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
        logger.error("Error parsing YAML file:")
        logger.error(f"YAML Error: {e}")
    except Exception as e:
        logger.error("An unexpected error occurred:")
        logger.error(f"Unexpected Error: {e}")
    return microservice_name
            
def add_configuration(file_path, microservice_name, template_path):
    """Add the specified configuration to the YAML file."""
    template = load_template(template_path)
    if template:
        configuration_yaml = template.replace('{{microservice_name}}', microservice_name)
        try:
            with open(file_path, 'a') as file:
                file.write(configuration_yaml)
            logger.info(f"Added configuration from {template_path} to {file_path}")
        except IOError as e:
            logger.error(f"Error writing to file '{file_path}': {e}")

def load_template(file_path):
    """Load the YAML template from a file."""
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except FileNotFoundError:
        logger.error(f"File '{file_path}' not found.")
        return None