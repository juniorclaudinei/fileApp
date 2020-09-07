## This application adds an extra layer of security when storing files in public clouds like Google Drive, MS OneDrive and so on.
## The application is still in the Alpha and has a lot to be improved, but at the moment it is functional.
## Each part of the code has its own explanation (kinda).
##
## PLEASE, considere take a look at the Git RoadMap section!!!
##
## Note: Some of the fuctions here could be coded together, but they are separated to make future implementations easier. =D
##
## Author: Claudinei Junior
## Date: 25/Aug/2020
## File: fileApp.py
##
## Enjoy!

import os, configparser, ast, hashlib, subprocess, time, mysql.connector, csv
from mysql.connector import errorcode

######### CONNECTION CONF ###########

## This part of the code deals with the database file configuration

mysqlConfigFile = ".../fileApp/connection.conf" ## Insert the full path
print(mysqlConfigFile)

configParser = configparser.ConfigParser()
configParser.read(mysqlConfigFile)
config = ast.literal_eval(configParser.get('MySQL', 'conf'))

##############################################################################################################################################
#############           ######################################################################################################################
############# FUNCTIONS ######################################################################################################################
#############           All the magic happens here (sorta)!!                ##################################################################
##############################################################################################################################################

### This function validates if there is a connection with the database
def tryCnx():
  flag = False

  try:
    mysql.connector.connect(**config)
  except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
      print("Something is wrong with your user name or password")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
      print("Database does not exist")
    else:
      print(err)
  else:
    flag = True

  return flag

### Check if file exists
def checkFile(userFile):
  if not os.path.isfile(userFile):
    status = False
  else:
    status = True

  return status

### Check if directory exists
def checkDir(userDir):
  if not os.path.isdir(userDir):
    status = False
  else:
    status = True

  return status

### Change the name of the file (this is just a way to avoid unsolicited attention)
def md5(uploadFile):
  md5File = hashlib.md5(uploadFile.encode())

  return (md5File.hexdigest()+".bin")

### Return all the remotes configured in the services table
def returnService():
  cnx = mysql.connector.connect(**config)
  cursor = cnx.cursor()
  serviceQuery = ("select * from files.services;")
  cursor.execute(serviceQuery)
    
  for (id, name, service) in cursor:
    print("{},{},{}".format(id, name, service))

  cursor.close()
  cnx.close()

  return True

### Return the service name (the name given to the remote during the Rclone configuration)
def serviceName(service):
  cnx = mysql.connector.connect(**config)
  cursor = cnx.cursor()
  selectQuery = ("select name from files.services where pk_id_service = %(id_service)s")
  cursor.execute(selectQuery, { 'id_service': service })
  
  count = 0
  for name in cursor:
    count = 1
    temp = str(name)
    serviceName = str(temp.split("'")[1::2]).replace("[","").replace("]","")

  if count == 0:
    serviceName = False
  
  cursor.close()
  cnx.close()

  return serviceName

### This fuction inserts the file into the file_log table and does the file upload using Rclone
def insertFile(oldName, newName, idService, serviceName, userFile):
  cnx = mysql.connector.connect(**config)
  cursor = cnx.cursor()
  addFileQuery = ("insert into files.file_log values (null, %s, %s, "
                  "(select pk_id_service from files.services where pk_id_service = %s), NOW());")

  cursor.execute(addFileQuery, (oldName, newName, idService))
  cursor.close()

  cursor = cnx.cursor()
  selectQuery = ("""
        select fg.pk_id_file_log as 'ID_FILE', fg.old_file as 'OLD_FILE', fg.new_file as 'NEW_FILE', s.service as 'SERVICE', fg.timestamp as 'TIMESTAMP' 
        from files.file_log fg, files.services s 
        where fg.fk_id_service = s.pk_id_service 
        and fg.new_file = %(new_file)s
        and fg.old_file = %(old_file)s
        and s.pk_id_service = %(service)s;""")
  cursor.execute(selectQuery, { 'new_file': newName, 'old_file':  oldName, 'service': idService})
  
  for (id_file, old_name, new_name, service, date) in cursor:
    print("Record inserted: ID: {}; Original Name: {}; New Name: {}; Service: {}, Insert Date: {}".format(id_file, old_name, new_name, service, date))

  cursor.close()

  ## Rclone
  cmd=["rclone copyto " + userFile + " " + serviceName + ":" + newName + " -P"]
  p = subprocess.Popen( cmd, stdin=subprocess.PIPE, shell=True )
  p.wait()

  if (p.returncode != 0):
    print("There was a problem trying to upload the file " + userFile + " to the remote server")
    exit (100)
    return False

  cnx.commit()
  cnx.close()

  return True

