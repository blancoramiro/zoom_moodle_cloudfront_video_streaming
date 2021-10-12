# Embed ZOOM recordings into moodle courses from S3 bucket 

![ZOOM MOODLE diagram](/zoommoodle_flow.png)


This job starts by checking for new recordings to process and upload. In case there is a new recording the script will first download it from zoom using the download_url plus the access_token which has to be generated before. Check zoom documentation for how to create JWT tokens.

Once the script has the mp4 file it executes ffmpeg to transcode it into HLS format and adds a watermark. 
This creates an M3U8 playlist and many chunks of about 10 seconds duration which compose the video. The playlist's size is very small, it's just a list with the list of all the video chunks and can be uploaded into a moodle repository to be use to embed the "video" into the courses. 
https://docs.moodle.org/311/en/File_system_repository

The video chunks (.ts files) are upoaded into an S3 bucket using s3 accelerator which is a must. Not using the accelerator is significantly slower.

Once the process is completed the recording is marked as complete in the database.

Access to the .ts files (the actual video) is granted through Cloudfront using a public-private key (https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/PrivateContent.html). There are two ways to grant access either by a signed URL or by signed cookies. During the signing process there is the possibility to grant only access to specific files. In this case we are using cookies during user login since it was faster to implement and we grant access to the directory which holds all the videos. To prevent users from accessing videos outside their curses we used a hashed directory path for every video which is stored in the database and the script modifies the M3U8 playlist. Example:


```# head  2021-09-16\ 18\:30\:00\ -\ 28143\(e619211a-bbe6-4dc1-bd8e-8eb1e2a70fbc\).m3u8 
#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:10
#EXT-X-MEDIA-SEQUENCE:0
#EXT-X-PLAYLIST-TYPE:EVENT
#EXTINF:10.000000,
https://s3bucket-xxxx.mydomain.com/dVtPqIYlp0bHIGCuM9bwgQM0Nt3CtR/stream0.ts
#EXTINF:10.000000,
https://s3bucket-xxxx.mydomain.com/dVtPqIYlp0bHIGCuM9bwgQM0Nt3CtR/stream1.ts
#EXTINF:10.000000,
...
```




# Example Database table structure
  
CREATE TABLE `zoom_recordings` (  
  `insertId` int(11) NOT NULL,  
  `start_time` varchar(100) DEFAULT NULL,  
  `course_id` varchar(50) NOT NULL,  
  `desc` varchar(250) NOT NULL,  
  `download_url` varchar(250) NOT NULL,  
  `out_ffmpeg` varchar(250) DEFAULT NULL,  
  `recordingId` varchar(140) NOT NULL,  
  `duration` varchar(100) NOT NULL,  
  PRIMARY KEY (`insertId`,`recordingId`)  
) ENGINE=InnoDB DEFAULT CHARSET=latin1  

# moodle/login/index.php simple patch

```//CLODFRONT PATCH

 /*Set-Cookie: 
 CloudFront-Policy=base64 encoded version of the policy statement; 
 Domain=optional domain name; 
 Path=/optional directory path; 
 Secure; 
 HttpOnly
 Set-Cookie: 
 CloudFront-Signature=hashed and signed version of the policy statement; 
 Domain=optional domain name; 
 Path=/optional directory path; 
 Secure; 
 HttpOnly
 Set-Cookie: 
 CloudFront-Key-Pair-Id=public key ID for the CloudFront public key whose corresponding private key you're using to generate the signature; 
 Domain=optional domain name; 
 Path=/optional directory path; 
 Secure; 
 HttpOnly 
 {
     "Statement": [
  {
      "Resource": "http://*",
      "Condition": {
   "IpAddress": {
       "AWS:SourceIp": "192.0.2.10/32"
   },
   "DateGreaterThan": {
       "AWS:EpochTime": 1357034400
   },
   "DateLessThan": {
       "AWS:EpochTime": 1357120800
   }
      }
  }
     ]
 } */

 $cfkeys_expires = time() + 86400;
 $cfkeys_policy = trim('{"Statement":[{"Resource":"https://s3bucket-xxxx.mydomain.com/*","Condition":{ "DateLessThan":{"AWS:EpochTime":'.$cfkeys_expires.'}}}]}');

 $cfkeys_signature = "";

 // load the private key
 $cfkeys_fp = fopen('/var/www/html/cloudfront_private_key.pem', "r");
 $cfkeys_priv_key = fread($cfkeys_fp, 8192);
 fclose($cfkeys_fp);
 $cfkeys_pkeyid = openssl_get_privatekey($cfkeys_priv_key);

 // compute signature
 openssl_sign($cfkeys_policy, $cfkeys_signature, $cfkeys_pkeyid);

 // free the key from memory
 openssl_free_key($cfkeys_pkeyid);

 setcookie('CloudFront-Policy', base64_encode($cfkeys_policy), $cfkeys_expires, "/", '.mydomain.com', true, false);
 setcookie('CloudFront-Signature', str_replace(array('+', '=', '/'), array('-', '_', '~'), base64_encode($cfkeys_signature)), $cfkeys_expires, "/", '.mydomain.com', true, false);
 setcookie('CloudFront-Key-Pair-Id', 'XXXXXXXXXXXXXX', $cfkeys_expires, "/", '.mydomain.com',  true, false);

 //CLOUDFRONT PATCH END```
 
 
![moodle1](/images/moodle1.png)
![moodle2](/images/moodle2.png)
![moodle3](/images/moodle3.png)
