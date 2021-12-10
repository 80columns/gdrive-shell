# gdrive-shell

This code enables you to perform the following functions in Google Drive:
1. Show the contents of a folder
Examples:
	ls (shows the contents of the current folder)
	ls relative/path
	ls /absolute/path

2. Change your current path to another folder
Examples:
	cd relative/path
	cd /absolute/path
	cd ..

3. Recursively transfer ownership of a specific folder or file to another Google user. Note that this will apply permissions on each individual file contained within a folder, not just the top-level folder object itself.
Examples:
	transfer user@domain.com (transfers the contents of the current folder)
	transfer relative/path > user@domain.com
	transfer /absolute/path > user@domain.com

4. Upload a file from your local system to a folder in your drive
Examples:
	upload /absolute/path/to/localfile (uploads the localfile into the current folder)
	upload /absolute/path/to/localfile > relative/path
	upload /absolute/path/to/localfile > /absolute/path

5. Find files and folders matching query strings within your current drive folder
Examples:
	find *partialmatch
	find exactmatch

Instructions:
To run this code, use Docker to build & run the image specified in Dockerfile:

docker build -t gdshell .
docker run -it gdshell /bin/bash

Once your Docker session is active, you can navigate to the gdshell folder in /root/gdshell and run the program:

cd gdshell
./main.py

You will need to supply your own values for client_id and client_secret within the credentials.json file. This file exists as a reference and does not actually contain any credentials.