### This fuction downloads the file using Rclone
def downloadFile(downloadFile, destDir):
  cnx = mysql.connector.connect(**config)
  cursor = cnx.cursor()

  selectQuery = ("""
          select fg.pk_id_file_log as 'ID_FILE', fg.old_file as 'OLD_FILE', fg.new_file as 'NEW_FILE', s.name as 'SERVICE_NAME', s.service as 'SERVICE', fg.timestamp as 'TIMESTAMP' 
          from files.file_log fg, files.services s 
          where fg.fk_id_service = s.pk_id_service
          and fg.pk_id_file_log = %(find)s""")
  cursor.execute(selectQuery, { 'find': downloadFile })
    
  count = 0 
  for (id_file, old_name, new_name, service_name, service, date) in cursor:
    count = 1
    sName = service_name
    oldFile = old_name
    newFile = new_name

  cursor.close()
  cnx.close()

  ## Checks if the sql returns is null
  if count == 0:
    return False

  #Rclone
  cmd=["rclone copyto " + sName + ":" + newFile + " " + destDir + "/" + oldFile + " -P"]
  p = subprocess.Popen( cmd, stdin=subprocess.PIPE, shell=True )
  p.wait()

  if (p.returncode != 0):
    print("There was a problem trying to download the file " + new_name + " to the remote server")
    exit(200)
    return False
  
  return True

### This fuctions returns a list of files that were uploaded
### userFind = 1 - Search for the original file name
### userFind = 2 - Search for the new file name
### userFind = 3 - Search for the remote (not remote name)
### userFind = 4 - Search for the file ID
### userFind > 4 - Search and return all the files
def returnFiles(userFind):
  cnx = mysql.connector.connect(**config)
  cursor = cnx.cursor()
  header = ("ID","ORIGINAL NAME","NEW NAME","REMOTE NAME","REMOTE","UPLOAD DATE")

  if userFind == 1:
    userEntry = input("Enter the original file name: ")
    selectQuery = ("""
          select fg.pk_id_file_log as 'ID_FILE', fg.old_file as 'OLD_FILE', fg.new_file as 'NEW_FILE', s.name as 'SERVICE_NAME', s.service as 'SERVICE', fg.timestamp as 'TIMESTAMP' 
          from files.file_log fg, files.services s 
          where fg.fk_id_service = s.pk_id_service
          and fg.old_file = %(find)s""")
    cursor.execute(selectQuery, { 'find': userEntry })
    
    count = 0
    for (id_file, old_name, new_name, service_name, service, date) in cursor:
      count = 1
      print("{}; {}; {}; {},  {}, {}".format(id_file, old_name, new_name, service_name, service, date))

    if count == 0:
      return False

    cursor.close()
    cnx.close()

  elif userFind == 2:
    userEntry = input("Enter the new file name: ")
    selectQuery = ("""
          select fg.pk_id_file_log as 'ID_FILE', fg.old_file as 'OLD_FILE', fg.new_file as 'NEW_FILE', s.name as 'SERVICE_NAME', s.service as 'SERVICE', fg.timestamp as 'TIMESTAMP' 
          from files.file_log fg, files.services s 
          where fg.fk_id_service = s.pk_id_service
          and fg.new_file = %(find)s""")
    cursor.execute(selectQuery, { 'find': userEntry })

    count = 0
    for (id_file, old_name, new_name, service_name, service, date) in cursor:
      count = 1
      print("{}; {}; {}; {},  {}, {}".format(id_file, old_name, new_name, service_name, service, date))

    if count == 0:
      return False
  
    cursor.close()
    cnx.close()

  elif userFind == 3:
    userEntry = input("Enter the remote: ")
    selectQuery = ("""
          select fg.pk_id_file_log as 'ID_FILE', fg.old_file as 'OLD_FILE', fg.new_file as 'NEW_FILE', s.name as 'SERVICE_NAME', s.service as 'SERVICE', fg.timestamp as 'TIMESTAMP' 
          from files.file_log fg, files.services s 
          where fg.fk_id_service = s.pk_id_service
          and s.service = %(find)s""")
    cursor.execute(selectQuery, { 'find': userEntry })
    
    count = 0
    for (id_file, old_name, new_name, service_name, service, date) in cursor:
      count = 1
      print("{}; {}; {}; {},  {}, {}".format(id_file, old_name, new_name, service_name, service, date))

    if count == 0:
      return False

    cursor.close()
    cnx.close()

  elif userFind == 4:
    flag = True
    while flag:
      userEntry = input("Enter the file ID: ")

      if not userEntry.isdigit():
        print("Please provide an integer (number)")
      else:
        flag = False

    selectQuery = ("""
          select fg.pk_id_file_log as 'ID_FILE', fg.old_file as 'OLD_FILE', fg.new_file as 'NEW_FILE', s.name as 'SERVICE_NAME', s.service as 'SERVICE', fg.timestamp as 'TIMESTAMP' 
          from files.file_log fg, files.services s 
          where fg.fk_id_service = s.pk_id_service
          and fg.pk_id_file_log = %(find)s""")
    cursor.execute(selectQuery, { 'find': userEntry })
    
    count = 0
    for (id_file, old_name, new_name, service_name, service, date) in cursor:
        count = 1
        print("{}; {}; {}; {}, {}, {}".format(id_file, old_name, new_name, service_name, service, date))
    if count == 0:
      print("There are no results for this query!")
      return False
  
    cursor.close()
    cnx.close()

    return True

  else:
    selectQuery = ("""
          select fg.pk_id_file_log as 'ID_FILE', fg.old_file as 'OLD_FILE', fg.new_file as 'NEW_FILE', s.name as 'SERVICE_NAME', s.service as 'SERVICE', fg.timestamp as 'TIMESTAMP' 
          from files.file_log fg, files.services s 
          where fg.fk_id_service = s.pk_id_service""")
    cursor.execute(selectQuery)
    
    count = 0
    for (id_file, old_name, new_name, service_name, service, date) in cursor:
      count = 1
      print("{}; {}; {}; {}, {}, {}".format(id_file, old_name, new_name, service_name, service, date))

    cursor.close()
    cnx.close()

    if count == 0:
      print("There are no results for this query!")
      return False

  return True

