import logging
import os
import sys
from eks_handler import handle_eks_yaml

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,  # Adjust as needed: DEBUG, INFO, WARNING, ERROR, CRITICAL
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('eks_configurator.log', mode='a')  # Log to a file
    ]
)

def get_user_selection():
    print("Welcome to the EKS Deployment Configurator!")
    print("Please select the configurations you want to add:")

    options = {
        '1': 'Service Account',
        '2': 'Ingress',
    }

    for key, value in options.items():
        print(f"{key}. {value}")

    selected_options = input("Enter the numbers of the options you want to add, separated by commas (e.g., 1,2): ")
    selected_options = selected_options.strip()

    if not selected_options:
        logging.error("No options selected.")
        return []

    selected_keys = [key.strip() for key in selected_options.split(',')]
    selected_configs = [options.get(key) for key in selected_keys if key in options]

    if not selected_configs:
        logging.error("Invalid options selected.")
    
    return selected_configs

def main():
    try:
        current_dir = os.getcwd()
        logging.info(f"Current Directory: {current_dir}")

        yaml_file_name = "eks-deployment.yaml"
        yaml_file_path = os.path.join(current_dir, yaml_file_name)

        logging.info(f"Looking for file: {yaml_file_path}")

        if not os.path.exists(yaml_file_path):
            logging.error(f"Error: '{yaml_file_name}' not found in the current directory.")
            print(f"Error: '{yaml_file_name}' not found in the current directory.")
            sys.exit(1)

        option_map = {
            'Service Account': 'Service Account',
            'Ingress': 'Ingress',
        }

        while True:
            selected_configs = get_user_selection()

            if not selected_configs:
                logging.info("No valid configurations selected.")
                print("No valid configurations selected.")

            options = [option_map[config] for config in selected_configs]

            # Handle the YAML modifications based on the user's selection
            handle_eks_yaml(yaml_file_path, options)

            logging.info("Configurations added successfully!")
            print("Configurations added successfully!")

            continue_choice = input("Do you want to add another configuration? (yes/no): ").strip().lower()
            if continue_choice != 'yes':
                break

    except Exception as e:
        logging.exception("An unexpected error occurred:")
        print("An unexpected error occurred. Check the log file for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
