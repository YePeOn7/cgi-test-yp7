"""
This library is creted to help verify the testing process of cgi parameter

@author: Yohan Prakoso
"""

import requests
from requests.auth import HTTPBasicAuth
import csv
import random
import time
import urllib
import winsound
from threading import Thread

class buzzer:
    def __init__(self):
        self.count = 0
        self.periode = 0
        self.threadOn = 0
    
    def buzzer(self, freq, times, long_sound):
        for _ in range(times):
            winsound.Beep(freq, int(long_sound))

class csv_file:
    def __init__(self):
        self.parameter=[]
        self.value=[]
        self.default_value=[]
        self.foo = "this is csv_file class"

    def read(self,CGI_TABLE_FILE_NAME, first_row = False):
        """
        This function is used to read the csv data for the reference
        
        Parameter:
            CGI_TABLE_FILE_NAME : the name of csv file
            first row           : determine to remove the first row or not (default value is False)

        Example (assume that "CGI" object has been created by using this class):
        CGI.read_csv_file("xxx.csv", first_row = True)
            ==> the fuction will read and return all the data of "xxx.csv" file without removing the first row

        return:
            array or list with format as follow (depend of the content of csv file):
                [[row1A, row1B, ...],[row2A, row2B, ...], ...]

        """
        with open(CGI_TABLE_FILE_NAME,"r") as csv_file:
            csv_read = list(csv.reader(csv_file, delimiter=","))
            if(first_row == False):
                csv_read = csv_read[1:] #remove the first row
            return csv_read


class device:
    def __init__(self):
        self.parameter=[]
        self.value=[]
        self.foo = "this is device class"

