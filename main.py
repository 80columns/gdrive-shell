#!/usr/bin/python3.9

from gdrive import gdrive

def main():
    print("Welcome to the GDrive shell! Enter a command, or enter 'help' to show the list of commands")

    # initialize the google drive client
    drive = gdrive()
    current_path = "/"

    # loop while interactively waiting for user input
    try:
        while True:
            print(f"gdrive ({current_path}) >> ", end="")
            command = input()

            if command == "help":
                print("Commands:\n"
                    + "ls\n\t[show the contents of the current folder]\n"
                    + "ls path/to/folder\n\t[show the contents of a folder]\n\n"
                    + "cd path/to/folder\n\t[change the current folder]\n"
                    + "transfer user@domain.com\n\t[transfer ownership of the current folder to user@domain.com]\n"
                    + "transfer path/to/object > user@domain.com\n\t[transfer ownership of a file/folder to user@domain.com]\n\n"
                    + "upload /full/path/to/localfile\n\t[upload a local file into the current folder]\n"
                    + "upload /full/path/to/localfile > path/to/folder\n\t[upload a local file into the target folder]\n\n"
                    + "find *partialmatch\n\t[find all files/folders within the current folder that partially match the supplied string]\n"
                    + "find exactmatch\n\t[find all files/folders within the current folder that exactly match the supplied string]\n\n"
                    + "exit\n\t[exit the interactive shell]\n")
            elif command.startswith("ls"):
                # if ls is provided by itself, pass an empty argument
                # otherwise, skip the first 3 characters in the string to find the target path
                argument = "" if command == "ls" else command [3:]

                drive.list_contents(current_path, argument)
            elif command.startswith("cd "):
                current_path = drive.change_folder(current_path, command[3:])
            elif command.startswith("transfer "):
                drive.transfer_ownership(current_path, command[9:])
            elif command.startswith("upload "):
                drive.upload_file(current_path, command[7:])
            elif command.startswith("find "):
                drive.search(current_path, command[5:])
            elif command == "exit":
                print("Exiting...")
                break
            else:
                print("Error: could not understand your command")

    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    main()
