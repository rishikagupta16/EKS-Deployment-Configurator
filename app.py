import logging
import os
import sys
from utils.eks_handler import handle_eks_yaml
import random
import time

# pyinstaller --onefile --add-data "templates:templates" --name EKS_Configurator app.py

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        # logging.StreamHandler(sys.stdout),
        logging.FileHandler('eks_configurator.log', mode='a')  # Log to a file
    ]
)

def get_user_selection():
    print("Please select the configurations you want to add:")

    options = {
        '1': 'Service Account',
        '2': 'Ingress',
        '3': 'Config-map',
        '4': 'Secret',
    }

    for key, value in options.items():
        print(f"{key}. {value}")

    selected_options = input("\nEnter the numbers of the options you want to add, separated by commas (e.g., 1,2,3), or 'quit' to exit: ")
    selected_options = selected_options.strip().lower()

    if selected_options == 'quit':
        return 'quit'

    if not selected_options:
        logging.error("No options selected.")
        return []

    selected_keys = [key.strip() for key in selected_options.split(',')]
    selected_configs = [options.get(key) for key in selected_keys if key in options]

    if not selected_configs:
        logging.error("Invalid options selected.")
    
    return selected_configs

def get_ingress_path():
    print("\nEnter the path to be added in the Ingress configuration (press Enter for root path)")
    ingress_path = input("e.g. '/your-microservice/api' : ").strip()
    return ingress_path

def get_options(prompt, options_dict, custom_option_name):
    """
    Generic function to get options from the user, including handling custom options.

    Args:
        prompt (str): The prompt to display to the user.
        options_dict (dict): A dictionary of pre-defined options.
        custom_option_name (str): The name of the custom option.

    Returns:
        dict: A dictionary of selected options.
    """
    print(prompt)

    for key, (option_name, _) in options_dict.items():
        print(f"{key}. {option_name}")

    selected_options = input("\nEnter the numbers of the options you want to add, separated by commas (e.g., 1,3,5): ").strip()
    selected_keys = [key.strip() for key in selected_options.split(',')]

    selected_inputs = {}
    invalid_keys = []

    for key in selected_keys:
        if key in options_dict:
            option_name, default_value = options_dict[key]
            if option_name == custom_option_name:
                custom_keys_input = input(f"\nEnter the custom {custom_option_name.lower()} key(s), separated by commas: ").strip().upper()
                custom_keys = [k.strip() for k in custom_keys_input.split(',')]
                for custom_key in custom_keys:
                    selected_inputs[custom_key] = "{{" + custom_key + "}}"
            else:
                selected_inputs[option_name.upper()] = default_value
        else:
            invalid_keys.append(key)

    if invalid_keys:
        print(f"Invalid option(s) entered: {', '.join(invalid_keys)}. Please select valid options.")

    return selected_inputs


def get_configmap_options():
    configmap_options = {
        '0': ('Other Custom config-map', "Custom"),
        '1': ('API_PATH', "{{apiPath}}"),
        '2': ('DB_URL', "{{dbUrl}}"),
        '3': ('DB_NAME', "{{dbName}}"),
        '4': ('DB_USER_NAME', "{{dbUserName}}"),
        '5': ('S3_DIR_ADDRESS', "{{s3DirAddress}}"),
        '6': ('S3_BUCKET_NAME', "{{s3BucketName}}"),
        '7': ('MINIMUM_IDLE', "{{minimumIdle}}"),
        '8': ('MAXIMUM_POOL_SIZE', "{{maximumPoolSize}}"),
        '9': ('IDLE_TIMEOUT', "{{idleTimeout}}"),
        '10': ('MAX_LIFETIME', "{{maxLifetime}}"),
        '11': ('CONNECTION_TIMEOUT', "{{connectionTimeout}}")
    }
    return get_options(
        "Please select the Configmap options you want to include:",
        configmap_options,
        'Other Custom config-map'
    )


def get_secretmap_options():
    secretmap_options = {
        '0': ('Other Custom Secret', "Custom secret"),
        '1': ('DB_PASSWORD', "{{dbPassword}}")
    }
    return get_options(
        "Please select the Secret options you want to include:",
        secretmap_options,
        'Other Custom Secret'
    )


