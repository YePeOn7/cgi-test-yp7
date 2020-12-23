import cgiTest
from requests.auth import HTTPBasicAuth
import csv
import random
import time

IP = "10.10.1.96"                       # IP adress of the IP Cam
# IP = "10.10.1.62"                       # IP adress of the IP Cam
auth = HTTPBasicAuth('admin', 'admin')  # Authentication user and password
cgi = cgiTest.cgi(IP, auth)             # cgi object init

CGI_TABLE_FILE_NAME = "T E S T.csv"
SAVE_PARAMETER_FILE_NAME = "SAVED_PARAMETER.csv"
RESTORED_PROCESS_FILE_NAME = "RESTORED_PROCESS.csv"
RESULT_FILE_NAME = "RESULT.csv"
PRESERVED_PARAMETER_FILE_NAME = "preserved_parameter.txt"

FIRST_CHAR_SHIF = 2

INDEX_PARAMETER = 0
INDEX_TYPE = 1
INDEX_INT_DEFAULT = 2
INDEX_STRING_DEFAULT = 3
INDEX_MIN_VALUE = 4
INDEX_MAX_VALUE = 5
INDEX_RW = 7

TYPE_INTEGER = 0
TYPE_BOOLEAN = 1
TYPE_STRING = 2

def check_cgi_respond_to_list():
    #List the parameters from cgi
    list_parameter_cgi = cgi.list_parameter("all")
    list_parameter_cgi = list_parameter_cgi.splitlines()
    cgi_param = []
    for i in range(len(list_parameter_cgi)):
        list_parameter_cgi[i] = list_parameter_cgi[i][:-1]      #remove ";"
        cgi_param.append(list_parameter_cgi[i].split("="))      # the format will [['profile_0.enabled', '1'], ['profile_0.encode.resolution.height', '1080'],...]
        # print(list_parameter_cgi[i])
    # print("cgi_param:{} \n".format(cgi_param))

    #To read a CSV file and add new column with new "xxx" text
    with open("default_val.csv","r") as csv_file:
        csv_read = csv.DictReader(csv_file, delimiter=",")
        with open("res.csv", "w",newline='') as new_file:
            fieldnames = ["cgi parameter name","default value","status"]
            csv_writter = csv.DictWriter(new_file, fieldnames=fieldnames, delimiter=',')
            csv_writter.writeheader()
            for line in csv_read:
                # print("finding {}.....".format(line["cgi parameter name"]))
                st_found = False 
                for s in cgi_param:
                    if (s[0] == line["cgi parameter name"]):
                        st_found = True
                        line["status"] = "Parameter available"
                        csv_writter.writerow(line)
                        continue
                if (st_found != True):
                    line["status"] = "Not Found"
                    csv_writter.writerow(line)
                    print ("{} is not founded!".format(line["cgi parameter name"]))

def match_cgi_device2list():
    cgi_param_device = cgi.get_device_parameter('all')                  #List the cgi parameter from the device
    # print("cgi_param:\n{} \n".format(cgi_param))
    csv_read = cgi.csv_file.read(CGI_TABLE_FILE_NAME, first_row=False)   #read csv file

    # Match the parameter on the cgi parameter of the device to the documentation
    with open("res2.csv", "w",newline='') as new_file:
        csv_writter = csv.writer(new_file, delimiter=',')
        csv_writter.writerow(["CGI PARAMETER NAME","NOTE"])
        for line in csv_read:
            # print(line[0][1:-1])
            # print("finding {}.....".format(line["cgi parameter name"]))
            if (line[0] ==''):
                if(line[2]==''):
                    continue
                else:
                    csv_writter.writerow(['','',line[2]])
            else:
                st_found = False 
                for s in cgi_param_device:
                    if (s[0] == line[0][1:-1]):
                        st_found = True
                        csv_writter.writerow([line[0],"Available"])
                        continue
                if (st_found != True):
                    csv_writter.writerow([line[0],"Not available"])
                    print ("{} is not found!".format(line[0]))

