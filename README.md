# fileApp

A secure layer to rclone and your cloud storage.

Why does this software exist?

Nowadays it is extremely common to back up files in public clouds like Google Drive and Microsoft OneDrive but it is enough to just have your email account hacked and all files will be lost or in hands that should not be.

This software adds an additional, manageable layer in the management of these files by changing the file name to an MD5 hash (yes, this is a very light layer of security - can we call it security?) and keeping track of the files that have been loaded.

When using this software you should (must) only use it to manage the uploaded files since the name will be changed and you may lose track.

## Status
Work in progress. Experimental.

## Read it first

This software was developed as a personal project where a concern of mine is being addressed. This project is in an Alpha state (if anything before Alpha, that's it) and there are several improvements and security issues that still need to be addressed.

If you decide to use this software, do so at your own risk.

This software does not manipulate any files on your file system, taking care only of managing the file in the public cloud.

IMPORTANT NOTE:

This software was developed and tested in the following environment:
* Operating System: macOS Catalina Version 10.15.6
* Python: 3.8.5  
* Rclone: v1.52.3
* MySQL: 8.0.21

This software will likely run on any Unix-like operating system, any version of Python 3.5 or greater, any version of MySQL 7 or greater, and any recent version of Rclone.

## Requirements
To run this software you will need the following software:
* Unix-like Operational System
* [Rclone](https://rclone.org/)
* [MySQL](https://dev.mysql.com/downloads/mysql/)
* [Python](https://www.python.org/downloads/)

## Setup

### Database
First, you will need to set up a MySQL database.

You may follow [this manual](https://dev.mysql.com/doc/refman/8.0/en/installing.html).

After installation, you need to log in using `root` or any other `adm` user and run the `DDL.sql` to create and configure all the tables needed.
* You should (must) change the `fileapp` password. Change this line:
`CREATE USER 'fileapp'@'localhost' IDENTIFIED BY '12345678';`

After that, change the fileApp password in `connection.confg`. You may also change the `host` if you are working with different servers.

### Rclone
You will need a Rclone installation and you may follow [this manual](https://rclone.org/install/).

After that you need to configure all the remotes that you want to use, here is a [manual](https://rclone.org/remote_setup/), but all you need is `rclone config`.


* IMPORTANTE NOTE:

Since this software only changes the file name for uploading, it is HIGHLY RECOMMENDED that you configure Rclone Crypt. Without this, any file accessed directly in the cloud that has its extension changed to the original will be accessed normally.

You need to configure all the remotes that you want before following this step.

Please, follow [this](https://rclone.org/crypt/) to configure Rclone Crypt and you must use this configuration:

* `name`:                       you can choose any name, but please, choose one that is different from others.
* `storage`:                    "crypt"
* `remote`:                     here you have to type the remote that you configured before. I'd recommend type 
                                the entire remote (Ex. "backupfile:"),but if you choose to create a directory and 
                                crypt only this directory, keep in mind that when you use this software,
                                all files will be uploaded under this main directory.
* `filename_encryption`:        "off" - DO NOT USE ANY OF THE OTHER OPTIONS. 
                                        It will messy with the file rename.
* `directory_name_encryption`: "false" - DO NOT USE DIRECTORY NAME ENCRYPTION. 
                                         This software uses an absolute path to manage the uploaded files.

From now on you can follow the link above.

REMINDER: 
* You have to include this encrypted remote into the services table (use option 4) and you should only use encrypted remotes to upload your files.
* All the rclone remote configuration has do be done directly using the rclone binary through the terminal since this software does not deal with
rclone configuration itself.

### fileApp.py
Now that you have MySQL and Rclone configured, you just need to change the variable `mysqlConfigFile`to point to `connection.conf` file. You need to use the full path of the connection file.

## RoadMap
This is the most important section of this readme. There is a lot of stuff that I have to improve in this code. Here there are some of the stuff that I already know that I am going to fix/improve/implement:

* GUI - I will implement a web interface to interact with this code. (maybe Django? or in the future, I will probably change the code to Java or maybe Node...)
* Security improvements - There are lots of security improvements that I need to do. For example how to deal with MySQL user and password connection.
* File Upload - I need to implement a way to avoid duplicated files.
* Replace file - I need to implement the replace function.
* Multi-file upload, download and remove - Implement a multi file option upload, download, and remove.
* Parameters - Implement parameters in this code to allow the user to run all the functions through the terminal without surf through the menus.
* Help section - Implement a help section
* Configuration script - Implement an install/configuration script to deal with all the requirements installation (MySQL, Rclone, etc...)
* Errors handle - I have to implement lots of errors handlers, but for now, errors are thrown on the screen on purpose.

* (I am not sure about this one) - Create a Docker Image with all the environment configured.
* (I am not sure about this one) - Make this piece of software as a service (maybe an API) and do some integration with other software.