def print_ascii_logo():
    logo = """
    ╔═╗╦╔═╔═╗  ╔═╗╔═╗╔╗╔╔═╗╦╔═╗╦ ╦╦═╗╔═╗╔╦╗╔═╗╦═╗
    ║╣ ╠╩╗╚═╗  ║  ║ ║║║║╠╣ ║║ ╦║ ║╠╦╝╠═╣ ║ ║ ║╠╦╝
    ╚═╝╩ ╩╚═╝  ╚═╝╚═╝╝╚╝╚  ╩╚═╝╚═╝╩╚═╩ ╩ ╩ ╚═╝╩╚═
    """
    print(logo)

def get_welcome_message():
    messages = [
        "Welcome to the future of automation!",
        "Empowering your workflow, one script at a time.",
        "Turning complex tasks into simple clicks.",
        "Your personal automation sidekick is here!",
        "Efficiency meets creativity - let's automate!",
        "Transforming ideas into automated reality.",
        "HyperAutomation: Where impossible becomes automated.",
        "Unleash the power of automation with us!",
        "Simplifying your day, the HyperAutomation way."
    ]
    return random.choice(messages)

def get_thank_you_message():
    messages = [
        "Thank you for using HyperAutomation! Have a great day!",
        "You're awesome! Thanks for automating with us!",
        "Automation complete! We hope you enjoyed the experience!",
        "Thank you for choosing HyperAutomation. Until next time!",
        "You've just made your microservice more efficient. Great job!"
    ]
    return random.choice(messages)

def animate_text(text):
    for char in text:
        print(char, end='', flush=True)
        time.sleep(0.05)
    print()

def main():
    print_ascii_logo()
    animate_text("Welcome to EKS Configurator!")
    print("\nMade with love <3 by HyperAutomation - ITaaP team\n")
    print(get_welcome_message())
    print("------------------------------------")
    
    try:
        current_dir = os.getcwd()
        logging.info(f"Current Directory: {current_dir}")

        yaml_file_name = "eks-deployment.yaml"
        yaml_file_path = os.path.join(current_dir, yaml_file_name)

        logging.info(f"Looking for file: {yaml_file_path}")

        if not os.path.exists(yaml_file_path):
            logging.error(f"Error: '{yaml_file_name}' not found in the current directory.")
            print(f"Error: '{yaml_file_name}' not found in the current directory, closing the application...")
            time.sleep(10)
            sys.exit(1)
        option_map = {
            'Service Account': 'Service Account',
            'Ingress': 'Ingress',
            'Config-map': 'Config-map',
            'Secret': 'Secret'
        }

        while True:
            selected_configs = get_user_selection()

            if selected_configs == 'quit':
                print(get_thank_you_message())
                time.sleep(5)
                sys.exit(0)

            if not selected_configs:
                logging.info("No valid configurations selected.")
                print("No valid configurations selected.")
                continue

            options = []
            ingress_path = None
            configmap_options = None
            secretmap_options = None
            
            for config in selected_configs:
                if config == 'Ingress':
                    ingress_path = get_ingress_path()
                elif config == 'Config-map': 
                    configmap_options = get_configmap_options()
                elif config == 'Secret':
                    secretmap_options = get_secretmap_options()
                options.append(option_map[config])

            # Handle the YAML modifications based on the user's selection
            handle_eks_yaml(yaml_file_path, options, ingress_path, configmap_options, secretmap_options)

            logging.info("Configurations added successfully!")
            print("Configurations added successfully!")

            continue_choice = input("Do you want to add another configuration? (yes/no): ").strip().lower()
            if continue_choice != 'yes':
                print(get_thank_you_message())
                time.sleep(5)
                break
                
    except KeyError as e:
        logging.exception(f"A KeyError occurred: {e}")
        print(f"A KeyError occurred: {e}. Please check your input.")
        time.sleep(5)
        sys.exit(1)
    except Exception as e:
        logging.exception("An unexpected error occurred:")
        print("An unexpected error occurred. Check the log file for details.")
        time.sleep(5)
        sys.exit(1)

if __name__ == "__main__":
    main()