def save_current_value():
    cgi_param_device = cgi.get_device_parameter('all')
    with open("saved_parameter.csv","w", newline='') as f:
        csv_writter = csv.writer(f, delimiter=',')

        for i in cgi_param_device:
            csv_writter.writerow(i)
    print(cgi_param_device)

def restore_last_value(delay = 0, max_size = 1024):
    value_to_be_written={}
    csv_read = cgi.csv_file.read("saved_parameter.csv", first_row=True)

    print("======= The value will be written =======")
    for x in csv_read:
        print("{} = {}".format(x[0],x[1]))

    for i in csv_read:
        value_to_be_written[i[0]]=i[1]

    # preserve some parameter
    print("========= Preserved parameter value =========")
    open("preserved_parameter_restore.txt","w").close() #clear the file contents
    # need_to_be_preserved = ['wireless','ipv6','http','https','network']
    for i in need_to_be_preserved:
        preserved_list = cgi.list_parameter(i).splitlines()
        preserved_list_splitted = [x.split('=') for x in preserved_list]
        for x in preserved_list_splitted:
            if(x[0] in value_to_be_written):
                print(x[0])
                with open("preserved_parameter_restore.txt","a") as f:
                    f.writelines("{}\n".format(x[0]))
                value_to_be_written.pop(x[0])

    # for i in value_to_be_written.keys():
    #     print(i, value_to_be_written[i])

    cgi.update_parameter(value_to_be_written, delay=delay, max_size = max_size)

    cgi_param_device = cgi.get_device_parameter()

    with open(RESTORED_PROCESS_FILE_NAME, "w",newline='') as new_file:
        csv_writter = csv.writer(new_file, delimiter=',')
        csv_writter.writerow(["CGI PARAMETER NAME","NOTE","CURRENT VALUE","WRITTEN VALUE"])

        for i in value_to_be_written.keys():
            status = ""
            for j in cgi_param_device:
                if(i==j[0] and value_to_be_written[i] == j[1]):
                    status = "PASS"
                    # print("{} {} {} {}".format(i, status, j[1], value_to_be_written[i]))
                    csv_writter.writerow([i, status, j[1], value_to_be_written[i]])
                    continue
                elif(i==j[0] and value_to_be_written[i] != j[1]):
                    status = "FAILED"
                    # print("{} {} {} {}".format(i, status, j[1], value_to_be_written[i]))
                    csv_writter.writerow([i, status, j[1], value_to_be_written[i]])
                    continue
            if(status == ""):
                status = "NOT FOUND"
                # print("{} {}".format(i, status))
                csv_writter.writerow([i, status])

