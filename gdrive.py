import magic
import os.path
import time

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload
from humanize import naturalsize
from tabulate import tabulate

class gdrive:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/drive.metadata']
        self.service = self.__get_service()
        self.current_folder_id = "root" # store the google drive id of the current folder for navigation

    def __get_service(self):
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', self.SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        return build('drive', 'v3', credentials=creds)

    def __get_folder_children_ids(self, folder_id):
        parent_ids = [folder_id]
        found_ids = []
        page_token = None

        while len(parent_ids) > 0:
            while True:
                contents = self.service.files().list(pageSize=100, q=f"'{parent_ids[0]}' in parents", fields="nextPageToken, files(id, mimeType)", pageToken=page_token).execute()
                results = contents.get('files', [])

                for item in results:
                    found_ids.append(item["id"])

                    if item["mimeType"] == "application/vnd.google-apps.folder":
                        parent_ids.append(item["id"])

                page_token = contents.get('nextPageToken')

                if not page_token:
                    break

            parent_ids.pop(0)

        return found_ids

    def __print_folder_contents(self, folder_id):
        page_token = None
        results_table = []

        while True:
            contents = self.service.files().list(pageSize=100, q=f"'{folder_id}' in parents", fields="nextPageToken, files(name, size, mimeType, modifiedTime)", pageToken=page_token).execute()
            results = contents.get('files', [])

            for item in results:
                if item["mimeType"] == "application/vnd.google-apps.folder":
                    results_table.append([item["modifiedTime"], "-", "folder", item["name"]])
                else:
                    results_table.append([item["modifiedTime"], naturalsize(item["size"]), item["mimeType"], item["name"]])

            page_token = contents.get('nextPageToken')

            if not page_token:
                break

        print(tabulate(results_table, headers=["Last Modified", "Size", "Type", "Name"]))

    def __traverse_path(self, current_path, argument):
        # check if this is an absolute or relative path
        target_path_id = "root" if argument.startswith("/") else self.current_folder_id
        target_path_name = "/" if argument.startswith("/") else current_path

        try:
            # remove any start/end empty strings from the extracted paths list
            path_parts = [path for path in argument.split("/") if path]

            for object in path_parts:
                if object == ".":
                    continue
                elif object == "..":
                    # get the id of the parent folder
                    contents = self.service.files().get(fileId=target_path_id, fields="parents").execute()
                    target_path_id = contents["parents"][0]
                    target_path_name = "/" if target_path_name.rindex("/") == 0 else target_path_name[:target_path_name.rindex("/")]
                else:
                    # get the id of the next sub-folder
                    contents = self.service.files().list(pageSize=1, q=f"'{target_path_id}' in parents and name='{object}'", fields="files(id,name)").execute()
                    item = contents.get('files', [])[0]
                    target_path_id = item["id"]
                    target_path_name += f"{item['name']}" if target_path_name == "/" else f"/{item['name']}"
        except (KeyError, IndexError):
            print(f"Error: could not resolve the provided path '{argument}'")

            return ("", "")

        return (target_path_id, target_path_name)

    def __batch_api_callback(self, request_id, response, exception):
        if exception:
            print(exception)
        else:
            print(f"added permission id {response.get('id')}")

    def list_contents(self, current_path, argument):
        # display the contents of the current directory
        if argument == "" or argument == ".":
            self.__print_folder_contents(self.current_folder_id)

        # evaluate the path provided in the argument parameter, and display its contents
        else:
            target_path_id = self.__traverse_path(current_path, argument)[0]

            if target_path_id:
                self.__print_folder_contents(target_path_id)
            else:
                return

    def change_folder(self, current_path, argument):
        target_path_id, target_path_name = self.__traverse_path(current_path, argument)

        if target_path_id and target_path_name:
            self.current_folder_id = target_path_id

            return target_path_name
        else:
            return current_path

    def transfer_ownership(self, current_path, argument):
        destination_account = ""
        target_object_ids = []

        if ">" in argument:
            arg_parts = argument.split(" > ")
            destination_account = arg_parts[1]
            target_object_ids.append(self.__traverse_path(current_path, arg_parts[0])[0])

            contents = self.service.files().get(fileId=target_object_ids[0], fields="id,mimeType").execute()
        
            if contents["mimeType"] == "application/vnd.google-apps.folder":
                target_object_ids.extend(self.__get_folder_children_ids(target_object_ids[0]))
        else:
            destination_account = argument
            target_object_ids.append(self.current_folder_id)
            target_object_ids.extend(self.__get_folder_children_ids(target_object_ids[0]))

        batch_request = self.service.new_batch_http_request(callback=self.__batch_api_callback)

        user_permission = {
            "type": "user",
            "role": "writer",
            "pendingOwner": True,
            "emailAddress": destination_account
        }

        for object_id in target_object_ids:
            batch_request.add(
                self.service.permissions().create(fileId=object_id, body=user_permission)
            )

        batch_request.execute()

        # sleep for 3 seconds between permissions requests
        time.sleep(3)

        user_permission = {
            "role": "owner",
            "type": "user",
            "emailAddress": destination_account
        }

        for object_id in target_object_ids:
            self.service.permissions().create(fileId=object_id, body=user_permission, transferOwnership=True).execute()

            # sleep for 1 second between each of the owner permissions requests
            time.sleep(1)

    def upload_file(self, current_path, argument):
        local_file = ""
        folder_id = ""

        # parse the local file path & target drive upload path
        if ">" in argument:
            path_parts = argument.split(" > ")
            local_file = path_parts[0]
            folder_id = self.__traverse_path(current_path, path_parts[1])[0]
        # get the local file path to be uploaded to the current shell folder
        else:
            local_file = argument
            folder_id = self.current_folder_id

        metadata = { "name": os.path.basename(local_file), "parents": [folder_id] }
        media = MediaFileUpload(local_file, mimetype=magic.from_file(local_file, mime=True))

        self.service.files().create(body=metadata, media_body=media).execute()

    def search(self, current_path, argument):
        page_token = None
        results_table = []
        id_parentid_map = {}
        id_pathname_map = {}

        # check if this is a partial or full match
        if argument.startswith("*"):
            operator = "contains"
            argument = argument[1:]
        else:
            operator = "="

        while True:
            contents = self.service.files().list(pageSize=100, q=f"name {operator} '{argument}'", fields="nextPageToken, files(id, name, size, mimeType, modifiedTime, parents)", pageToken=page_token).execute()
            results = contents.get('files', [])

            for item in results:
                # find the drive path of each file in the search results
                # when folders are found, their ids & names are stored in a local dictionary in order to reduce the total number of API calls
                item["path"] = ""
                item_id = item["id"]

                parent_id = item["parents"][0] if "parents" in item else ""
                item_name = None

                while True:
                    if item_id not in id_parentid_map:
                        id_parentid_map[item_id] = parent_id

                        if item_name is not None:
                            id_pathname_map[item_id] = item_name

                            if item_name != "My Drive":
                                item["path"] = f"/{item_name}" + item["path"]
                            else:
                                break

                        item_id = parent_id
                    else:
                        # when the if statement above is not executed for this object, skip up 1 level
                        # this can occur if the current matching item is a folder that was
                        # part of the parent path of another item that previously matched
                        if item_name is None:
                            parent_name = id_pathname_map[parent_id]
                            parent_id = id_parentid_map[parent_id]
                        else:
                            parent_name = id_pathname_map[item_id]

                        while parent_name != "My Drive":
                            item["path"] = f"/{parent_name}" + item["path"]

                            parent_name = id_pathname_map[parent_id]
                            parent_id = id_parentid_map[parent_id]

                        break

                    contents = self.service.files().get(fileId=item_id, fields="parents,name").execute()

                    parent_id = contents["parents"][0] if "parents" in contents else ""
                    item_name = contents["name"]

                # filter the results based on the current path of the shell
                if item["path"].startswith(current_path):
                    if item["mimeType"] == "application/vnd.google-apps.folder":
                        results_table.append([item["modifiedTime"], "-", "folder", item["path"], item["name"]])
                    else:
                        results_table.append([item["modifiedTime"], naturalsize(item["size"]), item["mimeType"], item["path"], item["name"]])

            page_token = contents.get('nextPageToken')

            if not page_token:
                break

        print(f"found {len(results_table)} items")
        print(tabulate(results_table, headers=["Last Modified", "Size", "Type", "Path", "Name"]))