### Insert a new remote into the services table
def insertRemote():

  remoteName = input("Enter the remote name: ")
  remoteService = input("Enter the remote service: ")

  cnx = mysql.connector.connect(**config)
  cursor = cnx.cursor()
  selectQuery = ("insert into files.services values (null, %s, %s)")
  cursor.execute(selectQuery, (remoteName, remoteService))
  
  cursor.close()
  cnx.commit()
  cnx.close()

  print("Remote added!\n")
  returnService()
  return True

### Insert a remote into the services table
def removeRemote():
  flag = True
  while flag:
    userConfirmation = input("\nAre you sure that you want to remove a remote? (y or n) ")
    userConfirmation = userConfirmation.upper()

    if userConfirmation != "Y" and userConfirmation != "N":
      print("The choices are ['y', 'n']. Please pick one of them.")
    elif userConfirmation == "N":
      flag = False
    else:
      control = True
      while control:
        returnService()
        removeService = input("Enter the remote ID you want to remove: ")

        if not removeService.isdigit():
          print("Please provide an integer (number)")
        else:
          if not serviceName(removeService):
            print("You must select a valid ID\n")
          else:
            cnx = mysql.connector.connect(**config)
            cursor = cnx.cursor()
            selectQuery = ("delete from files.services where pk_id_service = %(service_id)s")
            cursor.execute(selectQuery, {'service_id': removeService})
                
            cursor.close()
            cnx.commit()
            cnx.close()

            print("Remote removed!\n")
            returnService()
            control = False
            flag = False

  return True

### Remove the file from the file_log table and delete the file from the cloud service using Rclone
def removeFile(removeFileID):
  cnx = mysql.connector.connect(**config)
  cursor = cnx.cursor()
  selectQuery = ("""
          select fg.pk_id_file_log as 'ID_FILE', fg.old_file as 'OLD_FILE', fg.new_file as 'NEW_FILE', s.name as 'SERVICE_NAME', s.service as 'SERVICE', fg.timestamp as 'TIMESTAMP' 
          from files.file_log fg, files.services s 
          where fg.fk_id_service = s.pk_id_service
          and fg.pk_id_file_log = %(find)s""")
  cursor.execute(selectQuery, { 'find': removeFileID })
  
  count = 0
  for (id_file, old_name, new_name, service_name, service, date) in cursor:
    count = 1
    sName = service_name
    newFile = new_name
  
  cursor.close()
  
  if count == 0:
    cnx.close()
    return False
  
  flag = True
  while flag:
    userConfirmation = input("\nAre you sure that you want to remove this file? (y or n) ")
    userConfirmation = userConfirmation.upper()
    if userConfirmation != "Y" and userConfirmation != "N":
      print("The choices are ['y', 'n']. Please pick one of them.")
    elif userConfirmation == "Y":
      cursor = cnx.cursor()
      selectQuery = ("delete from files.file_log where pk_id_file_log = %(file_id)s")
      cursor.execute(selectQuery, {'file_id': removeFileID})
  
      #Rclone
      cmd=["rclone delete " + sName + ":" + newFile + " -P"]
      p = subprocess.Popen( cmd, stdin=subprocess.PIPE, shell=True )
      p.wait()
      
      if (p.returncode != 0):
        print("There was a problem trying to remove the file " + new_name + " to the remote server")
        exit(300)
        return False
      
      cnx.commit()
      cnx.close
      
      print("\nFile removed!\n")
      flag = False
      time.sleep(1)
      returnFiles(userFind=5)
    else:
      flag = False
  
  return True

