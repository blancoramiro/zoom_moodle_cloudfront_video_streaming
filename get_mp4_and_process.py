#!/usr/bin/python3
import requests
import sys,os
import subprocess
import json
import time
import string
import random
import pymysql
import os
import boto3
import fcntl
from botocore.config import Config
from io import BytesIO


lock_filename = '/tmp/recordings.lock'
lock_file = open(lock_filename, 'w')

try:
    fcntl.lockf(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
except IOError:
    print('already running')
    sys.exit(1)


AWSURL = 'https://s3bucket-xxxx.mydomain.com/'
WATERPATH = '/opt/RECORDINGS/watermark.png'
PATHTMP = '/opt/RECORDINGS/tmp/'
PATHMNT = '/opt/RECORDINGS/mnt/'

def download_file(url, random_name):
    #local_filename = url.split('/')[-1]
    local_filename = PATHTMP+random_name+'.mp4'
    # NOTE the stream=True parameter below
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                #if chunk:
                f.write(chunk)
    return True

db = pymysql.Connect(host="localhost",user="recordings",passwd="xxxxxxxxxxxxxxxxxxxxxxxxxxx",database="zoom_recordings",autocommit=True,port=3306)

cursor = db.cursor()

cursor.execute("SELECT * FROM recordings WHERE out_ffmpeg IS NULL", ())
pending_recs = cursor.fetchall()

client = boto3.client('s3')
#Creating Session With Boto3.
session = boto3.Session(
aws_access_key_id='XXXXXXXXXXXXXXXXXXXX', #<< AWS KEY from user with access to s3 bucket
aws_secret_access_key='xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
)
#Creating S3 Resource From the Session.
config = Config(s3={"use_accelerate_endpoint": True})
s3 = session.resource('s3', config=config)


for pending in pending_recs:   

    letters = string.ascii_letters+string.digits
    random_name = ''.join(random.choice(letters) for i in range(30))

    WPATH = PATHMNT+random_name+'/'
    PATHREPO = '/opt/RECORDINGS/repo/'+pending[8]+' - '+pending[7]+'('+str(pending[4])+')'
    #print(WPATH)
    #continue

    print(pending) 
    url = pending[9]
    
    result = subprocess.run(['/opt/RECORDINGS/jwt.pl'], stdout=subprocess.PIPE) # << get ZOOM JWT token
    token = result.stdout
    token = token.decode("utf-8")
    
    if download_file(url+'?access_token='+token, random_name):
        if not os.path.isdir(WPATH):
            os.makedirs(WPATH)
        if not os.path.isdir(PATHREPO):
            os.makedirs(PATHREPO)
        #continue
        try:
            ffmpeg_result = subprocess.run(['/usr/bin/ffmpeg', '-i', PATHTMP+random_name+'.mp4', '-i', WATERPATH, '-filter_complex', '[1][0]scale2ref=w=oh*mdar:h=ih*0.3[logo][video];[video][logo]overlay=main_w-overlay_w-5:main_h-overlay_h-5', '-c:v', 'libx264', '-crf', '28', '-preset', 'ultrafast', '-speed', '8', '-c:a', 'aac', '-b:a', '128k', '-ac', '2', '-f', 'hls', '-hls_time', '4', '-hls_playlist_type', 'event', WPATH+'stream.m3u8'],check=True)
        except subprocess.CalledProcessError as e:
            os.remove(PATHTMP+random_name+'.mp4')
            print(pending[0], "Ret code: ", e.returncode)
            continue
        FULLNAME = PATHREPO+'/'+pending[1]+' - '+str(pending[0])+'('+pending[11]+').m3u8'
        try:
            for file in os.listdir(WPATH):
                #print(file)
                s3.meta.client.upload_file(WPATH+file, 's3bucket-xxxx', random_name+'/'+file)
        except:
            print('Error subiendo a s3: ', str(pending[0]))
            os.remove(FULLNAME)
            os.remove(PATHTMP+random_name+'.mp4')
            continue

        try:
            f_in = open(WPATH+'stream.m3u8', "r")
            f_out = open(FULLNAME, "w")
            lines = f_in.readlines()
            for line in lines:
                f_out.write(line.replace('stream', AWSURL+random_name+'/stream'))
            f_in.close()
            f_out.close()
        except:
            print('Error escribiendo m3u8 file: ', str(pending[0]))
            os.remove(FULLNAME)
            os.remove(PATHTMP+random_name+'.mp4')
            continue

        try:
            cursor.execute("UPDATE recordings SET out_ffmpeg = %s WHERE insertId = %s", (random_name, pending[0]))
        except pymysql.Error as e:
            print("Error "+str(e.args[0])+": "+str(e.args[1]))
            os.remove(FULLNAME)
            os.remove(PATHTMP+random_name+'.mp4')
            exit(1)
        os.remove(PATHTMP+random_name+'.mp4')
    #exit() # for testing

lock_file.close()
