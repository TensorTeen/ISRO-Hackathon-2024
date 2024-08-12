from typing import Self, Optional
import os

from azure.ai.ml.entities import ManagedOnlineEndpoint, ManagedOnlineDeployment
from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential
from azure.core.exceptions import ClientAuthenticationError
from azure.core.credentials import AzureKeyCredential
from azure.ai.ml import MLClient
from azure.ai.ml.exceptions import ValidationException

from .schema import BaseTool

class AzureEndpointContextManager:
    """
    Important class to prevent leaving an endpoint running. ot really
        intended to be modified
    """
    def __init__(self, workspace_client: MLClient, endpoint: ManagedOnlineEndpoint):
        self.client = workspace_client
        self.endpoint = endpoint
    def __enter__(self) -> Self:
        self.client.begin_create_or_update(self.endpoint).wait()
        return self
    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        self.client.online_endpoints.begin_delete(name=self.endpoint.name).wait()

# class AzureMLClient(MLClient):
#     """Slightly modified class to allow use of context managers for endpoints.
#             Inherits from MLClient
        
#         Methods:
#             endpoint(): Returns an AzureEndpointContextManager instance, 
#                 which contains this client and the endpoint

#     """
#     def __init__(self, *args, **kwargs) -> None:
#         super().__init__(*args, **kwargs)
#     def endpoint(self, endpoint: ManagedOnlineEndpoint) -> AzureEndpointContextManager:
#         """
#         Returns an AzureEndpointContextManager instance, which contains 
#             this client and the endpoint

#         Args:
#             endpoint (ManagedOnlineEndpoint): The endpoint to manage
#         """
#         return AzureEndpointContextManager(self, endpoint) # yes
        

class AzureTool(BaseTool):
    def __init__(self, name: str, description: str, version: str, args: Optional[dict] = None, config=None):
        """
        Initializes an instance of the schema class.
        Args:
            name (str): The name of the schema.
            description (str): The description of the schema.
            version (str): The version of the schema.
            args (dict, optional): Additional arguments for the schema. 
                Defaults to {}.
            config (str, optional): The file name of the configuration. 
                If not specified, uses config.json.
        """
        super().__init__(name, description, version, args)
        # self.tool_type = "" - should be set by child classes
        


        # try:
        #     self.credential = DefaultAzureCredential()
        #     # do az login
        #     # Check if given credential can get token successfully.
        #     self.credential.get_token("https://management.azure.com/.default")
        # except ClientAuthenticationError as ex:
        #     # Fall back to InteractiveBrowserCredential in case DefaultAzureCredential not work
        #     # This will open a browser page for
        #     self.credential = InteractiveBrowserCredential()

        # self.workspace_client: MLClient = MLClient.from_config(self.credential, file_name=config)
        
        




class AzureModel:
        ...
            