##############################################################################################################################################
#############           ######################################################################################################################
############# MAIN CODE ######################################################################################################################
#############           Everything starts here!!                            ##################################################################
##############################################################################################################################################

## A nice clean start
os.system("clear")

## Checks if there is connection with the database
if not tryCnx():
  exit (10)

## Important note
print("""
      NOTE: This piece of software is in Alpha and you must use in your own risk.
            I am not responsable for anything wrong that may occur with you files and account.
            This is a personal project and there are lots of things that I still have to do.
            For now, I'd consider it as a home project that works but...if you are willing to use it.
            DO IT IN YOUR OWN RISK!!!!

            Also, you should read the RoadMap section =)
      """)

input("Press ENTER to continue....")

## Another important note
print("""
        There are some stuff that you should know:

        IT IS HIGLY RECOMMENDED THAT YOU USE THIS SOFTWARE WITH RCLONE CRYPT. WITHOUT RCLONE CRYPT THIS SOFTWARE ONLY CHANGES THE NAME OF THE FILE DURING THE
        UPLOAD. IF YOU THINK THAT ONLY CHANGE THE NAME WITHOUT ANY KINF OF CRYPT IF OK, THEN YOU CAN SKIP THIS CONFIGURATION (BUT YOU SHOULD NOT!!!)

        1 - You must avoid deal with files directly through the cloud service interface (it will mess things up here)
        2 - You must confirm that all the remotes configured in Rclone is configured in the database table. Use option 4
        3 - This software doesn't have backup routine or any kind of secure way to avoid you to delete the files table
            So, would be a good idea once a while to a manual backup. Use option 6
        4 - You can upload, download and remove files in your cloud store service, but this software does not deal with files
            in your File System. IF you want, you must remove your original file manually
      """)

input("Press ENTER to continue....")