def verify_update_parameter(group='all', delay = 0, min=0, max=-1, max_size = 1024, write = True):
    cgi_param_device = cgi.get_device_parameter('all')  # take parameter from the device before be modified , out => [['ZZZZ', "'YYYY'"], ['arcstatus.action.mask.cloud', '0'], ..]
    csv_read = cgi.csv_file.read(CGI_TABLE_FILE_NAME)   # Read the csv file               

    if(group != 'all'):
        csv_read = [i for i in csv_read if (group in i[0])]
    
    if(max==-1 or max>len(csv_read)):
        if(max>len(csv_read)):
            print(f'=== max value of {len(csv_read)} is exceeded ===')
            time.sleep(1)
        max = len(csv_read)
    
    csv_read = csv_read[min:max]                        # limit number of parameter to test

    tempDataWrite={}                                    # Dict the data will write to cgi
    typeTempDataWrite={}                                # type data

    # -- modification process -- #
    for i in csv_read:
        if('OP_W' in i[INDEX_RW] or 'ADMIN_W' in i[INDEX_RW]):
            if (i[INDEX_TYPE]=='0'): #integer
                written_value = i[INDEX_INT_DEFAULT]
                written_value = cgi.generate_dif_integer(i[INDEX_MIN_VALUE], i[INDEX_MAX_VALUE])
                # print("Par:{} Def:{} Min:{} Max:{} write:{}".format(i[INDEX_PARAMETER], i[INDEX_INT_DEFAULT], i[INDEX_MIN_VALUE], i[INDEX_MAX_VALUE], written_value))
                tempDataWrite[i[INDEX_PARAMETER][1:-1]] =  str(written_value)
                typeTempDataWrite[i[INDEX_PARAMETER][1:-1]] = TYPE_INTEGER
            if (i[INDEX_TYPE]=='1'): #bolean
                written_value = i[INDEX_INT_DEFAULT]
                written_value = cgi.generate_dif_boolean(written_value)
                tempDataWrite[i[INDEX_PARAMETER][1:-1]] = str(written_value)
                typeTempDataWrite[i[INDEX_PARAMETER][1:-1]] = TYPE_BOOLEAN
            if (i[INDEX_TYPE]=='2'): # string
                written_value = i[INDEX_STRING_DEFAULT][1:-1]
                written_value = cgi.generate_dif_string(written_value, FIRST_CHAR_SHIF)
                tempDataWrite[i[INDEX_PARAMETER][1:-1]] = str(written_value)
                typeTempDataWrite[i[INDEX_PARAMETER][1:-1]] = TYPE_STRING

    # preserve some parameter
    open(PRESERVED_PARAMETER_FILE_NAME,"w").close() #clear the file contents
    print("======== The parameters will be preserved ===========")
    for i in need_to_be_preserved:
        preserved_list = cgi.list_parameter(i).splitlines()
        preserved_list_splitted = [x.split('=') for x in preserved_list]
        for x in preserved_list_splitted:
            if(x[0] in tempDataWrite):
                with open(PRESERVED_PARAMETER_FILE_NAME,"a") as f:
                    f.writelines("{}\n".format(x[0]))
                tempDataWrite.pop(x[0])
                print(x[0])

    print("=========== The parameter will be modified ==============")
    for i in tempDataWrite.keys():
        print("{} ==> {}".format(i,tempDataWrite[i]))

    # -- save current parameter value -- #
    print("========= saving current parameter value ========")
    with open(SAVE_PARAMETER_FILE_NAME, "w", newline='') as f:
        csv_writter = csv.writer(f, delimiter=',')
        
        for i in tempDataWrite.keys():
            found = False
            for j in cgi_param_device:
                if(i==j[0]):
                    csv_writter.writerow([j[0],j[1]])
                    print("{} ==> {}".format(j[0], j[1]))
                    found = True
                    # print("found {}".format(i))
            if (found == False):
                print("save current parameter fail because there is no such of the parameter in the device: {}".format(i))

    # cgi.update_parameter_1by1(tempDataWrite, delay = delay)
    if(write == True):
        cgi.update_parameter(tempDataWrite, delay = delay, max_size = max_size, start_count = min)

    cgi_param_device = cgi.get_device_parameter('all')

    with open("RESULT.csv", "w",newline='') as new_file:
        csv_writter = csv.writer(new_file, delimiter=',')
        csv_writter.writerow(["CGI PARAMETER NAME","NOTE","CURRENT VALUE","WRITTEN VALUE"])

        for i in tempDataWrite.keys():
            status = ""
            for j in cgi_param_device:
                if(i==j[0] and tempDataWrite[i] == j[1]):
                    status = "PASS"
                    # print("{} {} {} {}".format(i, status, j[1], tempDataWrite[i]))
                    if typeTempDataWrite[i] != TYPE_STRING:
                        csv_writter.writerow([i, status, j[1], tempDataWrite[i]])
                    else:
                        csv_writter.writerow([i, status, f'"{j[1]}"', f'"{tempDataWrite[i]}"'])
                    continue
                elif(i==j[0] and tempDataWrite[i] != j[1]):
                    status = "FAILED"
                    # print("{} {} {} {}".format(i, status, j[1], tempDataWrite[i]))
                    if typeTempDataWrite[i] != TYPE_STRING:
                        csv_writter.writerow([i, status, j[1], tempDataWrite[i]])
                    else:
                        csv_writter.writerow([i, status, f'"{j[1]}"', f'"{tempDataWrite[i]}"'])
                    continue
            if(status == ""):
                status = "NOT FOUND"
                # print("{} {}".format(i, status))
                csv_writter.writerow([i, status])

