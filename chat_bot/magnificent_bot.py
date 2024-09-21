import requests
import re
import ast
import openai
import json
import importlib.util
import sys
import os


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
        # Replace 'YOUR_API_KEY' with your actual API key or set it as an environment variable
        openai.api_key = os.getenv('AZURE_OPENAI_API_KEY', '09cbdfcff42a458eb956d555c6512ab6')

    def fetch_file_from_github(self, file_path):
        url = f'https://raw.githubusercontent.com/{self.repo_owner}/{self.repo_name}/{self.branch}/{file_path}'
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            print(f"Failed to fetch {file_path} from GitHub. Status code: {response.status_code}")
            return None

    def parse_readme_for_mappings(self, readme_content):
        """
        Parses the README.md content to extract task-class mappings.

        Assumes that the README has sections in the format:
        ### 1. ClassName
        **Purpose**: <Description>
        """
        mappings = {}
        lines = readme_content.split('\n')
        current_class = None
        for line in lines:
            # Match class sections
            match = re.match(r'###\s+\d+\.\s+(\w+)', line)
            if match:
                current_class = match.group(1)
            elif current_class and line.strip().startswith('**Purpose**:'):
                purpose = line.strip().split('**Purpose**:')[1].strip()
                mappings[current_class] = purpose
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
        return combined_kb

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

    def interpret_user_prompt(self, user_prompt):
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
        self.conversation_history.append({"role": "user", "content": user_prompt})

        # Call the OpenAI API with the conversation history
        response = openai.ChatCompletion.create(
            engine="griffith-gpt-4o",  # Use your deployment_name here
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

    def load_class_from_file(self, file_content, class_name):
        module_name = f"module_{class_name}"
        spec = importlib.util.spec_from_loader(module_name, loader=None)
        module = importlib.util.module_from_spec(spec)
        exec(file_content, module.__dict__)
        cls = getattr(module, class_name)
        return cls

    def load_class_and_execute_method(self, class_name, function_name, parameters):
        """
        Dynamically load a class from a local file and execute the desired method.
        """
        try:
            # Check if the class belongs to a known module and import locally
            if class_name == "IAMPolicyAutomation":
                from iam_policy_automation import IAMPolicyAutomation
                cls = IAMPolicyAutomation
            elif class_name == "EC2Management":
                from ec2_management import EC2Management
                cls = EC2Management
            elif class_name == "RDSManagement":
                from rds_management import RDSManagement
                cls = RDSManagement
            else:
                print(f"Error: Unsupported class '{class_name}'")
                return None

            # Initialize the class
            instance = cls()

            # Check if the method exists in the class
            if not hasattr(instance, function_name):
                print(f"Error: Method '{function_name}' not found in class '{class_name}'.")
                return None

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

    def run(self):
        # Fetch README.md content
        readme_content = self.fetch_file_from_github('../README.md')
        if not readme_content:
            print("Failed to fetch README.md")
            return

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

        # Define a custom input function to handle PyDev issues
        def safe_input(prompt=''):
            print(prompt, end='')
            return sys.stdin.readline().rstrip('\n')

        # Start the conversational loop
        print("Assistant: Hello! How can I assist you today?")
        while True:
            # Get user input using the custom safe_input function
            user_input = safe_input("You: ")

            if not user_input:
                # EOF reached
                print("Assistant: Goodbye!")
                break

            if user_input.lower() in ["exit", "quit"]:
                print("Assistant: Goodbye!")
                break

            # Interpret the user prompt
            assistant_reply = self.interpret_user_prompt(user_input)
            print(f"Assistant: {assistant_reply}")

            # Extract the function details if provided in the assistant's reply
            function_details_json = self.extract_function_details_from_reply(assistant_reply)
            print("f_json:", function_details_json)
            if function_details_json:
                try:
                    function_details_list = json.loads(function_details_json)
                    print("f_lists:", function_details_list)
                except json.JSONDecodeError as e:
                    print(f"Assistant: Error parsing JSON: {e}")
                    continue

                # Check for missing parameters and ask the user to provide them
                missing_parameters = False
                for function_details in function_details_list:
                    for param, value in function_details['parameters'].items():
                        if value == "":  # Detect empty/missing parameters
                            missing_parameters = True
                            user_value = safe_input(f"Assistant: Please provide a value for '{param}': ")
                            function_details['parameters'][param] = user_value  # Update JSON with user-provided value

                if missing_parameters:
                    print(f"Updated function details: {json.dumps(function_details_list, indent=4)}")

                # Ask the user for confirmation to proceed with the action
                confirmation = safe_input(
                    "Assistant: Do you want me to proceed with executing these actions? (yes/no)\nYou: ")

                # Debugging: Print the confirmation input
                print(f"Confirmation input: '{confirmation}'")

                if confirmation.lower().strip() in ["yes", "y"]:
                    # Proceed to execute the functions
                    results = self.execute_functions(function_details_list)
                    for res in results:
                        if 'error' in res:
                            print(f"Assistant: Error in {res['class_name']}.{res['function_name']}: {res['error']}")
                        else:
                            print(f"Assistant: Executed {res['class_name']}.{res['function_name']} successfully.")
                            print(f"Assistant: Result: {res['result']}")
                else:
                    print("Assistant: Okay, let me know if you need anything else!")
            else:
                # No valid function details found, continue the conversation
                print("Assistant: I couldn't extract the function details. Please try again.")

    def extract_function_details_from_reply(self, assistant_reply):
        """
        Extracts the JSON function details from the assistant's reply.
        """
        try:
            # Find the JSON code block enclosed in ```json ... ```
            start_index = assistant_reply.find('```json')
            if start_index != -1:
                start_index += len('```json')
                end_index = assistant_reply.find('```', start_index)
                if end_index != -1:
                    json_str = assistant_reply[start_index:end_index].strip()
                else:
                    json_str = assistant_reply[start_index:].strip()
            else:
                # No JSON block found, return None
                print("No JSON block found in the assistant's reply.")
                return None

            # Sanitize the JSON string
            json_str = self.sanitize_gpt_response(json_str)

            # Check if the string is valid JSON
            if json_str:
                return json_str
            else:
                print("Error: Extracted JSON string is empty or invalid.")
                return None

        except Exception as e:
            print(f"Assistant: Error extracting function details: {e}")
            return None


def main():
    repo_owner = 'M-jha'  # Replace with your GitHub username
    repo_name = 'griffith'  # Replace with your repository name
    branch = 'main'
    executor = GPTFunctionExecutor(repo_owner, repo_name, branch)
    executor.run()


if __name__ == "__main__":
    main()