### Here the program starts and this is just a big (big!!!) if statement inside a while loop
stay = True
while stay:
  print("""
        \t What you want to do:
        \t 1: Upload
        \t 2: Download
        \t 3: Find
        \t 4: Rclone Remotes
        \t 5: File Table Backup
        \t 6: Delete (only cloud)
        \t 7: Exit
        """)
  option=input("Enter the option: ")

  if not option.isdigit():
    print("You Must enter a number between 1 and 7")
  else:
    option = int(option)

    if (option < 1 or option > 7):
      print("You Must enter a number between 1 and 7")
    else:
      if option == 1:
        flag = True
        while flag:
          userFile = input("Enter the full path and file name you want to upload (Ex. /var/tmp/file.log): ")

          if not checkFile(userFile):
            print("File does not exist!")
          else:
            flag = False
          
        destDir = input("Enter the full path where the file will be downloaded (Ex. /backup/logfiles): ")
        returnService()

        flag = True
        while flag:
          idService = input("Enter the remote ID you want to upload to: ")

          if not idService.isdigit():
            print("Please provide an integer (number)")
          else:
            if not serviceName(idService):
              print("You must select a valid ID\n")
              returnService()
            else:
              serviceName = serviceName(idService)
              flag = False

        newName = md5(userFile)
        oldName = userFile[userFile.rfind("/")+1:]
        insertFile(oldName, destDir+"/"+newName, idService, serviceName, userFile)

      elif option == 2:
        userDir = input("Enter the full path where the file will be downloaded (Ex. /tmp/logfiles): ")
        if not checkDir(userDir):
          print("Directory does not exist and will be created automatically (if your user has permission to do so)")
  
        returnFiles(userFind=5)
        
        flag = True
        while flag:
          fileID = input("Enter the file ID: ")

          if not fileID.isdigit():
            print("Please provide an integer (number)")
          else:
            if not downloadFile(fileID, userDir):
              print("You must select a valid ID\n")
            else:
              flag = False

      elif option == 3:
        flag = True
        while flag:
          print("""
                \t What you want to find:
                \t 1: Original Name
                \t 2: New Name
                \t 3: Remote
                \t 4: ID
                \t 5: All
                \t 6: Return
                """)
          userFind = input("Enter the option: ")

          if not userFind.isdigit():
            print("Please provide an integer (number)")
          else:
            userFind = int(userFind)
            if (userFind < 0 or userFind > 6):
              print("You Must enter a number between 1 and 6")
            else:
              if (userFind == 6):
                flag = False
              else:
                if not returnFiles(userFind):
                  print("No files found!")

      elif option == 4:
        print("""
              For now, this function only show the rclone remotes and the remotes configured in the database
              If you find any difference between them, please adjust it manually
              """)
        time.sleep(2)

        print("Rclone Remotes:")
        cmd=["rclone listremotes --long"]
        p = subprocess.Popen( cmd, stdin=subprocess.PIPE, shell=True )
        p.wait()

        if (p.returncode != 0):
          print("There was a problem trying to retrieve the Rclone remotes server")
          exit (400)

        print("\nDatabase Remotes:")
        returnService()

        flag = True
        while flag:
          changeRemote = input("\nDo you want to change the remote configuration? (y or n): ")
          changeRemote=changeRemote.upper()

          if changeRemote != "Y" and changeRemote != "N":
            print("The choices are ['y', 'n']. Please pick one of them.")
          else:
            if changeRemote == "N":
              flag = False
            else:
              control = True
              while control:
                print("""
                      1: Insert a New Remote
                      2: Remove a Remote
                      3: Return
                      """)
                option = input("Enter the option: ")

                if not option.isdigit():
                  print("You Must enter a number between 1 and 3")
                else:
                  option = int(option)
                  if (option < 1 or option > 3):
                    print("You Must enter a number between 1 and 3")
                  elif option == 1:
                    print("Please, provide the information exactly is configured in Rclone")
                    insertRemote()
                  elif option == 2:
                    removeRemote()
                  else:
                    flag = False
                    control = False
          
      elif option == 5:
        ## File table backup
        print("""
            * This fuction will backup the Rclone config file and all the data in the tables file_log and services.
            * This fuction WILL NOT backup the database structure and stuff. For that please run mysqldump 
              with root user directly on the terminal.
              """)

        input("Press ENTER to continue....")

        bkpDir = input("Enter the full path where the bkp will be done (Ex. /backup/logfiles): ")
        bkpDir = (bkpDir +"/fileApp_backup_"+time.strftime('%d%m%Y_%H%M%S')+"/")
        
        print("Starting Rclone backup at " + bkpDir)

        cmd=["mkdir -p "+ bkpDir + " && cp $(rclone config file | tail -1) " + bkpDir]
        p = subprocess.Popen( cmd, stdin=subprocess.PIPE, shell=True )
        p.wait()

        if (p.returncode != 0):
          print("There was a problem trying to retrieve the Rclone remotes server")
          exit (400)

        print("Rclone backup done!")

        print("Starting MySQL backup at " + bkpDir)
        cnx = mysql.connector.connect(**config)

        ## file_log table backup
        cursor = cnx.cursor()
        selectQuery = ("select * from files.file_log;")
        cursor.execute(selectQuery)

        with open(bkpDir + 'file_log.csv', mode='w') as file_log:
          file_log = csv.writer(file_log, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
          for (id_file, old_name, new_name, service, date) in cursor:
            file_log.writerow([id_file, old_name, new_name, service, date])

        cursor.close()

        ## services table backup
        cursor = cnx.cursor()
        selectQuery = ("select * from files.services;")
        cursor.execute(selectQuery)

        with open(bkpDir + 'services.csv', mode='w') as services:
          services = csv.writer(services, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
          for (id_service, service_name, service) in cursor:
            services.writerow([id_service, service_name, service])

        cursor.close()
        cnx.close()
        print("MySQL backup done!")

        print("To check the backup files, go to " + bkpDir)
        time.sleep(2)

      elif option == 6:
        print("""
            * This fuction will delete only the file and not the directory structure (even if this is the only file in the directory).
              """)

        input("Press ENTER to continue....")

        flag = True
        while flag:
          if not returnFiles(userFind=5):
            print("There is not files to be removed")
            flag = False
          else:
            removeFileID = input("Enter the file ID: ")
            
            if not removeFileID.isdigit():
              print("Please provide an integer (number)")
            else:
              removeFileID = int(removeFileID)
              
              if not removeFile(removeFileID):
                print("You must select a validID\n")
              else:
                flag = False

      else:
        print("Thank you for give my software a shot!!! See ya.")
        time.sleep(1)
        exit(0)
        stay = False