def interface():
    while(1):
        print("[1] Verify update parameter process")
        print("[2] Restore last parameter value")
        print("[3] List Parameter")
        print("[0] Exit")
        input_user = input("Enter the option:")

        if(input_user == '0'):
            print("Thank You.... Bye...!!")
            break
        elif(input_user == '1'):
            input_user = input("Use default value?\nParameter:'all' delay:5 max_url_size:1000 (Y/N/C)")
            if(input_user == 'Y' or input_user == 'y'):
                start_time = time.time()
                verify_update_parameter('all', delay=5, max_size=1000, write=True)

                print("UPDATING PARAMETER PROCESS VALUE HAS BEEN FINISHED...")
                print(f"Update process log is saved in file '{RESULT_FILE_NAME}'")

                print("ELAPSED TIME: {} seconds".format(time.time()-start_time))

            elif(input_user == 'N' or input_user == 'n'):
                parameter = input("Parameter: ")
                delay = input("Delay: ")
                max_size = input("Maximum url size(byte(s)): ")
                start_time = time.time()
                verify_update_parameter(parameter, delay=int(delay), max_size=int(max_size), write=True)

                print("UPDATING PARAMETER PROCESS VALUE HAS BEEN FINISHED...")
                print(f"Update process log is saved in file '{RESULT_FILE_NAME}'")

                print("ELAPSED TIME: {} seconds".format(time.time()-start_time))

            else:
                pass
            
        elif(input_user == '2'):
            input_user = input("Use default value?\nDelay:5 (Y/N/C)")
            if(input_user == 'Y' or input_user == 'y'):
                start_time = time.time()
                restore_last_value(delay = 5)

                print("RESTORING PARAMETER VALUE HAS BEEN FINISHED...")
                print(f"Restoring process log is saved in file '{RESTORED_PROCESS_FILE_NAME}'")

                print("ELAPSED TIME: {} seconds".format(time.time()-start_time))
            elif(input_user == 'N' or input_user == 'n'):
                delay = input("Delay: ")
                
                start_time = time.time()
                restore_last_value(delay = int(delay))

                print("RESTORING PARAMETER VALUE HAS BEEN FINISHED...")
                print(f"Restoring process log is saved in file '{RESTORED_PROCESS_FILE_NAME}'")

                print("ELAPSED TIME: {} seconds".format(time.time()-start_time))
            else:
                pass

        elif(input_user == '3'):
            input_user = input("List default parameter? Parameter: 'all' (Y/N/C)")
            if(input_user == "Y" or input_user == 'y'):
                start_time = time.time()
                print(cgi.list_parameter('all'))
            elif(input_user == "N" or input_user == 'n'):
                parameter = input("Parameter: ")
                start_time = time.time()
                print(cgi.list_parameter(parameter))

            print("ELAPSED TIME: {} seconds".format(time.time()-start_time))
        print('\n\n\n')

need_to_be_preserved = ['wireless',
                        'ipv6',
                        # 'http',
                        'http.port',
                        'https',
                        'network',
                        'user',
                        'pppoe', 
                        'motion_0.width', 
                        'motion_0.height',
                        'motion_1.width', 
                        'motion_1.height',
                        'motion_2.width', 
                        'motion_2.height',
                        'motion_3.width', 
                        'motion_3.height',
                        'motion_0.x',
                        'motion_0.y',
                        'motion_1.x',
                        'motion_1.y',
                        'motion_2.x',
                        'motion_2.y',
                        'motion_3.x',
                        'motion_3.y']

# --------- Cal the function -------------#
# check_cgi_respond_to_list()
# match_cgi_device2list()
# verify_update_parameter('all', delay=5, max_size=1000, write=True)
# save_current_value()
# restore_last_value(delay = 5)
interface()

# cgi.update_parameter({"motion.y":'40000'})
# cgi.update_parameter({"pppoe.enabled":'0'})
# print(cgi.list_parameter("pppoe"))


