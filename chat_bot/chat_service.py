import requests
import re
import ast
import json
import importlib.util
import os
import openai


class GPTFunctionExecutor:
    def __init__(self, repo_owner, repo_name, branch='main'):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.branch = branch
        self.combined_knowledge_base = {}
        self.code_files = []
        self.conversation_history = []
        # Initialize OpenAI API configuration for Azure
        openai.api_type = "azure"
        openai.api_base = "https://griffith.openai.azure.com/"
        openai.api_version = "2023-05-15"
        openai.api_key = os.getenv('AZURE_OPENAI_API_KEY', '09cbdfcff42a458eb956d555c6512ab6')

    def fetch_file_from_github(self, file_path):
        if file_path == 'README.md':
            url = f'https://raw.githubusercontent.com/{self.repo_owner}/{self.repo_name}/{self.branch}/{file_path}'
        else:
            url = f'https://raw.githubusercontent.com/{self.repo_owner}/{self.repo_name}/{self.branch}/ManageInstances/{file_path}'
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            raise Exception(f"Failed to fetch {file_path} from GitHub. Status code: {response.status_code}")

    def parse_readme_for_mappings(self, readme_content):
        mappings = {}
        lines = readme_content.split('\n')
        current_class = None
        for line in lines:
            match = re.match(r'###\s+\d+\.\s+(\w+)', line)
            if match:
                current_class = match.group(1)  # Get class name
            elif current_class and line.strip().startswith('**Purpose**:'):
                purpose = line.strip().split('**Purpose**:')[1].strip()
                mappings[current_class] = purpose  # Store class name and purpose
        return mappings

    def parse_python_file(self, file_content, file_name):
        tree = ast.parse(file_content, filename=file_name)
        classes = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                methods = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        func_name = item.name
                        docstring = ast.get_docstring(item) or ''
                        args = [arg.arg for arg in item.args.args if arg.arg != 'self']
                        methods.append({
                            'function_name': func_name,
                            'docstring': docstring,
                            'arguments': args
                        })
                classes[class_name] = methods
        return classes

    def build_code_knowledge_base(self, file_paths):
        knowledge_base = {}
        for file_path in file_paths:
            file_content = self.fetch_file_from_github(file_path)
            if file_content:
                classes = self.parse_python_file(file_content, file_path)
                knowledge_base.update(classes)
        return knowledge_base

    def build_combined_knowledge_base(self, task_class_mappings, code_knowledge_base):
        combined_kb = {}
        for cls, purpose in task_class_mappings.items():
            if cls in code_knowledge_base:
                combined_kb[cls] = {
                    'purpose': purpose,
                    'methods': code_knowledge_base[cls]
                }
        self.combined_knowledge_base = combined_kb

    def initialize(self):
        # Fetch README.md content
        readme_content = self.fetch_file_from_github('README.md')
        if not readme_content:
            raise Exception("Failed to fetch README.md")

        # Parse README for task-class mappings
        task_class_mappings = self.parse_readme_for_mappings(readme_content)

        # List of code files to parse
        self.code_files = [
            'iam_policy_automation.py',
            'ec2_management.py',
            'rds_management.py'
        ]

        # Build the code knowledge base
        code_knowledge_base = self.build_code_knowledge_base(self.code_files)

        # Build the combined knowledge base
        self.build_combined_knowledge_base(task_class_mappings, code_knowledge_base)

    def generate_system_prompt(self):
        prompt_parts = []
        for cls, info in self.combined_knowledge_base.items():
            purpose = info['purpose']
            methods = info['methods']
            method_descriptions = "\n".join([
                f"- {method['function_name']}({', '.join(method['arguments'])}): {method['docstring']}"
                for method in methods
            ])
            class_description = f"""
            Class: {cls}
            Purpose: {purpose}
            Methods:
            {method_descriptions}
            """
            prompt_parts.append(class_description)

        # Join the parts together to form the complete system prompt
        system_prompt = "\n".join(prompt_parts)
        return system_prompt

    def interpret_user_prompt(self, user_input):
        # Generate the system prompt once
        system_prompt = f"""
        You are an assistant that helps users manage AWS resources by mapping their requests to Python class methods based on their descriptions.

        Available classes and methods:
        {self.generate_system_prompt()}

        Your task is to:

        1. Understand the user's request and identify the appropriate class method(s) from the available list that can fulfill the request.

        2. **If the request requires parameters, prompt the user in the same interaction to provide them.** Example:
            - "create a new IAM user with username X"
            - "launch a new EC2 instance with type Y"

        3. Output the function details **only in JSON format**. The format should be:

        ```json
        [
            {{
                "class_name": "<ClassName>",
                "function_name": "<FunctionName>",
                "parameters": {{
                    "<param1>": "<value1>",
                    "<param2>": "<value2>"
                }}
            }}
        ]
        ```

        Ensure the JSON block is formatted properly, including opening and closing code blocks marked by ```json.

        Do not include any conversational text in your response. Only output JSON.
        """

        # Add the system prompt only if it's the first turn
        if not self.conversation_history:
            self.conversation_history.append({"role": "system", "content": system_prompt})

        # Add the user's message to the conversation history
        self.conversation_history.append({"role": "user", "content": user_input})

        # Call the OpenAI API with the conversation history
        response = openai.ChatCompletion.create(
            engine="griffith-gpt-4o",
            messages=self.conversation_history,
            temperature=0
        )

        # Get the assistant's reply
        assistant_reply = response['choices'][0]['message']['content']
        # Add the assistant's reply to the conversation history
        self.conversation_history.append({"role": "assistant", "content": assistant_reply})

        return assistant_reply

    def sanitize_gpt_response(self, response_text):
        # Remove any markdown code fences
        if response_text.startswith('```'):
            # Find the closing code fence
            end_index = response_text.find('```', 3)
            if end_index != -1:
                response_text = response_text[3:end_index]
            else:
                response_text = response_text[3:]
        # Strip leading and trailing whitespace
        response_text = response_text.strip()
        return response_text

    def extract_function_details_from_reply(self, assistant_reply):
        """
        Extracts the JSON function details from the assistant's reply.
        """
        try:
            start_index = assistant_reply.find('```json')
            if start_index != -1:
                start_index += len('```json')
                end_index = assistant_reply.find('```', start_index)
                if end_index != -1:
                    json_str = assistant_reply[start_index:end_index].strip()
                else:
                    json_str = assistant_reply[start_index:].strip()
            else:
                print("No JSON block found in the assistant's reply.")
                return None

            json_str = self.sanitize_gpt_response(json_str)

            if json_str:
                return json_str
            else:
                print("Error: Extracted JSON string is empty or invalid.")
                return None

        except Exception as e:
            print(f"Error extracting function details: {e}")
            return None

    # def load_class_and_execute_method(self, class_name, function_name, parameters):
    #     """
    #     Dynamically load a class from a local file and execute the desired method.
    #     """
    #     try:
    #         # Check if the class belongs to a known module and import locally
    #         if class_name == "IAMPolicyAutomation":
    #             from iam_policy_automation import IAMPolicyAutomation
    #             cls = IAMPolicyAutomation
    #         elif class_name == "EC2Management":
    #             from ec2_management import EC2Management
    #             cls = EC2Management
    #         elif class_name == "RDSManagement":
    #             from rds_management import RDSManagement
    #             cls = RDSManagement
    #         else:
    #             print(f"Error: Unsupported class '{class_name}'")
    #             return None
    #
    #         # Initialize the class
    #         instance = cls()
    #
    #         # Check if the method exists in the class
    #         if not hasattr(instance, function_name):
    #             print(f"Error: Method '{function_name}' not found in class '{class_name}'.")
    #             return None
    #
    #         # Get the method from the instance
    #         method = getattr(instance, function_name)
    #
    #         # Execute the method with the provided parameters
    #         result = method(**parameters)
    #         print(f"Executed {class_name}.{function_name} successfully. Result: {result}")
    #         return result
    #
    #     except ModuleNotFoundError as e:
    #         print(f"Error: Module not found for class '{class_name}'. Ensure the module is available locally.")
    #     except AttributeError as e:
    #         print(f"Error: Method '{function_name}' not found in class '{class_name}'.")
    #     except Exception as e:
    #         print(f"An error occurred: {e}")

    def load_class_and_execute_method(self, class_name, function_name, parameters):
        """
        Dynamically load a class from a local file and execute the desired method.
        """
        try:
            # Manually load the module if it's not automatically found
            if class_name == "IAMPolicyAutomation":
                module_path = os.path.join(os.getcwd(), 'iam_policy_automation.py')
                spec = importlib.util.spec_from_file_location("iam_policy_automation", module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                cls = getattr(module, "IAMPolicyAutomation")
            elif class_name == "EC2Management":
                from ec2_management import EC2Management
                cls = EC2Management
            elif class_name == "RDSManagement":
                from rds_management import RDSManagement
                cls = RDSManagement
            else:
                raise Exception(f"Error: Unsupported class '{class_name}'")

            # Initialize the class
            instance = cls()

            # Check if the method exists in the class
            if not hasattr(instance, function_name):
                raise Exception(f"Error: Method '{function_name}' not found in class '{class_name}'.")

            # Get the method from the instance
            method = getattr(instance, function_name)

            # Execute the method with the provided parameters
            result = method(**parameters)
            print(f"Executed {class_name}.{function_name} successfully. Result: {result}")
            return result

        except ModuleNotFoundError as e:
            print(f"Error: Module not found for class '{class_name}'. Ensure the module is available locally.")
        except AttributeError as e:
            print(f"Error: Method '{function_name}' not found in class '{class_name}'.")
        except Exception as e:
            print(f"An error occurred: {e}")

    def execute_functions(self, function_details_list):
        results = []

        for function_details in function_details_list:
            class_name = function_details['class_name']
            function_name = function_details['function_name']
            parameters = function_details['parameters']

            # Dynamically load class and execute the method locally
            result = self.load_class_and_execute_method(class_name, function_name, parameters)
            if result is not None:
                results.append({
                    'class_name': class_name,
                    'function_name': function_name,
                    'result': result
                })
            else:
                results.append({
                    'class_name': class_name,
                    'function_name': function_name,
                    'error': f"Failed to execute {class_name}.{function_name}"
                })

        return results

    def run(self, user_input, provided_parameters=None, use_gpt=True):
        """
        Process user input and return a JSON response.
        This method handles missing parameters and prompts user to confirm execution.
        """
        # Interpret the user input with GPT
        if use_gpt:
            assistant_reply = self.interpret_user_prompt(user_input)
        else:
            assistant_reply = user_input  # Bypass GPT when use_gpt is False (for missing parameters)

        # Extract function details from the assistant's reply
        function_details_json = self.extract_function_details_from_reply(assistant_reply)
        if not function_details_json:
            return {
                'message': "I couldn't extract valid function details. Please try again.",
                'bot_reply': assistant_reply
            }

        # Parse the function details JSON
        function_details_list = json.loads(function_details_json)

        # Check for missing parameters and prompt user to fill them
        if provided_parameters:
            for function_details in function_details_list:
                for param, value in provided_parameters.items():
                    function_details['parameters'][param] = value

        missing_parameters = False
        missing_fields = []
        for function_details in function_details_list:
            for param, value in function_details['parameters'].items():
                if value == "":  # Detect empty/missing parameters
                    missing_parameters = True
                    missing_fields.append(param)

        if missing_parameters:
            return {
                'message': f"Missing parameters: {', '.join(missing_fields)}. Please provide them.",
                'missing_fields': missing_fields,
                'bot_reply': assistant_reply,
                'function_details': function_details_list
            }

        # If no missing parameters, return confirmation request
        return {
            'message': "Do you want to proceed with executing these actions? Confirm with 'yes' or 'good to go'.",
            'bot_reply': assistant_reply,
            'function_details': function_details_list
        }

