# EKS-Deployment-Configurator
## Project Overview
The EKS Deployment YAML Configurator is a command-line tool designed to simplify the configuration and customization of Kubernetes deployment YAML files for Amazon EKS (Elastic Kubernetes Service). This tool reads existing EKS deployment YAML files and allows users to easily modify or add configurations through an interactive command-line interface.

By guiding users through a series of prompts, the tool gathers the necessary input for creating or updating configurations such as Service Accounts, Ingress settings, Deployment environment variables, and placeholder values. The tool then automatically updates the YAML file with the provided details, ensuring consistency and reducing manual errors.

## Key Features
Interactive CLI: Users are prompted to provide or modify specific configurations in the EKS deployment YAML file.
YAML Parsing and Manipulation: Seamlessly reads and modifies YAML files, ensuring the correct structure and syntax are maintained.
Service Account and Ingress Configuration: Allows for easy addition or updating of Service Accounts, Ingress settings, and other deployment configurations.
Validation and Error Handling: Built-in validation ensures user inputs are correct and meaningful, with robust error handling for file operations.
Customizable Placeholders: Users can define and replace placeholder values in their YAML configurations, making the tool adaptable to various deployment environments.
Target Audience
This tool is intended for DevOps engineers, developers, and IT professionals who manage Kubernetes deployments on Amazon EKS and need a streamlined way to configure YAML files across their teams.

## Project Goals
Proof of Concept (POC): Develop a functional POC to demonstrate the tool's capability to read, modify, and write EKS deployment YAML files based on user input.
Department-wide Deployment: After successful validation, distribute the tool to the department for broader use, improving efficiency and reducing errors in managing EKS deployments.

## Technology Stack
Programming Language: Python 3.6+
Libraries:
PyYAML for YAML parsing and manipulation.
Click for building the command-line interface.
Version Control: GitHub for code collaboration and versioning.