class cgi:
    def __init__(self, IP, auth):
        self.device = device()
        self.csv_file = csv_file()

        self.IP = IP
        self.auth = auth

    def generate_dif_boolean(self, dt_now):
        if(dt_now == '0'):
            return '1'
        elif(dt_now == '1'):
            return '0'
        else:
            print("generate_dif_boolean: the value is not boolean. dt_now -> {}.\n The value will be sign with 1".format(dt_now))
            return '1' 

    def generate_dif_integer(self, min_val, max_val):
        return round(random.uniform(int(min_val,0), int(max_val,0)))

    def generate_dif_string(self, dt_now, first_char_shift):
        if(len(dt_now) > 0):
                out = [ord(character) for character in dt_now]
                out[0] += first_char_shift
                out = ''.join([chr(ascii_char) for ascii_char in out])
                return out
        else:
            return ""

    def list_parameter(self, group = 'all'):
        """
        This function is used to perform list action of cgi parameter

        Example (assume that "CGI" object has been created by using this class):
        CGI.list_parameter("all")
            ==> use for list all cgi parameters of the device
        CGI.list_parameter("device.name")
            ==> use for list cgi parameters of the device that contain "device.name" in the name of the parameter

        return:
            list of cgi parameter with format as follow:
                device.boottime='2020/12/02 12:41:30';
                device.firmware='01.00.01.7754';
                device.hardware='AZ1.1';
                device.location='Device Location';
                .
                .
                .
        """
        r = requests.get("http://{}/cgi-bin/param.cgi?action=list&group={}".format(self.IP, group), auth=self.auth)
        # print(r.text)
        return(r.text)

    def update_parameter(self, data, delay=0, max_size = 1024, start_count = 0):
        """
        This fuction is used to update the cgi parameter

        data:
            dictionary of data will be updated, arrange such as:
            {"param 1":"param 1 data", "param 2": "param 2 data",...}

            for example if you want to update the parameter p2p.enable = 1 and internet.status = 1, the data will be:
                {"p2p.enable":1, "internet.enable":1} 
        """
        url_base = "http://{}/cgi-bin/param.cgi?action=update".format(self.IP)
        # len_url_base = len(url_base)
        # ============== split to some packet ================= #
        number_of_packet = 0
        parameter_packet = {}
        str_data = ""
        total_bytes_sent = 0
        total_parameters_sent = 0
        order_parameter = start_count
        for i in data.keys():
            # ==== build the request packet ==== #
            if(len(url_base + str_data + "&{}={}".format(i, urllib.parse.quote(data[i])))<max_size):
                str_data += "&{}={}".format(i, urllib.parse.quote(data[i]))
                parameter_packet[i] = data[i]
            else:
                print("=====> PACKET {}".format(number_of_packet))
                for j in parameter_packet.keys():
                    print(j,parameter_packet[j])

                url = "{}{}".format(url_base, str_data)
                # url = "http://10.10.1.96/cgi-bin/param.cgi?action=update&datetime.timezone=' +2:00'"
                # url = "http://10.10.1.96/cgi-bin/param.cgi?action=update&datetime.type=1&datetime.timezone=2:00&datetime.year=2017&datetime.month=4&datetime.day=27&datetime.hour=13&datetime.minute=39&datetime.second=25&datetime.format=1&datetime.current.year=1995"

                print("url => {}".format(url))
                print("size url => {} bytes ===== num of data => {}".format(len(url), len(parameter_packet)))
                print(f"order of parameter => {order_parameter} - {order_parameter + len(parameter_packet)-1}")
                order_parameter += len(parameter_packet)
                r = requests.get(str(url), auth=self.auth)
                print(r.text)
                
                total_bytes_sent += len(url)
                total_parameters_sent += len(parameter_packet)
                
                time.sleep(delay)
                parameter_packet.clear()
                number_of_packet += 1

                str_data="&{}={}".format(i, urllib.parse.quote(data[i]))
                parameter_packet[i] = data[i]

        if(len(str_data)>0):
            print("=======> PACKET {} (LAST)".format(number_of_packet))
            for j in parameter_packet.keys():
                    print(j,parameter_packet[j])

            # ==== send the last request packet ==== #
            url = "{}{}".format(url_base, str_data)
            # url = "http://{}/cgi-bin/param.cgi?action=update{}".format(self.IP, str_data)
            # url = "http://10.10.1.96/cgi-bin/param.cgi?action=update&datetime.type=1&datetime.timezone=2:00&datetime.year=2030&datetime.month=10&datetime.day=26&datetime.hour=20&datetime.minute=55&datetime.second=1&datetime.format=1&datetime.current.year=2033"
            print("url => {}".format(url))
            print("size url => {} bytes ===== num of data => {}".format(len(url), len(parameter_packet)))     

            r = requests.get(url, auth=self.auth)
            print(r.text)
            total_bytes_sent += len(url)
            total_parameters_sent += len(parameter_packet)

            print("===== SENDING PROCESS HAS BEEN DONE =======")
            print("Total Bytes Sent => {} \t Total Parameters Sent => {}".format(total_bytes_sent, total_parameters_sent))

            parameter_packet.clear()


    def update_parameter_1by1(self, data, delay = 0.5):
        """
        This fuction is used to update the cgi parameter

        data:
            dictionary of data will be updated, arrange such as:
            {"param 1":"param 1 data", "param 2": "param 2 data",...}

            for example if you want to update the parameter p2p.enable = 1 and internet.status = 1, the data will be:
                {"p2p.enable":1, "internet.enable":1} 
        """ 
        # ==== send the request packet ==== #
        str_data = ""
        for i in data.keys():
            # str_data = "&{}={}".format(i,data[i])
            str_data = "&{}={}".format(i, urllib.parse.quote(data[i]))

            url = "http://{}/cgi-bin/param.cgi?action=update{}".format(self.IP, str_data)
            # url = "http://{}/cgi-bin/param.cgi?action=update&user.size=2".format(self.IP)
            # url = "http://"+self.IP+"/cgi-bin/param.cgi?action=update"+str_data
            # url = "http://10.10.1.96/cgi-bin/param.cgi?action=update&user.size=2"

            print("update2 url => " + url)
            # print("len url => {}".format(len(url)))  
            # time.sleep(1)
            # print("sending........")
            r = requests.get(str(url), auth=self.auth)
            print(r.text)

            time.sleep(delay)


    def get_device_parameter(self, group='all'):
        list_parameter_cgi = self.list_parameter(group)
        list_parameter_cgi = list_parameter_cgi.splitlines()
        # print(list_parameter_cgi[:3])
        cgi_param = []
        for i in range(len(list_parameter_cgi)):
            list_parameter_cgi[i] = list_parameter_cgi[i][:-1]      #remove ";"
            splitted = list_parameter_cgi[i].split("=")
            if (splitted[1][0]=="'"):
                splitted[1]=splitted[1][1:-1]
            cgi_param.append(splitted)      # the format will [['profile_0.enabled', '1'], ['profile_0.encode.resolution.height', '1080'],...]
            
            self.device.parameter = [i[0] for i in cgi_param]
            self.device.value = [i[1] for i in cgi_param]
        return cgi_param


