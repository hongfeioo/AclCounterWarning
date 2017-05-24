#!/usr/bin/python
from collections import defaultdict
import telnetlib
import os,sys,commands,multiprocessing
import smtplib  
import time
import re
from email.mime.multipart import MIMEMultipart  
from email.mime.text import MIMEText  
from email.mime.image import MIMEImage  

import sys
if not "/root/labroom" in sys.path:
    sys.path.append("/root/labroom")
import messageMode
#-------config------------------
devicefile_init = '/root/getAclCounter/getAclCounter.ini'
devicetmp = '/root/getAclCounter/getAclCounter.tmp'
#mailtmp = '/root/npm/mail.tmp'
pythonlog =  '/root/mylog.txt'
sms_string = 'http://h.lie.com/el='

linecount = 0
MAX_process = 1       #mutiprocessing
sms_off = 0
mail_off = 0
#threshold_warning = 8000



usr = 'admin'
pwd = 'h'
#-------read file into idct-----------
begintime =  time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
devtmp_exi =  os.path.exists(devicetmp)
devinit_exi =  os.path.exists(devicefile_init)

if (devtmp_exi == False)&(devinit_exi == False):
    os.system("echo "+begintime+"  getAclCounter  no init &  no tmp file !  >> "+pythonlog)  # log to mylog.txt 
    print "no init no temp!!!"
    sys.exit()

if (devtmp_exi == False):
    devicefile = devicefile_init
    os.system("echo "+begintime+"  getAclCounter  devicefile init !  >> "+pythonlog)  # log to mylog.txt 
else:
    devicefile = devicetmp
    os.system("echo "+begintime+"  getAclCounter  devicefile tmp !  >> "+pythonlog)  # log to mylog.txt 



device_idct = defaultdict(lambda:defaultdict(dict))
file = open(devicefile)
for line in file.readlines():
    if (line.split()[0].find('#') >= 0)|(len(line) < 7): #jump the comments,jump short than 1.1.1.1
        continue
    else:
        device_idct[linecount]['ip'] = line.split()[0]
        device_idct[linecount]['acl'] = line.split()[1]
        device_idct[linecount]['rule']= line.split()[2]  
        device_idct[linecount]['description']= line.split()[3]
        device_idct[linecount]['last_counter']= line.split()[4]
        device_idct[linecount]['muti_mail']= line.split()[5]
        device_idct[linecount]['muti_phone']= line.split()[6]
        device_idct[linecount]['fazhi']= line.split()[7]
        linecount += 1    #line counter
file.close()
#print "linecount:",linecount
#print device_idct
#sys.exit()




def getAclCounter(_ip,_acl,_rule):
    #get ACL counter

    #---telnet,username,password------
    try:
        tn = telnetlib.Telnet(_ip,23,10)
    except Exception,e:
        return "telnet error ip:"+_ip+'-'+str(e)
    #----try to login --------
    try:
        login_keyword = tn.read_until(": ",10)
    except Exception,e:
        return "error ip:"+_ip+'-'+str(e)
    if str(login_keyword).find(':') == -1:
        return "error ip:"+_ip+'-'+'not find the login keyword maohao !'

    tn.write(usr+"\n")
    tn.read_until(": ",3)
    tn.write(pwd+"\n")
    #------judge logined in ------
    try:
        logined_keyword = tn.read_until(">",3)
    except Exception,e:
        return "error ip:"+_ip+'-'+str(e)
    if str(logined_keyword).find('>') == -1:
        return "error ip:"+_ip+'-'+'not find the jianhao  keyword !'
              
    cmd_acl = "dis acl "+_acl+" | i rule "+_rule
    #print cmd_acl
    #--begin to write command
    tn.write(cmd_acl + '\n')
    message1 = tn.expect(['>'],3)


    tn.write("quit\n")
    tn.close


    newresult = re.findall(r'(\d+) times',message1[2])
    #print newresult
    return str(newresult[0])





def func(_index):
    new_idct = defaultdict(lambda:defaultdict(dict))
    new_idct = device_idct
    fuc_ip = new_idct[_index]['ip']
    fuc_acl = new_idct[_index]['acl']
    fuc_rule = new_idct[_index]['rule']
    fuc_description = new_idct[_index]['description']
    fuc_last = new_idct[_index]['last_counter']
    fuc_muti_mail = new_idct[_index]['muti_mail']
    fuc_muti_phone = new_idct[_index]['muti_phone']
    fuc_fazhi = new_idct[_index]['fazhi']



    print '---',_index,'/',linecount,'---',fuc_ip,fuc_acl,'---',fuc_description,fuc_rule,'---[',fuc_last,']---',fuc_muti_mail,fuc_muti_phone,fuc_fazhi,'---'

    #get new status
    newcounter = getAclCounter(fuc_ip,fuc_acl,fuc_rule)
    changenum  = int(newcounter) - int(fuc_last)
    os.system("echo "+begintime+" getAclCounter "+fuc_ip + '-' +fuc_acl+'-'+ fuc_rule+'-'+ newcounter+"  >> "+pythonlog)  # log to mylog.txt 

    #write to tmp file---
    iofile = open(devicetmp,'a')
    write_line = fuc_ip + '\t' +fuc_acl+'\t'+ fuc_rule+'\t'+fuc_description +'\t'+ newcounter+'\t'+fuc_muti_mail+'\t'+fuc_muti_phone+'\t'+fuc_fazhi+'\n'
    iofile.write(write_line)
    iofile.close()

    #charge status  to send mail
    if  changenum > int(fuc_fazhi):
        #print str(int(newcounter) - int(fuc_last))
        sendtime =  time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
        os.system("echo "+sendtime+" getAclCounter "+fuc_ip + '-' +fuc_acl+'-'+ fuc_rule+'-'+ str(changenum)+"- -!  >> "+pythonlog)  # log to mylog.txt 
        sms_str = "ACL Warning:"+fuc_description+" counter up to "+str(changenum) +" !"
        #sms_str = " IP:"+fuc_ip+" acl:"+fuc_description+" counter up to "+str(changenum) +" warning!"
        mail_str = " IP:"+fuc_ip+"</p> acl:"+fuc_description+"</p>counter up to "+str(changenum) +" warning!"

        messageMode.send_muti_sms(fuc_muti_phone,sms_off,'getAclCounter sms ',sms_str)
        messageMode.sendtxtmail('GetAclCounter',mail_off,mail_str,fuc_muti_mail,sendtime)





    return 'func ok'

def main(_linecount):
    pool = multiprocessing.Pool(processes=MAX_process)
    result = []
    for index in xrange(_linecount):
        result.append(pool.apply_async(func, (index, )))
        #time.sleep(1)
    pool.close()
    pool.join()

    for res in result:
        if (res.successful() != True):
            print "Mutiprocess fail !"
            print 'Mutiprocess ret:',res.get(),res.successful()

if __name__ == "__main__":
    os.system("echo "+begintime+"  GetAclCounter   begin !  >> "+pythonlog)  # log to mylog.txt 
    os.system("rm -f "+devicetmp)    #delete tmp  file

    main(linecount)


    endtime =  time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    os.system("echo "+endtime+"  GetAclCounter over !  >> "+pythonlog)  # log to mylog.txt 
