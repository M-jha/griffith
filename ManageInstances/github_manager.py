import os
import requests
from flask import jsonify, request


class GitHubResource:
    """
    Class to manage GitHub organization members, repositories, and user access.
    """

    def __init__(self, org_name=None):
        """
        Initialize the GitHubResource class with a personal access token (PAT) from environment variable and organization name.

        Parameters:
            org_name (str): Name of the GitHub organization to manage. If not passed, use the default.
        """
        self.github_pat = os.getenv("GIT_SECRET")  # Use the environment variable if available
        if not self.github_pat:
            raise ValueError("GitHub Personal Access Token not found in environment variables.")
        self.org_name = org_name or 'GriffithGithubOrg'
        self.base_url = "https://api.github.com"

    def get_org_members(self):
        """
        Fetch the list of members in the GitHub organization.

        Returns:
            dict: A dictionary with the list of members or an error message.
        """
        url = f"{self.base_url}/orgs/{self.org_name}/members"
        headers = {"Authorization": f"token {self.github_pat}"}

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            members = response.json()
            member_list = [{"username": member['login']} for member in members]
            return {"data": member_list}  # Return raw JSON data
        else:
            return {
                "error": f"Failed to retrieve members: {response.status_code} - {response.text}"
            }

    def get_org_repos(self):
        """
        Fetch the list of repositories in the GitHub organization.

        Returns:
            dict: A dictionary with the list of repositories or an error message.
        """
        url = f"{self.base_url}/orgs/{self.org_name}/repos"
        headers = {"Authorization": f"token {self.github_pat}"}

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            repos = response.json()
            repo_list = [{"name": repo['name'], "url": repo['html_url']} for repo in repos]
            return {"repositories": repo_list}  # Return raw JSON data
        else:
            return {
                "error": f"Failed to retrieve repositories: {response.status_code} - {response.text}"
            }

    def get_user_access_level(self, username, repo):
        """
        Get the access level of a user for a specific repository in the organization.

        Parameters:
            username (str): The username of the user.
            repo (str): The repository name.

        Returns:
            dict: A dictionary with the access level or an error message.
        """
        headers = {"Authorization": f"token {self.github_pat}"}

        if not username or not repo:
            return {"error": "Missing username or repo parameter"}

        url = f"{self.base_url}/repos/{self.org_name}/{repo}/collaborators/{username}/permission"

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            access_data = response.json()
            access_level = access_data.get('permission', 'none')
            return {"accessLevel": access_level}  # Return raw JSON data
        else:
            return {
                "error": f"Failed to retrieve access level: {response.status_code} - {response.text}"
            }

    def manage_user_access(self, username, repo, access):
        """
        Manage (add or update) a user's access level for a specific repository in the organization.

        Parameters:
            username (str): The username of the user.
            repo (str): The repository name.
            access (str): The level of access ('pull', 'push', 'admin').

        Returns:
            dict: A dictionary with a success or error message.
        """
        if not username or not repo or not access:
            return {"error": "Missing username, repo, or access level"}

        headers = {
            'Authorization': f'Bearer {self.github_pat}',
            'Accept': 'application/vnd.github.v3+json'
        }
        url = f"{self.base_url}/repos/{self.org_name}/{repo}/collaborators/{username}"
        payload = {"permission": access}

        try:
            response = requests.put(url, headers=headers, json=payload)

            if response.status_code in [201, 204]:
                return {"message": f"Access level for {username} has been updated to {access} in {repo}."}
            else:
                return {
                    "error": f"Failed to manage access: {response.status_code} - {response.text}"
                }
        except requests.RequestException as e:
            return {"error": str(e)}

    def create_repo(self, repo_name, private=True):
        """
        Create a new repository in the GitHub organization.

        Parameters:
            repo_name (str): Name of the repository to create.
            private (bool): Whether the repository should be private or public (default is True).

        Returns:
            dict: A dictionary with repository details or an error message.
        """
        url = f"{self.base_url}/orgs/{self.org_name}/repos"
        headers = {
            'Authorization': f'Bearer {self.github_pat}',
            'Accept': 'application/vnd.github.v3+json'
        }
        payload = {
            "name": repo_name,
            "private": private,
            "auto_init": True,
            "gitignore_template": "Python"
        }

        try:
            response = requests.post(url, headers=headers, json=payload)

            if response.status_code == 201:
                return {"message": f"Repository '{repo_name}' created successfully"}
            else:
                return {
                    "error": f"Failed to create repository: {response.status_code} - {response.text}"
                }
        except requests.RequestException as e:
            return {"error": str(e)}

    def delete_repo(self, repo_name):
        """
        Delete a repository from the GitHub organization.

        Parameters:
            repo_name (str): Name of the repository to delete.

        Returns:
            dict: A dictionary with success or error message.
        """
        url = f"{self.base_url}/repos/{self.org_name}/{repo_name}"
        headers = {"Authorization": f"token {self.github_pat}"}

        response = requests.delete(url, headers=headers)

        if response.status_code == 204:
            return {"message": f"Repository '{repo_name}' deleted successfully"}
        else:
            return {
                "error": f"Failed to delete repository: {response.status_code} - {response.text}"
            }
