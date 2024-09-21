from openai import AzureOpenAI
from datetime import datetime
from AWS.AWSResource import AWSResourceFactory
import boto3

client = AzureOpenAI(
  azure_endpoint = "https://griffith.openai.azure.com/",
  api_key= "9afff3ab5f0e4e0492dd0ed64194dba1",
  api_version="2023-05-15"
)

# Generate a unique filename using the current timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = f"chatgpt responses/openai_response_{timestamp}.txt"

try:
    response = client.chat.completions.create(
        model="griffith-gpt-4o",  # model = "deployment_name".
        messages=[
            {"role": "system", "content": "You are an expert CA"},
            {"role": "user", "content": f"calculate final amount if lumsum of 100 is invested for 15% return and for 30 years' "}
        ]
    )

    response_content = response.choices[0].message.content
    print(response_content)

    # Save response to a unique file
    with open(output_file, "w") as file:
        file.write(response_content + "\n")  # Save the response in a unique file

except Exception as e:
    print("Error: ", e)
