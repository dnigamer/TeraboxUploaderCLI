# TeraboxUploaderCLI
Python CLI tool to make uploads to your Terabox cloud from any Linux or Windows environment without having to use the website.


## Configuration
### Getting the JS Token
To use this tool you need to have a Terabox account and a JS Token key. You can get the session JS Token by logging into your Terabox account and following the sequence of steps below:

1. Open your Terabox cloud.
2. Open the browser's developer tools (F12).<br/>
![Developer tools F12](<images/devf12.png>)
3. Go to the "Network" tab.<br/>
![Developer tools F12 Network tab](<images/devf12network.png>)
4. Select the "XHR" filter.<br/>
![Developer tools F12 XHR filter](<images/devf12fetch.png>)
5. Click any directory or file in the cloud.
6. Look for any request made to the Terabox cloud URL and click on it.<br/>
![Developer tools F12 request item](<images/devf12list.png>)
7. Select the "Payload" tab.<br/>
![Developer tools F12 Payload tab](<images/devf12payload.png>)
8. Look for the jsToken parameter in the list and copy its value.

If you can't find the jsToken parameter, try selecting any other directory or file in the cloud and look for the jsToken parameter in the request payload. Make sure that you have the "XHR" filter selected and that you are looking at the "Payload" tab.


### Getting the cookies values
Additionally to the JS Token, you will need to capture the cookies values. You can get them by following the sequence of steps below:

1. Open your Terabox cloud.
2. Open the browser's developer tools (F12).<br/>
![Developer tools F12](<images/devf12.png>)
3. Go to the "Application" tab.<br/>
![Developer tools F12 Application tab](<images/devf12apptab.png>)
4. Select the "Cookies" item in the left panel.<br/>
![Developer tools F12 Cookies tab](<images/devf12cookiestab.png>)
5. Look for the cookies values and copy them.<br/>
![Developer tools F12 Cookies values](<images/devf12cookieval.png>)

You will need to copy the csrfToken, browserid, lang, ndus, and ndut_fmt values. This step is required to make the tool be compatible with the Terabox API as much as possible. Even though there are some paramters that are not directly used by the Terabox API, they can still create problems if they are not present in the request headers.


### Building the secrets.json file
Create a file named `secrets.json` in the same directory as the `main.py` file. The file should have the following structure:

```json
{
  "jstoken": "your_js_token_here",
  "bdstoken": "your_bd_token_here",
  "cookies": {
    "csrfToken": "your_csrf_token_here",
    "browserid": "your_browser_id_here",
    "lang": "en",
    "ndus": "your_ndus_token_here",
    "ndut_fmt": "your_ndut_fmt_token_here"
  }
}

```

Replace the `your_js_token_here`, `your_bd_token_here`, `your_csrf_token_here`, `your_browser_id_here`, `your_ndus_token_here`, and `your_ndut_fmt_token_here` values with the ones you captured in the previous steps.


### Building the settings.json file
Create a file named `settings.json` in the same directory as the `main.py` file. The file should have the following structure:

```json
{
  "directories": {
    "sourcedir": "source_directory_here",
    "remotedir": "remote_terabox_directory_here",
    "uploadeddir": "uploaded_files_directory_here"
  },
  "files": {
    "movefiles": "false or true",
    "deletesource": "false or true"
  },
  "encryption": {
    "enabled": "true or false",
    "encryptionkey": "your_encryption_key_here"
  },
  "ignoredfiles": []
}
```


#### Settings.json directory options
- Replace the `source_directory_here` value with the path to the directory you want to upload to Terabox. 
- Replace the `remote_terabox_directory_here` value with the path to the directory in your Terabox cloud where you want to upload the files. 
- Replace the `uploaded_files_directory_here` value with the path to the directory where you want to move the files after they are uploaded to Terabox. 
- Replace the `your_encryption_key_here` value with the key you want to use to encrypt the files before uploading them.


