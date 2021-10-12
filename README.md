# Embed ZOOM recordings into moodle courses from S3 bucket 

![ZOOM MOODLE diagram](/zoommoodle_flow.png)


This job starts by checking for new recordings to process and upload. In case there is a new recording the script will first download it from zoom using the download_url plus the access_token which has to be generated before. Check zoom documentation for how to create JWT tokens.

Once the script has the mp4 file it executes ffmpeg to transcode it into HLS format and adds a watermark. 
This creates an M3U8 playlist and many chunks of about 10 seconds duration which compose the video. The playlist's size is very small, it's just a list with the list of all the video chunks and can be uploaded into a moodle repository to be use to embed the "video" into the courses. 

The video chunks (.ts files) are upoaded into an S3 bucket using s3 accelerator which is a must. Not using the accelerator is significantly slower.


VideoJS has support for HLS

- m3u8 streaming
- Add watermark
- Easy import from moodle repository
- Cloudfront private key to restrict access


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