#### Settings.json file options
- If you don't want to use encryption, set the `enabled` value to `false`. 
- If you want to move the files to the `uploadeddir` after they are uploaded to Terabox, set the `movefiles` value to `true`. 
- If you want to delete the source files after they are uploaded to Terabox, set the `deletesource` value to `true`. 
- You can also add a list of filenames and/or file globbing patterns to be ignored in the upload process by adding their names to the `ignoredfiles` list.


## Dependencies
The tool uses some external libraries to work properly. You can install them by running the following command in the terminal:

```sh
pip install -r requirements.txt
```


### Curl installation
#### For Linux and macOS users
In addition to the libraries listed in the `requirements.txt` file, you will also need to have curl installed in your system to make the uploads to Terabox. The tool will attempt to bootstrap the curl installation if it is not present in your system, according to the OS you are using. However, if the tool is not able to install curl, you will need to install it manually.


#### For Windows users
For Windows, the tool will also attempt to install curl, but by utilizing a pre-built version of curl for Windows located [here](https://curl.se/windows/dl-8.5.0_5/curl-8.5.0_5-win64-mingw.zip). You can also install curl manually by following the instructions in the [curl website](https://curl.se/windows/) for downloading the binaries and utilizing the following method to install curl to be used by the tool:

1. Download the curl zip file from the [curl website](https://curl.se/windows/).
2. Extract the zip file to a directory of your choice.
3. Add the directory where you extracted the curl files to the system's PATH environment variable.

Alternatively, you can also use the Windows Subsystem for Linux (WSL) to run the tool in a Linux environment.


## Usage
The most important thing to use the tool is to have, of course, python installed in your system. If you don't have it installed, you can download it from the [Python website](https://www.python.org/downloads/).<br>
To then run the tool, ensure that you have the `secrets.json` and `settings.json` files configured correctly and that you have installed the dependencies listed in the `requirements.txt` file. <br>Then, simply run the `main.py` file using the following command in the terminal:

```sh
python main.py
```

The tool will start the upload process and display the progress of the uploads in the console.
Any errors that occur during the upload process will be displayed in the console. You can later check the terminal output to see if there were any errors during the upload process.


## Troubleshooting
If you encounter any issues while using the tool, please open an issue in the [Issues](https://github.com/dnigamer/TeraboxUploaderCLI/issues) section of the repository. I will try to help you as soon as possible. <br>However, there are some common issues that you may encounter, which are listed below:
- The tool is not able to install curl in your system.
  - This can happen if you are using an unsupported OS or if the tool is not able to install curl due to some other reason.
- The tool is not able to find the `secrets.json` or `settings.json` files.
  - This can happen if the files are not present in the same directory as the `main.py` file. 
  - Check the guide above to make sure that you have created the files correctly.
- The tool is not able to upload the files to Terabox.
  - This can happen if the `secrets.json` file is not configured correctly or if the JS Token already expired.
  - Check the guide above to make sure that you have captured the JS Token and cookies values correctly.
- The tool is not able to move the files to the `uploadeddir` directory after they are uploaded to Terabox.
  - This can happen if the `settings.json` file is not configured correctly or if the `uploadeddir` directory does not exist.
- The tool is not able to encrypt the files before uploading them to Terabox.
  - This can happen if the encryption section in the `settings.json` file is not configured correctly or if the encryption key specified is not valid to be used with this encryption algorithm.
  - Other case is if the key doesn't exist in the directory specified or if the tool doesn't have the necessary permissions to read the key file.
- The tool is not able to delete the source files after they are uploaded to Terabox.
  - This can happen if the `settings.json` file is not configured correctly or if the source files are being used by another process outside the tool.


## Contributing
If you want to contribute to the project, please open a pull request in the [Pull requests](https://github.com/dnigamer/TeraboxUploaderCLI/pulls) section of the repository. I will review your changes and merge them if they are appropriate. 


## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.